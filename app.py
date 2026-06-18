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

# Título Principal adaptado al usuario
st.title("📊 FINZA - Gestión y Finanzas")
if user["rol"] == "ADMIN":
    st.write("### Panel de Control General (Modo Administrador)")
else:
    st.write(f"### Sistema de Cierre - Sede: **{user['nombre']}**")

if st.button("🚪 Cerrar
