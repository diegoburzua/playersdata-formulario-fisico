import streamlit as st
from datetime import date
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

# Autenticación con Google Sheets desde Streamlit secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = st.secrets["gspread"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Abrir hoja de cálculo y pestañas
spreadsheet = client.open_by_key("1T9lH0MNDQOJACChmK40DslErSkwJBSNSB-RvAFtb2TY")
worksheet_eval = spreadsheet.worksheet("EvaluacionesFisicas")
worksheet_jug = spreadsheet.worksheet("Jugadores")

# Cargar datos
df_eval = pd.DataFrame(worksheet_eval.get_all_records())
df_jug = pd.DataFrame(worksheet_jug.get_all_records())

# Título
st.title("Ingreso de Evaluaciones Físicas")

# Filtro por categoría
categorias = sorted(df_jug['categoria_origen'].unique())
categoria_seleccionada = st.selectbox("Seleccionar categoría", categorias)

# Filtrar jugadores por categoría
df_filtrado = df_jug[df_jug['categoria_origen'] == categoria_seleccionada]
jugador_dict = {f"{row['jugador_nombre']} (ID: {row['jugador_id']})": row['jugador_id'] for _, row in df_filtrado.iterrows()}
jugador_seleccionado = st.selectbox("Seleccionar jugador", list(jugador_dict.keys()))

# Fecha de evaluación
fecha_eval = st.date_input("Fecha de evaluación", value=date.today())

# Buscar fila existente en EvaluacionesFisicas
def obtener_fila(jugador_id, fecha):
    for i, fila in enumerate(df_eval.to_dict(orient='records')):
        if fila['jugador_id'] == jugador_id and fila['fecha_evaluacion'] == fecha.strftime("%Y-%m-%d"):
            return i + 2  # offset por encabezado
    return None

# Insertar nueva fila si no existe
jugador_id = jugador_dict[jugador_seleccionado]
fila_idx = obtener_fila(jugador_id, fecha_eval)
if fila_idx is None:
    nueva_fila = {
        'jugador_id': jugador_id,
        'fecha_evaluacion': fecha_eval.strftime("%Y-%m-%d"),
        'talla': 0, 'suma_pliegues': 0, 'salto_horizontal': 0, 'cmj': 0,
        'sprint_10_mts_seg': 0, 'sprint_20_mts_seg': 0, 'sprint_30_mts_seg': 0,
        'agilidad_505': 0, 'vel_lanzada': 0, 'vo2_max': 0,
        'pt_musculo': 0, 'pt_grasa': 0, 'comentario': ""
    }
    worksheet_eval.append_row(list(nueva_fila.values()))
    df_eval = pd.concat([df_eval, pd.DataFrame([nueva_fila])], ignore_index=True)
    fila_idx = obtener_fila(jugador_id, fecha_eval)

# Función para actualizar celda
def actualizar_valor(columna, valor):
    col_idx = df_eval.columns.get_loc(columna) + 1
    worksheet_eval.update_cell(fila_idx, col_idx, valor)

# Obtener fila actual
fila_actual = df_eval.iloc[fila_idx - 2]

# Campos de ingreso
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
