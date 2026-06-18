import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="FINZA - Control de Ventas y Caja",
    page_icon="📊",
    layout="centered"
)

# ==========================================
# 6. SEGURIDAD BÁSICA (Control de Accesos)
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
# 1. CONEXIÓN A DATOS (Google Sheets)
# ==========================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Error al conectar con Google Sheets. Verifica tu archivo .streamlit/secrets.toml")
    st.stop()

# ==========================================
# 2. LÓGICA DE LECTURA (SQL)
# ==========================================
# Leemos las tablas principales de la base de datos
try:
    df_locales = conn.query("SELECT * FROM CATALOGO_LOCALES;", ttl="1m")
    df_registro = conn.query("SELECT * FROM REGISTRO_DIARIO;", ttl="0m") # ttl=0 para leer datos frescos
except Exception as e:
    st.error(f"Error al leer las tablas mediante SQL: {e}")
    st.stop()

# Título de la Aplicación Principal
st.title("📊 FINZA - Gestión y Finanzas")
st.write("### Sistema de Cuadre de Caja Diario")
st.divider()

# ==========================================
# 3. FORMULARIO DE REGISTRO
# ==========================================
st.subheader("📝 Nuevo Registro de Cierre Diario")

with st.form(key="formulario_ventas", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        fecha = st.date_input("Fecha del Registro", datetime.now())
        # Lista desplegable dinámica basada en la tabla CATALOGO_LOCALES
        lista_locales = df_locales["Nombre_Local"].tolist() if not df_locales.empty else ["Local 1", "Local 2", "Local 3", "Local 4", "Local 5"]
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

    # Botón de envío del formulario
    boton_enviar = st.form_submit_button(label="💾 Guardar y Cuadrar Caja")

# ==========================================
# 4. PROCESAMIENTO Y ESCRITURA EN PANDAS
# ==========================================
if boton_enviar:
    if not email_usuario:
        st.warning("⚠️ Por favor, introduce el correo electrónico para la trazabilidad antes de guardar.")
    else:
        # Lógica de Negocio Financiera
        total_ventas_dia = ventas_menor + ventas_mayor
        
        # Efectivo Neto que debió entrar en físico: (Ventas Totales - Lo que fue por Yape - Lo que se gastó)
        efectivo_neto_caja = total_ventas_dia - ventas_yape - gastos_dia
        
        # Total final esperado en la caja física sumando el fondo inicial
        total_en_caja_final = saldo_inicial + efectivo_neto_caja
        
        # Generamos un ID único basado en timestamp para evitar sobreescrituras (Error clásico de sincronización)
        id_registro = f"REG-{int(datetime.timestamp(datetime.now()))}"
        
        # Crear la nueva fila respetando la estructura de datos anterior
        nuevo_registro = pd.DataFrame([{
            "ID": id_registro,
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Local": local_seleccionado,
            "Email_Usuario": email_usuario,
            "Saldo_Inicial_Caja": saldo_inicial,
            "Ventas_Por_Menor": ventas_menor,
            "Ventas_Por_Mayor": ventas_mayor,
            "Total_Ventas_Dia": total_ventas_dia,
            "Ventas_Yape_Digital": ventas_yape,
            "Gastos_Efectivo_Dia": gastos_dia,
            "Descripcion_Gasto": descripcion_gasto,
            "Efectivo_Neto_Caja": efectivo_neto_caja,
            "Total_En_Caja_Final": total_en_caja_final
        }])
        
        # Concatenamos el DataFrame existente con la nueva fila
        df_actualizado = pd.concat([df_registro, nuevo_registro], ignore_index=True)
        
        # Guardamos de forma permanente en la pestaña específica de Google Sheets
        try:
            conn.update(worksheet="REGISTRO_DIARIO", data=df_actualizado)
            st.success(f"✅ ¡Cierre de caja registrado con éxito! ID: {id_registro}")
            st.balloons()
            
            # Mostramos un resumen del cuadre del día en pantalla
            st.info(f"**Resumen Financiero del Día:**\n"
                    f"* **Total Ventas del Día:** S/. {total_ventas_dia:.2f}\n"
                    f"* **Efectivo Neto Esperado (Sin Yape/Gastos):** S/. {efectivo_neto_caja:.2f}\n"
                    f"* **Monto Físico Final en Caja Chica:** S/. {total_en_caja_final:.2f}")
            
            # Forzamos recarga de la página para actualizar el historial inferior
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al guardar en Google Sheets: {e}")

# ==========================================
# 5. VISUALIZACIÓN DEL HISTORIAL
# ==========================================
st.divider()
st.subheader("🗂️ Historial de Registros Diarios")

if not df_registro.empty:
    # Ordenamos por fecha descendente para ver lo último primero
    df_mostrar = df_registro.sort_values(by="Fecha", ascending=False)
    st.dataframe(
        df_mostrar,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Aún no hay registros guardados en esta hoja.")
