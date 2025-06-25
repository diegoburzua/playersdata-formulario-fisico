import streamlit as st
from datetime import date
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Autenticación
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gspread"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Google Sheets
SPREADSHEET_KEY = "1T9lH0MNDQOJACChmK40DslErSkwJBSNSB-RvAFtb2TY"
spreadsheet = client.open_by_key(SPREADSHEET_KEY)
hoja_jugadores = spreadsheet.worksheet("Jugadores")
hoja_eval = spreadsheet.worksheet("EvaluacionesFisicas")

# DataFrames
df_jugadores = pd.DataFrame(hoja_jugadores.get_all_records())
df_jugadores.columns = df_jugadores.columns.str.strip().str.lower().str.replace(" ", "_")

df_eval = pd.DataFrame(hoja_eval.get_all_records())
if df_eval.empty:
    df_eval = pd.DataFrame(columns=[
        'jugador_id', 'fecha_evaluacion', 'talla', 'suma_pliegues', 'salto_horizontal', 'cmj',
        'sprint_10_mts_seg', 'sprint_20_mts_seg', 'sprint_30_mts_seg',
        'agilidad_505', 'vel_lanzada', 'vo2_max', 'pt_musculo', 'pt_grasa', 'comentario'
    ])
else:
    df_eval.columns = df_eval.columns.str.strip().str.lower().str.replace(" ", "_")

# Configuración
st.title("Ingreso de Evaluaciones Físicas")

# Bloques de test
tests_por_bloque = {
    "Test de Composición Corporal": {
        "Talla (cm)": "talla",
        "% Músculo": "pt_musculo",
        "% Grasa": "pt_grasa",
        "Suma pliegues": "suma_pliegues"
    },
    "Test Físicos": {
        "Salto Horizontal (cm)": "salto_horizontal",
        "CMJ (cm)": "cmj",
        "Sprint 10 mts (seg)": "sprint_10_mts_seg",
        "Sprint 20 mts (seg)": "sprint_20_mts_seg",
        "Sprint 30 mts (seg)": "sprint_30_mts_seg",
        "Agilidad 5-0-5 (seg)": "agilidad_505",
        "Vel. Lanzada (km/h)": "vel_lanzada",
        "VO2 Max": "vo2_max"
    }
}

# Selección del bloque y test
bloque_sel = st.selectbox("Selecciona el bloque de test", list(tests_por_bloque.keys()))
test_opciones = tests_por_bloque[bloque_sel]
test_etiqueta = st.selectbox("Selecciona el test a realizar", list(test_opciones.keys()))
test_columna = test_opciones[test_etiqueta]

# Filtrado de jugadores por categoría
st.subheader("Buscar jugadores por categoría (opcional)")
categorias = sorted(df_jugadores['categoria_origen'].unique())
categoria_filtrada = st.selectbox("Filtrar jugadores para facilitar la búsqueda", ["Todas"] + categorias)

if categoria_filtrada != "Todas":
    df_visible = df_jugadores[df_jugadores['categoria_origen'] == categoria_filtrada]
else:
    df_visible = df_jugadores.copy()

# Inicialización de sesión para guardar selecciones
if "jugadores_seleccionados" not in st.session_state:
    st.session_state.jugadores_seleccionados = set()

# Multiselección y acumulación
jugadores_dict = {f"{row['jugador_nombre']} (ID: {row['jugador_id']})": row['jugador_id'] for _, row in df_visible.iterrows()}
jugadores_elegidos = st.multiselect("Selecciona los jugadores para este test", list(jugadores_dict.keys()))

if st.button("Agregar a la selección"):
    for jugador in jugadores_elegidos:
        st.session_state.jugadores_seleccionados.add(jugador)
    st.success("Jugadores agregados correctamente.")

# Confirmación final
if st.button("✅ Confirmar selección de jugadores"):
    st.session_state.confirmado = True

# Mostrar formularios de ingreso de datos
if st.session_state.get("confirmado"):
    st.subheader(test_etiqueta)

    id_lookup = {f"{row['jugador_nombre']} (ID: {row['jugador_id']})": row['jugador_id'] for _, row in df_jugadores.iterrows()}
    reverse_lookup = {v: k for k, v in id_lookup.items()}

    for jugador_key in sorted(st.session_state.jugadores_seleccionados):
        jugador_id = id_lookup.get(jugador_key)
        nombre = reverse_lookup.get(jugador_id)

        st.markdown(f"**{nombre}**")
        valor = st.number_input(f"{test_etiqueta}", key=jugador_id, min_value=0.0, value=0.0)

        if st.button(f"Guardar {test_etiqueta}", key=f"guardar_{jugador_id}"):
            # Buscar o crear fila
            fecha = date.today().strftime("%Y-%m-%d")
            fila_idx = None
            for i, fila in enumerate(df_eval.to_dict(orient='records')):
                if fila['jugador_id'] == jugador_id and fila['fecha_evaluacion'] == fecha:
                    fila_idx = i + 2
                    break
            if fila_idx is None:
                nueva = {
                    'jugador_id': jugador_id,
                    'fecha_evaluacion': fecha,
                    'talla': "-", 'suma_pliegues': "-", 'salto_horizontal': "-", 'cmj': "-",
                    'sprint_10_mts_seg': "-", 'sprint_20_mts_seg': "-", 'sprint_30_mts_seg': "-",
                    'agilidad_505': "-", 'vel_lanzada': "-", 'vo2_max': "-",
                    'pt_musculo': "-", 'pt_grasa': "-", 'comentario': ""
                }
                hoja_eval.append_row(list(nueva.values()))
                fila_idx = len(hoja_eval.get_all_values())
            col_idx = df_eval.columns.get_loc(test_columna) + 1
            hoja_eval.update_cell(fila_idx, col_idx, valor)
            st.success(f"{test_etiqueta} guardado para {nombre}.")
