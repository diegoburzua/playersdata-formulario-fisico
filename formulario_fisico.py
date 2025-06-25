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

# Convertir a DataFrames y normalizar columnas
df_jugadores = pd.DataFrame(hoja_jugadores.get_all_records())
df_jugadores.columns = df_jugadores.columns.str.strip().str.lower().str.replace(" ", "_")

df_eval = pd.DataFrame(hoja_eval.get_all_records())
df_eval.columns = df_eval.columns.str.strip().str.lower().str.replace(" ", "_")

# Título
st.title("Ingreso de Evaluaciones Físicas")

# Filtro por categoría
categorias = sorted(df_jugadores['categoria_origen'].unique())
categoria_sel = st.selectbox("Seleccionar categoría", categorias)

# Jugadores de esa categoría
df_cat = df_jugadores[df_jugadores['categoria_origen'] == categoria_sel]
jugadores_dict = {f"{row['jugador_nombre']} (ID: {row['jugador_id']})": row['jugador_id'] for _, row in df_cat.iterrows()}
jugador_sel = st.selectbox("Seleccionar jugador", list(jugadores_dict.keys()))
jugador_id = jugadores_dict[jugador_sel]

# Fecha
fecha_eval = st.date_input("Fecha de evaluación", value=date.today())

# Función para obtener fila existente
def obtener_fila(jugador_id, fecha):
    for i, fila in enumerate(df_eval.to_dict(orient='records')):
        if fila['jugador_id'] == jugador_id and fila['fecha_evaluacion'] == fecha.strftime("%Y-%m-%d"):
            return i + 2  # +2 por encabezado y 1-indexing
    return None

# Función para crear nueva fila si no existe
def crear_nueva_fila(jugador_id, fecha):
    nueva_fila = {
        'jugador_id': jugador_id,
        'fecha_evaluacion': fecha.strftime("%Y-%m-%d"),
        'talla': 0,
        'suma_pliegues': 0, 'salto_horizontal': 0, 'cmj': 0,
        'sprint_10_mts_seg': 0, 'sprint_20_mts_seg': 0, 'sprint_30_mts_seg': 0,
        'agilidad_505': 0, 'vel_lanzada': 0, 'vo2_max': 0,
        'pt_musculo': 0, 'pt_grasa': 0, 'comentario': ""
    }
    hoja_eval.append_row(list(nueva_fila.values()))
    return obtener_fila(jugador_id, fecha)

# Función para actualizar un valor (crea fila si es necesario)
def actualizar_valor(columna, valor):
    global df_eval, fila_actual
    fila_idx = obtener_fila(jugador_id, fecha_eval)
    if fila_idx is None:
        fila_idx = crear_nueva_fila(jugador_id, fecha_eval)
        df_eval = pd.DataFrame(hoja_eval.get_all_records())
        df_eval.columns = df_eval.columns.str.strip().str.lower().str.replace(" ", "_")
    col_idx = df_eval.columns.get_loc(columna) + 1
    hoja_eval.update_cell(fila_idx, col_idx, valor)
    fila_actual = df_eval.iloc[fila_idx - 2]

# Obtener fila actual si existe
fila_idx = obtener_fila(jugador_id, fecha_eval)
fila_actual = df_eval.iloc[fila_idx - 2] if fila_idx else {
    'talla': 0, 'suma_pliegues': 0, 'salto_horizontal': 0, 'cmj': 0,
    'sprint_10_mts_seg': 0, 'sprint_20_mts_seg': 0, 'sprint_30_mts_seg': 0,
    'agilidad_505': 0, 'vel_lanzada': 0, 'vo2_max': 0,
    'pt_musculo': 0, 'pt_grasa': 0, 'comentario': ""
}

# Campos físicos
campos = [
    ("talla", "Talla (cm)"),
    ("suma_pliegues", "Suma de pliegues"),
    ("salto_horizontal", "Salto horizontal (cm)"),
    ("cmj", "CMJ (cm)"),
    ("sprint_10_mts_seg", "Sprint 10 mts (seg)"),
    ("sprint_20_mts_seg", "Sprint 20 mts (seg)"),
    ("sprint_30_mts_seg", "Sprint 30 mts (seg)"),
    ("agilidad_505", "Agilidad 5-0-5 (seg)"),
    ("vel_lanzada", "Vel. lanzada (km/h)"),
    ("vo2_max", "VO2 Max"),
    ("pt_musculo", "% Músculo"),
    ("pt_grasa", "% Grasa")
]

for campo, etiqueta in campos:
    valor = st.number_input(etiqueta, min_value=0.0, value=float(fila_actual[campo]))
    if st.button(f"💾 Guardar {etiqueta}"):
        actualizar_valor(campo, valor)
        st.success(f"✅ {etiqueta} guardado.")

# Comentario
comentario = st.text_area("Comentario (opcional)", value=fila_actual['comentario'])
if st.button("💾 Guardar Comentario"):
    actualizar_valor("comentario", comentario)
    st.success("✅ Comentario guardado.")

# Guardar evaluación completa
if st.button("📤 Guardar evaluación completa"):
    for campo, _ in campos:
        actualizar_valor(campo, float(locals()[campo]))
    actualizar_valor("comentario", comentario)
    st.success("📤 Evaluación completa guardada exitosamente.")
