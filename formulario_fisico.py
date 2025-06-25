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

# Cargar DataFrames
df_jugadores = pd.DataFrame(hoja_jugadores.get_all_records())
df_jugadores.columns = df_jugadores.columns.str.strip().str.lower().str.replace(" ", "_")

records_eval = hoja_eval.get_all_records()
df_eval = pd.DataFrame(records_eval)
if not df_eval.empty:
    df_eval.columns = df_eval.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
else:
    df_eval = pd.DataFrame(columns=[
        'jugador_id', 'fecha_evaluacion', 'talla', 'suma_pliegues', 'salto_horizontal', 'cmj',
        'sprint_10_mts_seg', 'sprint_20_mts_seg', 'sprint_30_mts_seg',
        'agilidad_505', 'vel_lanzada', 'vo2_max', 'pt_musculo', 'pt_grasa', 'comentario'
    ])

# Segmentos de test
tests_composicion = ['talla', 'pt_musculo', 'pt_grasa', 'suma_pliegues']
tests_fisicos = ['salto_horizontal', 'cmj', 'sprint_10_mts_seg', 'sprint_20_mts_seg', 'sprint_30_mts_seg', 'agilidad_505', 'vel_lanzada', 'vo2_max']

tests_dict = {
    "Test de Composición Corporal": tests_composicion,
    "Test Físicos": tests_fisicos
}

etiquetas = {
    "talla": "Talla (cm)", "pt_musculo": "% Músculo", "pt_grasa": "% Grasa", "suma_pliegues": "Suma pliegues",
    "salto_horizontal": "Salto horizontal (cm)", "cmj": "CMJ (cm)",
    "sprint_10_mts_seg": "Sprint 10 mts (seg)", "sprint_20_mts_seg": "Sprint 20 mts (seg)", "sprint_30_mts_seg": "Sprint 30 mts (seg)",
    "agilidad_505": "Agilidad 5-0-5 (seg)", "vel_lanzada": "Velocidad lanzada (km/h)", "vo2_max": "VO2 Máx"
}

# UI
st.title("Ingreso de Evaluaciones Físicas")
tipo_test = st.selectbox("Selecciona el bloque de test", list(tests_dict.keys()))
tests_disponibles = tests_dict[tipo_test]
test_seleccionado = st.selectbox("Selecciona el test a realizar", tests_disponibles, format_func=lambda x: etiquetas[x])

# Filtro de búsqueda por categoría (no restringe la selección)
st.markdown("### Buscar jugadores por categoría (opcional)")
categorias = sorted(df_jugadores["categoria_origen"].unique())
categoria_filtro = st.selectbox("Filtrar jugadores para facilitar la búsqueda", ["Todas"] + categorias)

if categoria_filtro != "Todas":
    sugeridos = df_jugadores[df_jugadores["categoria_origen"] == categoria_filtro]
else:
    sugeridos = df_jugadores

# Multiselect con todos los jugadores disponibles
jugadores_dict = {f"{row['jugador_nombre']} (ID: {row['jugador_id']}) [{row['categoria_origen']}]": row['jugador_id'] for _, row in df_jugadores.iterrows()}

jugadores_sel = st.multiselect("Selecciona los jugadores para este test", jugadores_dict.keys(),
                                default=[f"{row['jugador_nombre']} (ID: {row['jugador_id']}) [{row['categoria_origen']}]" for _, row in sugeridos.iterrows()])

# Funciones
def obtener_fila(jugador_id, fecha):
    for i, fila in enumerate(df_eval.to_dict(orient='records')):
        if fila['jugador_id'] == jugador_id and fila['fecha_evaluacion'] == fecha.strftime("%Y-%m-%d"):
            return i + 2
    return None

def crear_fila_vacia(jugador_id, fecha):
    nueva_fila = {
        'jugador_id': jugador_id,
        'fecha_evaluacion': fecha.strftime("%Y-%m-%d"),
        'talla': "", 'suma_pliegues': "", 'salto_horizontal': "", 'cmj': "",
        'sprint_10_mts_seg': "", 'sprint_20_mts_seg': "", 'sprint_30_mts_seg': "",
        'agilidad_505': "", 'vel_lanzada': "", 'vo2_max': "",
        'pt_musculo': "", 'pt_grasa': "", 'comentario': ""
    }
    hoja_eval.append_row(list(nueva_fila.values()))
    global df_eval
    df_eval = pd.DataFrame(hoja_eval.get_all_records())
    df_eval.columns = df_eval.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    return len(hoja_eval.get_all_values())

def actualizar_valor(jugador_id, columna, valor, fecha):
    fila_idx = obtener_fila(jugador_id, fecha)
    if fila_idx is None:
        fila_idx = crear_fila_vacia(jugador_id, fecha)
    col_idx = df_eval.columns.get_loc(columna) + 1
    hoja_eval.update_cell(fila_idx, col_idx, valor)

# Formulario por jugador
fecha_hoy = date.today()
for nombre in jugadores_sel:
    jugador_id = jugadores_dict[nombre]
    st.subheader(f"{nombre}")
    valor = st.number_input(f"{etiquetas[test_seleccionado]}", min_value=0.0, key=f"{jugador_id}_{test_seleccionado}")
    if st.button(f"💾 Guardar {etiquetas[test_seleccionado]}", key=f"guardar_{jugador_id}_{test_seleccionado}"):
        actualizar_valor(jugador_id, test_seleccionado, valor, fecha_hoy)
        st.success(f"✅ {etiquetas[test_seleccionado]} guardado para {nombre}.")
