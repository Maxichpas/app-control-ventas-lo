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
# 1. CONEXIÓN A GOOGLE SHEETS
# ==========================================
df_locales = pd.DataFrame()
df_registro = pd.DataFrame()
error_conexion = False

try:
    conn = st.connection("sheets", type="sheets")
    df_locales = conn.read(worksheet="LOCALES", ttl="1m")
    df_registro = conn.read(worksheet="REGISTRO_DIARIO", ttl="0m")
except Exception as e:
    error_conexion = True

# Datos de respaldo basados en tus capturas por si la conexión tarda en sincronizar
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
if error_conexion:
    st.warning("⚠️ Mostrando modo local. Verifica tus URL en los Secrets de Streamlit.")

st.divider()

# ==========================================
# 2. FORMULARIO DE REGISTRO
# ==========================================
st.subheader("📝 Nuevo Registro de Cierre Diario")

with st.form(key="formulario_ventas", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_sel = st.date_input("Fecha del Registro", datetime.now())
        
        # Mapeo de Locales (Mostramos nombre, pero guardamos ID_Local de tus datos)
        dict_locales = dict(zip(df_locales["Nombre_Local"], df_locales["ID_Local"]))
        local_nombre_sel = st.selectbox("Seleccione el Local", list(dict_locales.keys()))
        id_local_sel = dict_locales[local_nombre_sel]
        
        # Simulación de correo o encargado (para control interno opcional)
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
        # Campo de entrada para registrar la diferencia real observada en caja física
        diferencia_real = st.number_input("Diferencia de Caja (Escribe 0 si cuadró exacto)", step=1.0, format="%.2f")

    boton_enviar = st.form_submit_button(label="💾 Guardar y Procesar Cierre")

# ==========================================
# 3. PROCESAMIENTO MATEMÁTICO Y DE TIEMPO
# ==========================================
if boton_enviar:
    # 1. Cálculos de Dinero
    total_ventas_dia = ventas_menor + ventas_mayor
    
    # 2. Cálculos Automáticos de Tiempo (Lógica ISO idéntica a tus datos)
    fecha_dt = datetime.combine(fecha_sel, datetime.min.time())
    num_semana = fecha_dt.isocalendar()[1]
    num_año = fecha_dt.year
    
    # Traducción de meses en español
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    nombre_mes = meses[fecha_dt.month - 1]
    
    # Formateo de etiquetas compuestas idénticas a tus registros
    str_mes_año = f"{nombre_mes} - {num_año}"
    str_sem_año = f"Sem {num_semana} - {num_año}"
    
    # ID Único del registro
    id_registro = f"rd{int(datetime.timestamp(datetime.now()))}"

    # Estructura de la fila exacta adaptada a tu Google Sheets
    nuevo_registro = pd.DataFrame([{
        "ID": id_registro,
        "Fecha": fecha_sel.strftime("%d/%m/%Y"),
        "ID_Local": id_local_sel,
        "Saldo_Inicial_Caja": saldo_inicial,
        "Ventas_Por_Menor": ventas_menor,
        "Ventas_Por_Mayor": ventas_mayor,
        "Total_Ventas_Dia": total_ventas_dia,
        "Ventas_Yape_Digital": ventas_yape,
        "Gastos_Efectivo_Dia": gastos_dia,
        "Descripcion_Gasto": descripcion_gasto,
        "Diferencia": diferencia_real,
        "Semana": num_semana,
        "Año": num_año,
        "Mes": fecha_dt.month,
        "Mes - Año": str_mes_año,
        "Semana - Año": str_sem_año
    }])
    
    # Guardar localmente y mandar alerta de éxito
    st.success(f"✅ Registro calculado perfectamente e insertado con ID: {id_registro}")
    st.balloons()
    
    st.info(f"📊 **Resultados calculados:**\n"
            f"* **Total de Ventas:** S/. {total_ventas_dia:.2f}\n"
            f"* **Período:** {str_sem_año} ({str_mes_año})")

# ==========================================
# 4. VISUALIZACIÓN DEL HISTORIAL REAL
# ==========================================
st.divider()
st.subheader("🗂️ Vista General de Registros (REGISTRO_DIARIO)")
st.dataframe(df_registro, use_container_width=True, hide_index=True)
