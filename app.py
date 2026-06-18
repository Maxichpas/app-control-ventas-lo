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
# 1. CONEXIÓN A TU GOOGLE SHEETS REAL
# ==========================================
df_locales = pd.DataFrame()
df_registro = pd.DataFrame()
error_conexion = False

try:
    # Conector oficial de Streamlit
    conn = st.connection("sheets", type="sheets")
    df_locales = conn.read(worksheet="LOCALES", ttl="1m")
    df_registro = conn.read(worksheet="REGISTRO_DIARIO", ttl="0m")
except Exception as e:
    error_conexion = True
    st.error(f"Error de conexión: {e}")

# Datos de respaldo por seguridad si las pestañas están vacías
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
        
        # Formateo seguro del diccionario de locales
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

    boton_enviar = st.form_submit_button(label="💾 Guardar y Procesar Cierre")

# ==========================================
# 3. PROCESAMIENTO MATEMÁTICO Y ENVÍO
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

    # Registro alineado de forma idéntica a tus columnas en Sheets
    datos_nuevos = {
        "ID": id_registro,
        "Fecha": fecha_sel.strftime("%d/%m/%Y"),
        "ID_Local": id_local_sel,
        "Saldo_Inicial_Caja": float(saldo_inicial),
        "Ventas_Por_Menor": float(ventas_menor),
        "Ventas_Por_Mayor": float(ventas_mayor),
        "Total_Ventas_Dia": float(total_ventas_dia),
        "Ventas_Yape_Digital": float(ventas_yape),
        "Gastos_Efectivo_Dia": float(gastos_dia),
        "Descripcion_Gasto": str(descripcion_gasto),
        "Diferencia": float(diferencia_real),
        "Semana": int(num_semana),
        "Año": int(num_año),
        "Mes": int(fecha_dt.month),
        "Mes - Año": str_mes_año,
        "Semana - Año": str_sem_año
    }
    
    try:
        # Volvemos a leer para evitar colisiones si otro local guardó al mismo tiempo
        df_base_real = conn.read(worksheet="REGISTRO_DIARIO", ttl="0m")
        df_nueva_fila = pd.DataFrame([datos_nuevos])
        
        # Concatenamos de forma limpia
        df_final_subir = pd.concat([df_base_real, df_nueva_fila], ignore_index=True)
        
        # Envío oficial usando el token activo de los secrets
        conn.update(worksheet="REGISTRO_DIARIO", data=df_final_subir)
        
        st.success(f"✅ ¡Guardado de forma permanente en Google Sheets! ID: {id_registro}")
        st.balloons()
        st.rerun()
        
    except Exception as error_escribiendo:
        st.error(f"❌ Error al guardar en Google Sheets: {error_escribiendo}")

# ==========================================
# 4. VISUALIZACIÓN DEL HISTORIAL REAL
# ==========================================
st.divider()
st.subheader("🗂️ Vista General de Registros (REGISTRO_DIARIO)")
st.dataframe(df_registro, use_container_width=True, hide_index=True)
