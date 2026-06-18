import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página de Streamlit
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
    password_ingresada = st.text_input("Introduce la contraseña para ingresar:", type="password")
    if st.button("Iniciar Sesión"):
        if password_ingresada == PASSWORD_CORRECTA:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("⚠️ Contraseña incorrecta. Inténtalo de nuevo.")
    st.stop()

# ==========================================
# 1. INTENTO DE CONEXIÓN A GOOGLE SHEETS
# ==========================================
df_locales = pd.DataFrame()
df_registro = pd.DataFrame()
usando_datos_simulados = False

try:
    conn = st.connection("sheets", type="sheets")
    # Cambiado a "LOCALES" según tu captura real image_d25e06.png
    df_locales = conn.read(worksheet="LOCALES", ttl="1m")
    df_registro = conn.read(worksheet="REGISTRO_DIARIO", ttl="0m")
except Exception as e:
    usando_datos_simulados = True

# Si la hoja "LOCALES" no carga, usamos los datos reales de tu captura como respaldo seguro
if df_locales.empty:
    df_locales = pd.DataFrame({"Nombre_Local": ["Chulucanas 1", "Chulucanas 2", "Piura Ambulante", "Piura Aypate A7", "Piura Aypate B4"]})

if df_registro.empty:
    df_registro = pd.DataFrame(columns=[
        "ID", "Fecha", "Local", "Email_Usuario", "Saldo_Inicial_Caja", 
        "Ventas_Por_Menor", "Ventas_Por_Mayor", "Total_Ventas_Dia", 
        "Ventas_Yape_Digital", "Gastos_Efectivo_Dia", "Descripcion_Gasto", 
        "Efectivo_Neto_Caja", "Total_En_Caja_Final"
    ])

# Título de la Aplicación Principal
st.title("📊 FINZA - Gestión y Finanzas")
st.write("### Sistema de Cuadre de Caja Diario")

if usando_datos_simulados:
    st.warning("⚠️ Nota: Conexión en espera. Asegúrate de haber guardado la URL en los Secrets de Streamlit.")

st.divider()

# ==========================================
# 2. FORMULARIO DE REGISTRO
# ==========================================
st.subheader("📝 Nuevo Registro de Cierre Diario")

with st.form(key="formulario_ventas", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        fecha = st.date_input("Fecha del Registro", datetime.now())
        
        # Extraemos la columna 'Nombre_Local' que se ve en tu captura
        if "Nombre_Local" in df_locales.columns:
            lista_locales = df_locales["Nombre_Local"].dropna().tolist()
        else:
            lista_locales = ["Chulucanas 1", "Chulucanas 2", "Piura Ambulante", "Piura Aypate A7", "Piura Aypate B4"]
            
        local_seleccionado = st.selectbox("Seleccione el Local", lista_locales)
        email_usuario = st.text_input("Correo de la Encargada (Trazabilidad)", placeholder="ejemplo@finza.com")

    with col2:
        saldo_inicial = st.number_input("Saldo Inicial de Caja Chica (S/.)", min_value=0.0, step=10.0, format="%.2f")
        ventas_menor = st.number_input("Ventas al Por Menor (S/.)", min_value=0.0, step=10.0, format="%.2f")
        ventas_mayor = st.number_input("Ventas al Por Mayor (S/.)", min_value=0.0, step=10.0, format="%.2f")

    st.markdown("---")
    col3, col4 = st.columns(2)
    
    with col3:
        ventas_yape = st.number_input("Monto Recibido por Yape / Digital (S/.)", min_value=0.0, step=10.0, format="%.2f")
        gastos_dia = st.number_input("Gastos en Efectivo del Día (S/.)", min_value=0.0, step=5.0, format="%.2f")
    
    with col4:
        descripcion_gasto = st.text_area("Descripción de los Gastos", placeholder="Ej: Compra de útiles de limpieza, pasajes, etc.")

    boton_enviar = st.form_submit_button(label="💾 Guardar y Cuadrar Caja")

# ==========================================
# 3. PROCESAMIENTO
# ==========================================
if boton_enviar:
    if not email_usuario:
        st.warning("⚠️ Por favor, introduce el correo electrónico para la trazabilidad.")
    else:
        total_ventas_dia = ventas_menor + ventas_mayor
        efectivo_neto_caja = total_ventas_dia - ventas_yape - gastos_dia
        total_en_caja_final = saldo_inicial + efectivo_neto_caja
        id_registro = f"REG-{int(datetime.timestamp(datetime.now()))}"
        
        st.success(f"✅ ¡Cierre calculado con éxito! ID: {id_registro}")
        st.balloons()
        
        st.info(f"**Resumen Financiero ({local_seleccionado}):**\n"
                f"* Total Ventas: S/. {total_ventas_dia:.2f}\n"
                f"* Efectivo Neto Esperado: S/. {efectivo_neto_caja:.2f}\n"
                f"* Total en Caja Chica: S/. {total_en_caja_final:.2f}")

# ==========================================
# 4. VISUALIZACIÓN DEL HISTORIAL
# ==========================================
st.divider()
st.subheader("🗂️ Historial de Registros Diarios")
st.dataframe(df_registro, use_container_width=True, hide_index=True)
