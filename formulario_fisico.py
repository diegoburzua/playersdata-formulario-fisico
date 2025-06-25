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

# Google Sheet
SPREADSHEET_KEY = "1T9lH0MNDQOJACChmK40DslErSkwJBSNSB-RvAFtb2TY"
spreadsheet = client.open_by_key(SPREADSHEET_KEY)
hoja_jugadores = spreadsheet.worksheet("Jugadores")
hoja_eval = spreadsheet.worksheet("EvaluacionesFisicas")

# DataFrames
jugadores_df = pd.DataFrame(hoja_jugadores.get_all_records())
jugadores_df.columns = jugadores_df.columns.str.strip().str.lower().str.replace(" ", "_")

records_eval = hoja_eval.get_all_records()
eval_df = pd.DataFrame(records_eval)
if not eval_df.empty:
    eval_df.columns = eval_df.columns.str.strip().str.lower().str.replace(" ", "_")
else:
    eval_df = pd.DataFrame(columns=[
        'jugador_id', 'fecha_evaluacion', 'talla', 'suma_pliegues', 'salto_horizontal', 'cmj',
        'sprint_10_mts_seg', 'sprint_20_mts_seg', 'sprint_30_mts_seg', 'agilidad_505', 'vel_lanzada',
        'vo2_max', 'pt_musculo', 'pt_grasa', 'comentario'])

# Definiciones
bloques_test = {
    "Test de Composición Corporal": ["talla", "pt_musculo", "pt_grasa", "suma_pliegues"],
    "Test Físicos": ["salto_horizontal", "cmj", "sprint_10_mts_seg", "sprint_20_mts_seg",
                      "sprint_30_mts_seg", "agilidad_505", "vel_lanzada", "vo2_max"]
}

nombres_columnas = {
    "talla": "Talla (cm)",
    "suma_pliegues": "Suma de pliegues",
    "salto_horizontal": "Salto horizontal (cm)",
    "cmj": "CMJ (cm)",
    "sprint_10_mts_seg": "Sprint 10 mts (seg)",
    "sprint_20_mts_seg": "Sprint 20 mts (seg)",
    "sprint_30_mts_seg": "Sprint 30 mts (seg)",
    "agilidad_505": "Agilidad 5-0-5 (seg)",
    "vel_lanzada": "Vel. lanzada (km/h)",
    "vo2_max": "VO2 Max",
    "pt_musculo": "% Músculo",
    "pt_grasa": "% Grasa"
}

# Interfaz
st.title("Ingreso de Evaluaciones Físicas")

bloque = st.selectbox("Selecciona el bloque de test", list(bloques_test.keys()))
test_seleccionado = st.selectbox("Selecciona el test a realizar", bloques_test[bloque])

# Filtro por categoría
st.subheader("Buscar jugadores por categoría (opcional)")
categorias = sorted(jugadores_df['categoria_origen'].unique())
categoria_filtro = st.selectbox("Filtrar jugadores para facilitar la búsqueda", ["Todas"] + categorias)

if categoria_filtro == "Todas":
    jugadores_filtrados = jugadores_df
else:
    jugadores_filtrados = jugadores_df[jugadores_df['categoria_origen'] == categoria_filtro]

jugador_opcion = st.selectbox("Selecciona los jugadores para este test", jugadores_filtrados.apply(
    lambda x: f"{x['jugador_nombre']} (ID: {x['jugador_id']})", axis=1))

# Estado de selección acumulada
if "jugadores_seleccionados" not in st.session_state:
    st.session_state.jugadores_seleccionados = []

if st.button("Agregar a la selección"):
    if jugador_opcion not in st.session_state.jugadores_seleccionados:
        st.session_state.jugadores_seleccionados.append(jugador_opcion)

# Mostrar lista de seleccionados
st.markdown("**Jugadores seleccionados:**")
for j in st.session_state.jugadores_seleccionados:
    st.markdown(f"- {j}")

if st.checkbox("✅ Confirmar selección de jugadores"):
    st.subheader(nombres_columnas[test_seleccionado])

    for jugador_str in st.session_state.jugadores_seleccionados:
        nombre, resto = jugador_str.split(" (ID: ")
        jugador_id = int(resto.replace(")", ""))
        st.markdown(f"**{jugador_str}**")

        valor = st.number_input(nombres_columnas[test_seleccionado], min_value=0.0, format="%.2f", key=f"input_{jugador_id}")
        if st.button(f"💾 Guardar {nombres_columnas[test_seleccionado]}", key=f"btn_{jugador_id}"):
            # Obtener fila o crear nueva
            hoy = date.today().strftime("%Y-%m-%d")
            fila_idx = next((i+2 for i, row in enumerate(eval_df.to_dict(orient="records"))
                             if row['jugador_id'] == jugador_id and row['fecha_evaluacion'] == hoy), None)
            if fila_idx is None:
                nueva_fila = {col: "-" for col in eval_df.columns}
                nueva_fila['jugador_id'] = jugador_id
                nueva_fila['fecha_evaluacion'] = hoy
                hoja_eval.append_row([nueva_fila.get(col, "") for col in eval_df.columns])
                fila_idx = len(hoja_eval.get_all_values())
            # Obtener índice de columna
            col_idx = eval_df.columns.get_loc(test_seleccionado) + 1
            hoja_eval.update_cell(fila_idx, col_idx, valor)
            st.success(f"✅ {nombres_columnas[test_seleccionado]} guardado para {nombre}.")
