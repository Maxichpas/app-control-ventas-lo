import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import json

# === CONFIGURACIÓN ULTRA-SEGURA: OCULTA GITHUB, MENÚS Y EL "MANAGE APP" ===
st.markdown("""
    <style>
    /* Oculta la barra superior (Menú y GitHub) */
    header {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    
    /* Elimina el botón 'Manage app' de la esquina inferior derecha */
    div[data-testid="stStatusWidget"] {display: none !important;}
    div[class*="stStatusWidget"] {display: none !important;}
    
    /* Bloquea cualquier elemento flotante o marca de agua del sistema */
    .stAppDeployButton {display: none !important;}
    iframe[title="Managed Hosting Banner"] {display: none !important;}
    #streamlitConnectionIndicator {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

# Configuración de la página
st.set_page_config(
    page_title="FINZA - Control de Ventas y Caja",
    page_icon="📊",
    layout="centered"
)

# ==========================================
# CONFIGURACIÓN DE USUARIOS POR TIENDA
# ==========================================
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
    df_registro["ID_Local"] = df_registro["ID_Local"].astype(str).str.zfill(4)
    df_locales["ID_Local"] = df_locales["ID_Local"].astype(str).str.zfill(4)
except Exception as e:
    pass

if df_locales.empty:
    df_locales = pd.DataFrame({
        "ID_Local": ["0001", "0002", "0003", "0004", "0005"],
        "Nombre_Local": ["Chulucanas 1", "Chulucanas 2", "Piura Ambulante", "Piura Aypate A7", "Piura Aypate B4"]
    })

# Título Principal
st.title("📊 FINZA - Gestión y Finanzas")

# Cabecera dinámica y botones de sesión
col_user, col_logout = st.columns([4, 1])
with col_user:
    if user["rol"] == "ADMIN":
        st.write("### Panel de Control General (Modo Administrador)")
    else:
        st.write(f"### Sistema de Cierre - Sede: **{user['nombre']}**")
with col_logout:
    if st.button("🚪 Salir"):
        st.session_state["user_data"] = None
        st.rerun()

st.divider()

# ==========================================
# 2. SISTEMA DE VISTAS (PESTAÑAS)
# ==========================================
if user["rol"] == "ADMIN":
    # El Administrador ve tres pestañas: Registro diario, Historial y sus Gastos Mensuales del Dueño
    tab_cierre, tab_historial, tab_gastos_admin = st.tabs(["📝 Cierre Diario Tiendas", "🗂️ Historial General", "💰 Mis Gastos Mensuales (Dueño)"])
else:
    # Las tiendas solo ven dos pestañas comunes
    tab_cierre, tab_historial = st.tabs(["📝 Nuevo Cierre Diario", "🗂️ Mi Historial"])
    tab_gastos_admin = None

# ---- PESTAÑA 1: FORMULARIO DE CIERRE DIARIO ----
with tab_cierre:
    st.subheader("Formulario de Cierre Diario")
    with st.form(key="formulario_ventas", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_sel = st.date_input("Fecha del Registro", datetime.now())
            if user["rol"] == "ADMIN":
                dict_locales = dict(zip(df_locales["Nombre_Local"], df_locales["ID_Local"]))
                local_nombre_sel = st.selectbox("Seleccione el Local", list(dict_locales.keys()))
                id_local_sel = dict_locales[local_nombre_sel]
            else:
                id_local_sel = user["id_local"]
                st.info(f"Local asignado automáticamente: **{user['nombre']}**")

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
        
        st.markdown("### 🔍 Verificación y Cuadre de Caja")
        col5, col6, col7 = st.columns(3)
        
        efectivo_neto_esperado = saldo_inicial + ventas_menor + ventas_mayor - ventas_yape - gastos_dia
        
        with col5:
            st.metric(label="Efectivo_Neto_Caja (Calculado)", value=f"S/. {efectivo_neto_esperado:.2f}")
        
        with col6:
            efectivo_fisico_real = st.number_input("Total_En_Caja_Final (Físico Real)", min_value=0.0, step=10.0, format="%.2f")
        
        diferencia_real = efectivo_fisico_real - efectivo_neto_esperado
        
        if diferencia_real == 0:
            alerta_cuadre = "OK"
        elif diferencia_real < 0:
            alerta_cuadre = f"FALTA DINERO (S/. {abs(diferencia_real):.2f})"
        else:
            alerta_cuadre = f"SOBRA DINERO (S/. {diferencia_real:.2f})"
        
        with col7:
            st.text_input("Alerta_Cuadre", value=alerta_cuadre, disabled=True)
        
        boton_enviar = st.form_submit_button(label="💾 Enviar Cierre Directo")

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
            "Descripción_Gasto": str(descripcion_gasto),
            "Diferencia": float(diferencia_real),
            "Semana": int(num_semana),
            "Año": int(num_año),
            "Mes": int(fecha_dt.month),
            "Mes_Año": str_mes_año,
            "Semana_Año": str_sem_año
        }
        
        try:
            script_url = st.secrets["connections"]["sheets"]["script_api"]
            response = requests.post(script_url, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            if response.status_code == 200 or "SUCCESS" in response.text:
                st.success(f"🚀 ¡Cierre registrado AUTOMÁTICAMENTE! ID: {id_registro}")
                st.balloons()
                st.rerun()
            else:
                st.error(f"Error en el servidor de Google (Código: {response.status_code})")
        except Exception as err:
            st.error(f"❌ Error de conexión: {err}")

# ---- PESTAÑA 2: HISTORIAL ----
with tab_historial:
    st.subheader("🗂️ Historial de Registros")
    if not df_registro.empty:
        if user["rol"] != "ADMIN":
            df_filtrado = df_registro[df_registro["ID_Local"] == user["id_local"]]
            st.write("Mostrando los registros históricos de tu sucursal.")
        else:
            df_filtrado = df_registro
            st.write("Mostrando registros globales de todas las sedes (Vista Admin).")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.info("No hay registros históricos disponibles.")

# ---- PESTAÑA 3: GASTOS MENSUALES POR LOCAL (SOLO ADMIN) ----
if tab_gastos_admin is not None:
    with tab_gastos_admin:
        st.subheader("📊 Matriz de Costos y Gastos Fijos Mensuales")
        st.write("Configura la estructura de costos y gastos fijos para cada local correspondiente al mes.")
        
        with st.form(key="form_gastos_fijos_admin", clear_on_submit=True):
            # Fila 1: Temporalidad y Destino
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                dict_locales = dict(zip(df_locales["Nombre_Local"], df_locales["ID_Local"]))
                local_gasto_sel = st.selectbox("Seleccione el Local a Configurar", list(dict_locales.keys()))
                id_local_gasto = dict_locales[local_gasto_sel]
            with col_f2:
                mes_gasto = st.selectbox("Mes de Aplicación", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], index=datetime.now().month - 1)
            with col_f3:
                anio_gasto = st.number_input("Año de Aplicación", min_value=2024, max_value=2030, value=datetime.now().year, step=1)
            
            st.markdown("##### 📦 Márgenes de Costo de Ventas")
            col_f4, col_f5 = st.columns(2)
            with col_f4:
                pct_menor = st.number_input("Pct Costo Menor (Ej: 0.60)", min_value=0.0, max_value=1.0, value=0.60, step=0.05, format="%.2f")
            with col_f5:
                pct_mayor = st.number_input("Pct Costo Mayor (Ej: 0.80)", min_value=0.0, max_value=1.0, value=0.80, step=0.05, format="%.2f")
            
            st.markdown("##### 💰 Desglose de Gastos Fijos (S/.)")
            col_f6, col_f7 = st.columns(2)
            with col_f6:
                alquiler = st.number_input("Alquiler (S/.)", min_value=0.0, step=50.0, format="%.2f")
                sueldos = st.number_input("Sueldos / Planilla (S/.)", min_value=0.0, step=50.0, format="%.2f")
            with col_f7:
                servicios = st.number_input("Servicios (Luz/Agua/Net) (S/.)", min_value=0.0, step=10.0, format="%.2f")
                asesoria = st.number_input("Asesoría / Jefe Sede (S/.)", min_value=0.0, step=50.0, format="%.2f")
            
            # Cálculo Automático del Total en Pantalla antes de enviar
            total_gastos_calculado = alquiler + sueldos + servicios + asesoria
            st.metric(label="✨ Total Gastos Fijos Calculados", value=f"S/. {total_gastos_calculado:.2f}")
            
            boton_gasto_admin = st.form_submit_button(label="💾 Guardar en Matriz de Gastos")
            
        if boton_gasto_admin:
            id_gasto_fm = f"fm{int(datetime.timestamp(datetime.now()))}"
            meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            num_mes = meses_lista.index(mes_gasto) + 1
            
            # payload idéntico a tu estructura de columnas para mapearlo en tu Apps Script
            payload_gasto = {
                "ID": id_gasto_fm,
                "Fecha": f"{anio_gasto}-{str(num_mes).zfill(2)}", # Formato YYYY-MM como en tu tabla
                "ID_Local": id_local_gasto,
                "Pct_Costo_Menor": float(pct_menor),
                "Pct_Costo_Mayor": float(pct_mayor),
                "Alquiler": float(alquiler),
                "Sueldos": float(sueldos),
                "Servicios": float(servicios),
                "Asesoria_Jefe": float(asesoria),
                "Total_Gastos_Fijos": float(total_gastos_calculado),
                "Mes": mes_gasto,
                "Año": int(anio_gasto),
                "Mes_Año": f"{mes_gasto} - {anio_gasto}",
                "Origen": "MATRIZ_GASTOS" # Etiqueta para que tu Apps Script sepa a qué pestaña enviarlo
            }
            
            try:
                script_url = st.secrets["connections"]["sheets"]["script_api"]
                response = requests.post(script_url, data=json.dumps(payload_gasto), headers={"Content-Type": "application/json"})
                if response.status_code == 200 or "SUCCESS" in response.text:
                    st.success(f"✅ ¡Estructura de costos registrada para {local_gasto_sel}! ID: {id_gasto_fm}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Error al procesar el guardado en Google Sheets.")
            except Exception as err:
                st.error(f"❌ Error de conexión con la API: {err}")
