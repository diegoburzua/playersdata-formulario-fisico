import streamlit as st
import pyodbc
from datetime import date

# Conexión a SQL Server
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=DESKTOP-EDB1FCU\\SQLEXPRESS;'
    'DATABASE=PLAYERSDATA;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

# Título
st.title("Ingreso de Evaluaciones Físicas")

# Filtro por categoría de origen
cursor.execute("SELECT DISTINCT categoria_origen FROM Jugadores")
categorias = [row[0] for row in cursor.fetchall()]
categoria_seleccionada = st.selectbox("Seleccionar categoría", categorias)

# Filtrar jugadores por categoría
cursor.execute("SELECT jugador_id, jugador_nombre FROM Jugadores WHERE categoria_origen = ?", (categoria_seleccionada,))
jugadores = cursor.fetchall()
jugador_dict = {f"{nombre} (ID: {id})": id for id, nombre in jugadores}
jugador_seleccionado = st.selectbox("Seleccionar jugador", list(jugador_dict.keys()))

# Fecha de evaluación
fecha_eval = st.date_input("Fecha de evaluación", value=date.today())

# Verificar si ya existe una evaluación para ese jugador en esa fecha
cursor.execute("""
    SELECT COUNT(*) FROM EvaluacionesFisicas 
    WHERE jugador_id = ? AND fecha_evaluacion = ?
""", (jugador_dict[jugador_seleccionado], fecha_eval))
existe = cursor.fetchone()[0]

# Si no existe, insertar evaluación vacía
if not existe:
    cursor.execute("""
        INSERT INTO EvaluacionesFisicas (
            jugador_id, fecha_evaluacion
        ) VALUES (?, ?)
    """, (jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()

# Obtener valores existentes
cursor.execute("""
    SELECT suma_pliegues, salto_horizontal, cmj, sprint_10_mts_seg, sprint_20_mts_seg,
           sprint_30_mts_seg, agilidad_505, vel_lanzada, vo2_max, pt_musculo, pt_grasa, comentario
    FROM EvaluacionesFisicas
    WHERE jugador_id = ? AND fecha_evaluacion = ?
""", (jugador_dict[jugador_seleccionado], fecha_eval))
valores = cursor.fetchone()

# Crear variables con valores precargados
(
    valor_suma_pliegues, valor_salto_horizontal, valor_cmj,
    valor_sprint10, valor_sprint20, valor_sprint30,
    valor_agilidad, valor_vel_lanzada, valor_vo2,
    valor_pt_musculo, valor_pt_grasa, valor_comentario
) = valores if valores else (None,) * 12

# Inputs con valores precargados y botones por campo
suma_pliegues = st.number_input("Suma de pliegues", min_value=0.0, value=valor_suma_pliegues or 0.0)
if st.button("💾 Guardar suma de pliegues"):
    cursor.execute("""
        UPDATE EvaluacionesFisicas SET suma_pliegues = ?
        WHERE jugador_id = ? AND fecha_evaluacion = ?
    """, (suma_pliegues, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ Suma de pliegues guardada.")

salto_horizontal = st.number_input("Salto horizontal (cm)", min_value=0.0, value=valor_salto_horizontal or 0.0)
if st.button("💾 Guardar salto horizontal"):
    cursor.execute("UPDATE EvaluacionesFisicas SET salto_horizontal = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (salto_horizontal, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ Salto horizontal guardado.")

cmj = st.number_input("CMJ (cm)", min_value=0.0, value=valor_cmj or 0.0)
if st.button("💾 Guardar CMJ"):
    cursor.execute("UPDATE EvaluacionesFisicas SET cmj = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (cmj, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ CMJ guardado.")

sprint10 = st.number_input("Sprint 10 mts (seg)", min_value=0.0, value=valor_sprint10 or 0.0)
if st.button("💾 Guardar Sprint 10m"):
    cursor.execute("UPDATE EvaluacionesFisicas SET sprint_10_mts_seg = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (sprint10, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ Sprint 10m guardado.")

sprint20 = st.number_input("Sprint 20 mts (seg)", min_value=0.0, value=valor_sprint20 or 0.0)
if st.button("💾 Guardar Sprint 20m"):
    cursor.execute("UPDATE EvaluacionesFisicas SET sprint_20_mts_seg = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (sprint20, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ Sprint 20m guardado.")

sprint30 = st.number_input("Sprint 30 mts (seg)", min_value=0.0, value=valor_sprint30 or 0.0)
if st.button("💾 Guardar Sprint 30m"):
    cursor.execute("UPDATE EvaluacionesFisicas SET sprint_30_mts_seg = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (sprint30, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ Sprint 30m guardado.")

agilidad = st.number_input("Agilidad 5-0-5 (seg)", min_value=0.0, value=valor_agilidad or 0.0)
if st.button("💾 Guardar Agilidad"):
    cursor.execute("UPDATE EvaluacionesFisicas SET agilidad_505 = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (agilidad, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ Agilidad guardada.")

vel_lanzada = st.number_input("Vel. lanzada (km/h)", min_value=0.0, value=valor_vel_lanzada or 0.0)
if st.button("💾 Guardar Vel. lanzada"):
    cursor.execute("UPDATE EvaluacionesFisicas SET vel_lanzada = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (vel_lanzada, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ Vel. lanzada guardada.")

vo2 = st.number_input("VO2 Max", min_value=0.0, value=valor_vo2 or 0.0)
if st.button("💾 Guardar VO2 Max"):
    cursor.execute("UPDATE EvaluacionesFisicas SET vo2_max = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (vo2, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ VO2 Max guardado.")

pt_musculo = st.number_input("% Músculo", min_value=0.0, value=valor_pt_musculo or 0.0)
if st.button("💾 Guardar % Músculo"):
    cursor.execute("UPDATE EvaluacionesFisicas SET pt_musculo = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (pt_musculo, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ % Músculo guardado.")

pt_grasa = st.number_input("% Grasa", min_value=0.0, value=valor_pt_grasa or 0.0)
if st.button("💾 Guardar % Grasa"):
    cursor.execute("UPDATE EvaluacionesFisicas SET pt_grasa = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (pt_grasa, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ % Grasa guardado.")

comentario = st.text_area("Comentario (opcional)", value=valor_comentario or "")
if st.button("💾 Guardar Comentario"):
    cursor.execute("UPDATE EvaluacionesFisicas SET comentario = ? WHERE jugador_id = ? AND fecha_evaluacion = ?",
                   (comentario, jugador_dict[jugador_seleccionado], fecha_eval))
    conn.commit()
    st.success("✅ Comentario guardado.")

# Botón para guardar todo junto
if st.button("📤 Guardar evaluación completa"):
    cursor.execute("""
        UPDATE EvaluacionesFisicas SET
            suma_pliegues = ?, salto_horizontal = ?, cmj = ?,
            sprint_10_mts_seg = ?, sprint_20_mts_seg = ?, sprint_30_mts_seg = ?,
            agilidad_505 = ?, vel_lanzada = ?, vo2_max = ?,
            pt_musculo = ?, pt_grasa = ?, comentario = ?
        WHERE jugador_id = ? AND fecha_evaluacion = ?
    """, (
        suma_pliegues, salto_horizontal, cmj,
        sprint10, sprint20, sprint30,
        agilidad, vel_lanzada, vo2,
        pt_musculo, pt_grasa, comentario,
        jugador_dict[jugador_seleccionado], fecha_eval
    ))
    conn.commit()
    st.success("📤 Evaluación completa guardada exitosamente.")
