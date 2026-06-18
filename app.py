import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# Configuración de la página
st.set_page_config(
    page_title="FINZA - Control de Ventas y Caja",
    page_icon="📊",
    layout="centered"
)

# ==========================================
# CONFIGURACIÓN DE USUARIOS POR TIENDA
# ==========================================
# Definimos las contraseñas y qué "ID_Local" puede ver cada una
USUARIOS = {
    "admin": {"pass": "FinzaMaster2026*", "rol": "ADMIN", "id_local": "TODOS"},
    "chulucanas1": {"pass": "Chulu1*", "rol": "TIENDA", "id_local": "0001", "nombre": "Chulucanas 1"},
    "chulucanas2": {"pass": "Chulu2*", "rol": "TIENDA", "id_local": "0002", "nombre": "Chulucanas 2"},
    "piura_amb": {"pass": "PiuraAmb*", "rol": "TIENDA", "id_local": "0003", "nombre": "Piura Ambulante"},
    "piura_a7": {"pass": "PiuraA7*", "rol": "TIENDA", "id_local": "0004", "nombre": "Piura Aypate A7"},
    "piura_b4": {"pass": "PiuraB4*", "rol": "TIENDA", "id_local": "0005", "nombre": "Piura Aypate B4"},
}

if "user_data" not in st.session_state:
    st.session_state["user_data"] = None

if st.session_state["user_data"] is None:
    st.subheader("🔐 Acceso al Sistema FINZA - Tiendas")
    usuario_ingresado = st.text_input("Usuario (ej: chulucanas1 o admin):").strip().lower()
    password_ingresada = st.text_input("Contraseña:", type="password")
    
    if st.button("Iniciar Sesión"):
        if usuario_ingresado in USUARIOS and USUARIOS[usuario_ingresado]["pass"] == password_ingresada:
            st.session_state["user_data"] = USUARIOS[usuario_ingresado]
            st.rerun()
        else:
            st.error("⚠️ Usuario o contraseña incorrectos.")
    st.stop()

user = st.session_state["user_data"]

# ==========================================
# 1. LECTURA DIRECTA POR URL EN MEMORIA
# ==========================================
SHEET_ID = "1PcL3wmbMCmPtdTYSo6CcOWOPpeHIe7mx2SmeOuWaHA0"
URL_LOCALES = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=LOCALES"
URL_REGISTRO = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=REGISTRO_DIARIO"

df_locales = pd.DataFrame()
df_registro = pd.DataFrame()

try:
    df_locales = pd.read_csv(URL_LOCALES)
    df_registro = pd.read_csv(URL_REGISTRO)
    # Limpieza de strings
    df_registro["ID_Local"] = df_registro["ID_Local"].astype(str).str.zfill(4)
    df_locales["ID_Local"] = df_locales["ID_Local"].astype(str).str.zfill(4)
except Exception as e:
    pass

if df_locales.empty:
    df_locales = pd.DataFrame({
        "ID_Local": ["0001", "0002", "0003", "0004", "0005"],
        "Nombre_Local": ["Chulucanas 1", "Chulucanas 2", "Piura Ambulante", "Piura Aypate A7", "Piura Aypate B4"]
    })

# Título Principal adaptado al usuario logueado
st.title("📊 FINZA - Gestión y Finanzas")
if user["rol"] == "ADMIN":
    st.write("### Panel de Control General (Modo Administrador)")
else:
    st.write(f"### Sistema de Cierre - Sede: **{user['nombre']}**")

if st.button("🚪 Cerrar Sesión"):
    st.session_state["user_data"] = None
    st.rerun()

st.divider()

# ==========================================
# 2. FORMULARIO DE REGISTRO
# ==========================================
st.subheader("📝 Nuevo Registro de Cierre Diario")

with st.form(key="formulario_ventas", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_sel = st.date_input("Fecha del Registro", datetime.now())
        
        # SI ES TIENDA, bloqueamos el local para que solo registre el suyo. SI ES ADMIN, puede elegir.
        if user["rol"] == "ADMIN":
            dict_locales = dict(zip(df_locales["Nombre_Local"], df_locales["ID_Local"]))
            local_nombre_sel = st.selectbox("Seleccione el Local", list(dict_locales.keys()))
            id_local_sel = dict_locales[local_nombre_sel]
        else:
            id_local_sel = user["id_local"]
            st.info(f"Local asignado automáticamente: **{user['nombre']}**")
            
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

    boton_enviar = st.form_submit_button(label="💾 Enviar Cierre Directo a Google Sheets")

# ==========================================
# 3. PROCESAMIENTO Y ENVÍO AUTOMÁTICO
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

    # Diccionario de datos estructurado como JSON para el Apps Script
    payload = {
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
        "Mes_Año": str_mes_año,
        "Semana_Año": str_sem_año
    }

    try:
        # Extraemos la URL de Apps Script desde los secrets de la nube
        script_url = st.secrets["connections"]["sheets"]["script_api"]
        
        # Hacemos el envío POST
        response = requests.post(script_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        
        # Si responde 200 y el texto contiene SUCCESS (o limpia el 401 redireccionando internamente)
        if response.status_code == 200 or "SUCCESS" in response.text:
            st.success(f"🚀 ¡Cierre registrado AUTOMÁTICAMENTE en el Google Sheets! ID: {id_registro}")
            st.balloons()
            st.rerun()
        else:
            st.error(f"Error en respuesta del servidor de Google (Código: {response.status_code})")
            st.info("Intentando guardar de todas formas...")
    except Exception as err:
        st.error(f"❌ Error al conectar con la API de Google: {err}")

# ==========================================
# 4. VISUALIZACIÓN INTELIGENTE (FILTRADA POR TIENDA)
# ==========================================
st.divider()
st.subheader("🗂️ Historial de Registros")

if not df_registro.empty:
    # APLICAMOS EL FILTRO DE SEGURIDAD
    if user["rol"] != "ADMIN":
        # La tienda solo ve filas donde coincida su ID_Local
        df_filtrado = df_registro[df_registro["ID_Local"] == user["id_local"]]
        st.write(f"Mostrando solo los registros históricos de tu sucursal.")
    else:
        # El Administrador ve absolutamente todo sin restricciones
        df_filtrado = df_registro
        st.write("Mostrando registros globales de todas las sedes (Vista Admin).")
        
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
else:
    st.info("No hay registros históricos disponibles en este momento.")
