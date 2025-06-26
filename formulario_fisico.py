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

# ID de tu Google Sheets
SPREADSHEET_KEY = "1T9lH0MNDQOJACChmK40DslErSkwJBSNSB-RvAFtb2TY"
spreadsheet = client.open_by_key(SPREADSHEET_KEY)

# Cargar hojas
hoja_jugadores = spreadsheet.worksheet("Jugadores")
hoja_eval = spreadsheet.worksheet("EvaluacionesFisicas")

# Jugadores
df_jugadores = pd.DataFrame(hoja_jugadores.get_all_records())
df_jugadores.columns = df_jugadores.columns.str.strip().str.lower().str.replace(" ", "_")

# Evaluaciones
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

# --- Interfaz de usuario ---
st.title("Ingreso de Evaluaciones Físicas")

# Selección de bloque de test y test específico
bloques_tests = {
    "Test de Composición Corporal": ["talla", "pt_musculo", "pt_grasa", "suma_pliegues"],
    "Test Físicos": [
        "salto_horizontal", "cmj", "sprint_10_mts_seg", "sprint_20_mts_seg",
        "sprint_30_mts_seg", "agilidad_505", "vel_lanzada", "vo2_max"
    ]
}

bloque_sel = st.selectbox("Selecciona el bloque de test", list(bloques_tests.keys()))
test_sel = st.selectbox("Selecciona el test a realizar", bloques_tests[bloque_sel])

# Selección de jugadores por categoría
st.subheader("Buscar jugadores por categoría (opcional)")
categorias = sorted(df_jugadores['categoria_origen'].unique())
categoria_filtrada = st.selectbox("Filtrar jugadores para facilitar la búsqueda", ["Todas"] + categorias)

if categoria_filtrada != "Todas":
    df_visible = df_jugadores[df_jugadores['categoria_origen'] == categoria_filtrada]
else:
    df_visible = df_jugadores

jugadores_dict = {f"{row['jugador_nombre']} (ID: {row['jugador_id']})": row['jugador_id'] for _, row in df_visible.iterrows()}
jugadores_keys = list(jugadores_dict.keys())

jugadores_a_agregar = st.multiselect("Selecciona los jugadores para este test", jugadores_keys)

if 'jugadores_seleccionados' not in st.session_state:
    st.session_state['jugadores_seleccionados'] = []

if st.button("Agregar a la selección"):
    for jugador in jugadores_a_agregar:
        if jugadores_dict[jugador] not in [j[1] for j in st.session_state['jugadores_seleccionados']]:
            st.session_state['jugadores_seleccionados'].append((jugador, jugadores_dict[jugador]))

if st.session_state['jugadores_seleccionados']:
    st.markdown("**Jugadores seleccionados:**")
    for nombre, _ in st.session_state['jugadores_seleccionados']:
        st.markdown(f"- {nombre}")

# Confirmación de selección
disparar_test = st.checkbox("✅ Confirmar selección de jugadores")

# Funciones auxiliares
def obtener_fila(jugador_id, fecha):
    for i, fila in enumerate(df_eval.to_dict(orient='records')):
        if fila['jugador_id'] == jugador_id and fila['fecha_evaluacion'] == fecha.strftime("%Y-%m-%d"):
            return i + 2
    return None

def crear_nueva_fila(jugador_id, fecha):
    nueva_fila = {
        'jugador_id': jugador_id,
        'fecha_evaluacion': fecha.strftime("%Y-%m-%d"),
        'talla': "-", 'suma_pliegues': "-", 'salto_horizontal': "-", 'cmj': "-",
        'sprint_10_mts_seg': "-", 'sprint_20_mts_seg': "-", 'sprint_30_mts_seg': "-",
        'agilidad_505': "-", 'vel_lanzada': "-", 'vo2_max': "-",
        'pt_musculo': "-", 'pt_grasa': "-", 'comentario': ""
    }
    hoja_eval.append_row(list(nueva_fila.values()))
    global df_eval
    df_eval = pd.DataFrame(hoja_eval.get_all_records())
    df_eval.columns = df_eval.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")
    return len(hoja_eval.get_all_values())

def actualizar_valor(jugador_id, columna, valor):
    fila_idx = obtener_fila(jugador_id, date.today())
    if fila_idx is None:
        fila_idx = crear_nueva_fila(jugador_id, date.today())
    col_idx = df_eval.columns.get_loc(columna) + 1
    hoja_eval.update_cell(fila_idx, col_idx, valor)

# Mostrar ingreso de datos si se confirmó
if disparar_test:
    st.subheader(test_sel.replace("_", " ").capitalize())
    for nombre, jugador_id in st.session_state['jugadores_seleccionados']:
        with st.expander(f"{nombre}"):
            valor = st.number_input(f"{test_sel.replace('_', ' ').capitalize()}", min_value=0.0, value=0.0, key=f"{jugador_id}_{test_sel}")
            if st.button(f"💾 Guardar {test_sel.replace('_', ' ').capitalize()}", key=f"guardar_{jugador_id}_{test_sel}"):
                actualizar_valor(jugador_id, test_sel, valor)
                st.success("✅ Guardado correctamente")
