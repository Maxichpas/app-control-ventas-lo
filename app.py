import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="FINZA - Control de Ventas y Caja",
    page_icon="📊",
    layout="centered"
)

# ==========================================
# SEGURIDAD BÁSICA (Control de Accesos)
# ==========================================
PASSWORD_CORRECTA = "Finza2026*"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.subheader("🔐 Acceso al Sistema FINZA")
    password_ingresada = st.text_input("Introduce la contraseña:", type="password")
    if st.button("Iniciar Sesión"):
        if password_ingresada == PASSWORD_CORRECTA:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("⚠️ Contraseña incorrecta.")
    st.stop()

# ==========================================
# 1. LECTURA DIRECTA POR URL EN MEMORIA (Infallible)
# ==========================================
# ID de tu Google Sheet real extraído de tu link
SHEET_ID = "1PcL3wmbMCmPtdTYSo6CcOWOPpeHIe7mx2SmeOuWaHA0"

# Convertimos la URL para descarga directa en formato CSV por pestaña
URL_LOCALES = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=LOCALES"
URL_REGISTRO = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=REGISTRO_DIARIO"

df_locales = pd.DataFrame()
df_registro = pd.DataFrame()

try:
    # Leemos directamente usando Pandas (Evita usar el problemático st.connection)
    df_locales = pd.read_csv(URL_LOCALES)
    df_registro = pd.read_csv(URL_REGISTRO)
except Exception as e:
    st.error(f"Aviso de lectura: {e}")

# Datos de respaldo por si el internet del servidor falla
if df_locales.empty:
    df_locales = pd.DataFrame({
        "ID_Local": ["0001", "0002", "0003", "0004", "0005"],
        "Nombre_Local": ["Chulucanas 1", "Chulucanas 2", "Piura Ambulante", "Piura Aypate A7", "Piura Aypate B4"]
    })

if df_registro.empty:
    df_registro = pd.DataFrame(columns=[
        "ID", "Fecha", "ID_Local", "Saldo_Inicial_Caja", "Ventas_Por_Menor", 
        "Ventas_Por_Mayor", "Total_Ventas_Dia", "Ventas_Yape_Digital", 
        "Gastos_Efectivo_Dia", "Descripcion_Gasto", "Diferencia", 
        "Semana", "Año", "Mes", "Mes - Año", "Semana - Año"
    ])

# Título de la Aplicación
st.title("📊 FINZA - Gestión y Finanzas")
st.write("### Sistema de Cuadre de Caja Diario")
st.divider()

# ==========================================
# 2. FORMULARIO DE REGISTRO
# ==========================================
st.subheader("📝 Nuevo Registro de Cierre Diario")

with st.form(key="formulario_ventas", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_sel = st.date_input("Fecha del Registro", datetime.now())
        
        # Ajustamos los ID de locales para que mantengan el formato texto de 4 dígitos
        df_locales["ID_Local"] = df_locales["ID_Local"].astype(str).str.zfill(4)
        dict_locales = dict(zip(df_locales["Nombre_Local"], df_locales["ID_Local"]))
        
        local_nombre_sel = st.selectbox("Seleccione el Local", list(dict_locales.keys()))
        id_local_sel = dict_locales[local_nombre_sel]
        email_usuario = st.text_input("Encargada (Email)", placeholder="ejemplo@finza.com")

    with col2:
        saldo_inicial = st.number_input("Saldo Inicial de Caja (S/.)", min_value=0.0, step=10.0, format="%.2f")
        ventas_menor = st.number_input("Ventas Por Menor (S/.)", min_value=0.0, step=10.0, format="%.2f")
        ventas_mayor = st.number_input("Ventas Por Mayor (S/.)", min_value=0.0, step=10.0, format="%.2f")

    st.markdown("---")
    col3, col4 = st.columns(2)
    
    with col3:
        ventas_yape = st.number_input("Ventas Yape / Digital (S/.)", min_value=0.0, step=10.0, format="%.2f")
        gastos_dia = st.number_input("Gastos Efectivo del Día (S/.)", min_value=0.0, step=5.0, format="%.2f")
        
    with col4:
        descripcion_gasto = st.text_area("Descripción del Gasto", placeholder="Ej: Bolsas, pasajes, limpieza...")
        diferencia_real = st.number_input("Diferencia de Caja", step=1.0, format="%.2f")

    boton_enviar = st.form_submit_button(label="💾 Calcular y Generar Fila")

# ==========================================
# 3. PROCESAMIENTO MATEMÁTICO Y EXPORTACIÓN
# ==========================================
if boton_enviar:
    total_ventas_dia = ventas_menor + ventas_mayor
    fecha_dt = datetime.combine(fecha_sel, datetime.min.time())
    num_semana = fecha_dt.isocalendar()[1]
    num_año = fecha_dt.year
    
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    nombre_mes = meses[fecha_dt.month - 1]
    
    str_mes_año = f"{nombre_mes} - {num_año}"
    str_sem_año = f"Sem {num_semana} - {num_año}"
    id_registro = f"rd{int(datetime.timestamp(datetime.now()))}"

    # Fila formateada de forma idéntica a tus columnas en Sheets
    fila_texto = (
        f"{id_registro}\t{fecha_sel.strftime('%d/%m/%Y')}\t{id_local_sel}\t"
        f"{saldo_inicial}\t{ventas_menor}\t{ventas_mayor}\t{total_ventas_dia}\t"
        f"{ventas_yape}\t{gastos_dia}\t{descripcion_gasto}\t{diferencia_real}\t"
        f"{num_semana}\t{num_año}\t{fecha_dt.month}\t{str_mes_año}\t{str_sem_año}"
    )
    
    st.success(f"✅ ¡Cierre de caja procesado con éxito! ID: {id_registro}")
    st.balloons()
    
    # Bloque informativo para la encargada
    st.info(f"📊 **Resumen del Cálculo:**\n"
            f"* **Local:** {local_nombre_sel} ({id_local_sel})\n"
            f"* **Total Ventas Diarias:** S/. {total_ventas_dia:.2f}\n"
            f"* **Período:** {str_sem_año}")
    
    # Herramienta de contingencia: Genera una línea para copiar y pegar directamente abajo en tu Excel si falla la API
    st.text_area("📋 Fila lista para tu Google Sheets (Copia y pega en la última fila de REGISTRO_DIARIO si lo requieres):", fila_texto)

# ==========================================
# 4. VISUALIZACIÓN DEL HISTORIAL REAL
# ==========================================
st.divider()
st.subheader("🗂️ Vista General de Registros (REGISTRO_DIARIO)")
st.dataframe(df_registro, use_container_width=True, hide_index=True)
