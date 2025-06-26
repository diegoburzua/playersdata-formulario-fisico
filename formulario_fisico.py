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

# ID del Google Sheet
SPREADSHEET_KEY = "1T9lH0MNDQOJACChmK40DslErSkwJBSNSB-RvAFtb2TY"
spreadsheet = client.open_by_key(SPREADSHEET_KEY)

# Cargar hojas
hoja_jugadores = spreadsheet.worksheet("Jugadores")
hoja_eval = spreadsheet.worksheet("EvaluacionesFisicas")

# Cargar DataFrame jugadores
df_jugadores = pd.DataFrame(hoja_jugadores.get_all_records())
df_jugadores.columns = df_jugadores.columns.str.strip().str.lower().str.replace(" ", "_")

# Título
st.title("Ingreso de Evaluaciones Físicas")

# Bloques de test
bloques_test = {
    "Test de Composición Corporal": {
        "Talla (cm)": "talla",
        "% Músculo": "pt_musculo",
        "% Grasa": "pt_grasa",
        "Suma de pliegues": "suma_pliegues"
    },
    "Test Físicos": {
        "Salto horizontal (cm)": "salto_horizontal",
        "CMJ (cm)": "cmj",
        "Sprint 10 mts (seg)": "sprint_10_mts_seg",
        "Sprint 20 mts (seg)": "sprint_20_mts_seg",
        "Sprint 30 mts (seg)": "sprint_30_mts_seg",
        "Agilidad 5-0-5 (seg)": "agilidad_505",
        "Vel. lanzada (km/h)": "vel_lanzada",
        "VO2 Max": "vo2_max"
    }
}

# Selección bloque y test
bloque_sel = st.selectbox("Selecciona el bloque de test", list(bloques_test.keys()))
test_dict = bloques_test[bloque_sel]
nombre_test = st.selectbox("Selecciona el test a realizar", list(test_dict.keys()))
columna_test = test_dict[nombre_test]

# Filtrar por categoría
st.subheader("Buscar jugadores por categoría (opcional)")
categorias = ["Todas"] + sorted(df_jugadores["categoria_origen"].unique())
categoria_sel = st.selectbox("Filtrar jugadores para facilitar la búsqueda", categorias)

if categoria_sel != "Todas":
    df_filtrado = df_jugadores[df_jugadores["categoria_origen"] == categoria_sel]
else:
    df_filtrado = df_jugadores

df_filtrado["display"] = df_filtrado.apply(lambda row: f"{row['jugador_nombre']} (ID: {row['jugador_id']})", axis=1)

# Inicializar selección persistente
if "jugadores_seleccionados" not in st.session_state:
    st.session_state.jugadores_seleccionados = []

# Selección múltiple y agregación
seleccionados = st.multiselect("Selecciona los jugadores para este test", df_filtrado["display"].tolist())

if st.button("Agregar a la selección"):
    nuevos_ids = [int(s.split("ID:")[1].split(")")[0].strip()) for s in seleccionados]
    for i in nuevos_ids:
        if i not in st.session_state.jugadores_seleccionados:
            st.session_state.jugadores_seleccionados.append(i)

# Mostrar selección actual con botón para eliminar
st.markdown("### Jugadores seleccionados:")
eliminar = []
for idx, jugador_id in enumerate(st.session_state.jugadores_seleccionados):
    jugador = df_jugadores[df_jugadores["jugador_id"] == jugador_id].iloc[0]
    col1, col2 = st.columns([5, 1])
    with col1:
        st.write(f"- {jugador['jugador_nombre']} (ID: {jugador_id}) [{jugador['categoria_origen']}]")
    with col2:
        if st.button("❌", key=f"del_{jugador_id}"):
            eliminar.append(idx)

for idx in sorted(eliminar, reverse=True):
    del st.session_state.jugadores_seleccionados[idx]

# Confirmar
confirmar = st.checkbox("✅ Confirmar selección de jugadores")

# Ingreso de datos
if confirmar:
    st.markdown(f"## {nombre_test}")
    for jugador_id in st.session_state.jugadores_seleccionados:
        jugador = df_jugadores[df_jugadores["jugador_id"] == jugador_id].iloc[0]
        nombre_jugador = jugador["jugador_nombre"]
        st.markdown(f"**{nombre_jugador} (ID: {jugador_id}) [Categoría: {jugador['categoria_origen']}]**")

        valor = st.number_input(f"{nombre_test}", min_value=0.0, step=0.01, key=f"{columna_test}_{jugador_id}")
        if st.button(f"💾 Guardar {nombre_test}", key=f"guardar_{columna_test}_{jugador_id}"):
            # Buscar fila por jugador + fecha
            registros = hoja_eval.get_all_records()
            fila_idx = None
            for i, row in enumerate(registros):
                if str(row["jugador_id"]) == str(jugador_id) and row["fecha_evaluacion"] == date.today().strftime("%Y-%m-%d"):
                    fila_idx = i + 2  # 1-indexed + encabezado
                    break

            if fila_idx:
                col_idx = hoja_eval.row_values(1).index(columna_test) + 1
                hoja_eval.update_cell(fila_idx, col_idx, valor)
            else:
                fila = {
                    'jugador_id': jugador_id,
                    'fecha_evaluacion': date.today().strftime("%Y-%m-%d"),
                    'talla': "", 'suma_pliegues': "", 'salto_horizontal': "", 'cmj': "",
                    'sprint_10_mts_seg': "", 'sprint_20_mts_seg': "", 'sprint_30_mts_seg': "",
                    'agilidad_505': "", 'vel_lanzada': "", 'vo2_max': "",
                    'pt_musculo': "", 'pt_grasa': "", 'comentario': ""
                }
                fila[columna_test] = valor
                hoja_eval.append_row([fila[col] for col in fila])

            st.success(f"✅ {nombre_test} guardado para {nombre_jugador}")
