import streamlit as st
from datetime import date
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Autenticación Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gspread"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Google Sheets
SPREADSHEET_KEY = "1T9lH0MNDQOJACChmK40DslErSkwJBSNSB-RvAFtb2TY"
spreadsheet = client.open_by_key(SPREADSHEET_KEY)
hoja_jugadores = spreadsheet.worksheet("Jugadores")
hoja_eval = spreadsheet.worksheet("EvaluacionesFisicas")

# Datos de jugadores
df_jugadores = pd.DataFrame(hoja_jugadores.get_all_records())
df_jugadores.columns = df_jugadores.columns.str.strip().str.lower().str.replace(" ", "_")

# Datos evaluación
df_eval = pd.DataFrame(hoja_eval.get_all_records())
df_eval.columns = df_eval.columns.astype(str).str.strip().str.lower().str.replace(" ", "_") if not df_eval.empty else []

# Diccionario de test
bloques_test = {
    "Test de Composición Corporal": {
        "talla": "Talla (cm)",
        "pt_musculo": "% Músculo",
        "pt_grasa": "% Grasa",
        "suma_pliegues": "Suma pliegues"
    },
    "Test Físicos": {
        "salto_horizontal": "Salto horizontal (cm)",
        "cmj": "CMJ (cm)",
        "sprint_10_mts_seg": "Sprint 10m (seg)",
        "sprint_20_mts_seg": "Sprint 20m (seg)",
        "sprint_30_mts_seg": "Sprint 30m (seg)",
        "agilidad_505": "Agilidad 505 (seg)",
        "vel_lanzada": "Velocidad lanzada (km/h)",
        "vo2_max": "VO2 Máx"
    }
}

st.title("Ingreso de Evaluaciones Físicas")

# Bloque y test
bloque = st.selectbox("Selecciona el bloque de test", list(bloques_test.keys()))
test_seleccionado = st.selectbox("Selecciona el test a realizar", list(bloques_test[bloque].keys()))

# Categoría filtro
st.subheader("Buscar jugadores por categoría (opcional)")
categorias = sorted(df_jugadores['categoria_origen'].unique())
categoria_filtro = st.selectbox("Filtrar jugadores para facilitar la búsqueda", ["Todas"] + categorias)

# Jugadores filtrados
if categoria_filtro == "Todas":
    df_filtrado = df_jugadores.copy()
else:
    df_filtrado = df_jugadores[df_jugadores['categoria_origen'] == categoria_filtro]

jugadores_dict = {f"{row['jugador_nombre']} (ID: {row['jugador_id']})": row['jugador_id'] for _, row in df_filtrado.iterrows()}
jugadores_seleccionados = st.multiselect("Selecciona los jugadores para este test", list(jugadores_dict.keys()), key="multiselect_jugadores")

if "preseleccion" not in st.session_state:
    st.session_state.preseleccion = []

# Agregar jugadores
if st.button("Agregar a la selección"):
    nuevos_ids = [jugadores_dict[j] for j in jugadores_seleccionados if jugadores_dict[j] not in st.session_state.preseleccion]
    st.session_state.preseleccion.extend(nuevos_ids)

# Mostrar selección actual
st.markdown("**Jugadores seleccionados:**")
for jugador_id in st.session_state.preseleccion:
    nombre = df_jugadores[df_jugadores['jugador_id'] == jugador_id]['jugador_nombre'].values[0]
    if st.button(f"❌ Quitar {nombre} (ID: {jugador_id})", key=f"quitar_{jugador_id}"):
        st.session_state.preseleccion.remove(jugador_id)

# Confirmar
if st.checkbox("✅ Confirmar selección de jugadores"):
    for jugador_id in st.session_state.preseleccion:
        nombre = df_jugadores[df_jugadores['jugador_id'] == jugador_id]['jugador_nombre'].values[0]
        st.markdown(f"### {nombre} (ID: {jugador_id})")

        valor = st.number_input(bloques_test[bloque][test_seleccionado], min_value=0.0, key=f"input_{jugador_id}")

        if st.button(f"💾 Guardar {bloques_test[bloque][test_seleccionado]}", key=f"guardar_{jugador_id}"):
            fecha_hoy = date.today().strftime("%Y-%m-%d")

            fila_existente = df_eval[(df_eval['jugador_id'] == jugador_id) & (df_eval['fecha_evaluacion'] == fecha_hoy)]
            if fila_existente.empty:
                fila_vacia = {
                    'jugador_id': jugador_id,
                    'fecha_evaluacion': fecha_hoy,
                    'talla': "",
                    'suma_pliegues': "",
                    'salto_horizontal': "",
                    'cmj': "",
                    'sprint_10_mts_seg': "",
                    'sprint_20_mts_seg': "",
                    'sprint_30_mts_seg': "",
                    'agilidad_505': "",
                    'vel_lanzada': "",
                    'vo2_max': "",
                    'pt_musculo': "",
                    'pt_grasa': "",
                    'comentario': ""
                }
                fila_vacia[test_seleccionado] = valor
                hoja_eval.append_row(list(fila_vacia.values()))
                st.success("✅ Registro creado exitosamente")
            else:
                row_idx = df_eval.index[(df_eval['jugador_id'] == jugador_id) & (df_eval['fecha_evaluacion'] == fecha_hoy)][0] + 2
                col_idx = df_eval.columns.get_loc(test_seleccionado) + 1
                hoja_eval.update_cell(row_idx, col_idx, valor)
                st.success("✅ Valor actualizado exitosamente")
