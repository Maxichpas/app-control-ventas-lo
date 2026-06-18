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
# 1. CONEXIÓN NATIVA A GOOGLE SHEETS
# ==========================================
try:
    # Usamos el conector nativo de Streamlit para Sheets (no requiere librerías externas)
    conn = st.connection("sheets", type="sheets")
except Exception as e:
    st.error("Error al conectar con Google Sheets. Verifica tus Secrets en Streamlit Cloud.")
    st.stop()

# ==========================================
# 2. LÓGICA DE LECTURA DE DATOS
# ==========================================
try:
    # El conector nativo lee las pestañas directamente como DataFrames
    df_locales = conn.read(worksheet="CATALOGO_LOCALES", ttl="1m")
    df_registro = conn.read(worksheet="REGISTRO_DIARIO", ttl="0m")
except Exception as e:
    st.error(f"Error al leer las pestañas del Google Sheet: {e}")
    st.write("Asegúrate de que los nombres de las pestañas coincidan exactamente.")
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
        efectivo_neto_caja = total_ventas_dia - ventas_yape - gastos_dia
        total_en_caja_final = saldo_inicial + efectivo_neto_caja
        
        id_registro = f"REG-{int(datetime.timestamp(datetime.now()))}"
        
        # Estructura del nuevo registro
        nuevo_registro = pd.DataFrame([{
            "ID": id_registro,
            "Fecha": str(fecha),
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
        
        # Unimos los datos
        df_actualizado = pd.concat([df_registro, nuevo_registro], ignore_index=True)
        
        # Guardamos usando la función nativa de Streamlit para actualizar
        try:
            # Nota: El conector nativo de Streamlit requiere una cuenta de servicio o OAuth en los Secrets para escribir.
            # Asegúrate de haber configurado tu archivo de Secrets correctamente en la nube.
            st.write("Procesando guardado...")
            # En el conector nativo de Streamlit, para actualizar se vuelve a subir el dataframe modificado mediante gspread interno
            # Si usas la URL pública en los secrets, esta función será de solo lectura. Para escribir necesitas las credenciales completas JSON en secrets.
            # Como alternativa directa de desarrollo rápido si tu hoja es pública para edición:
            # Mandamos la actualización de datos
            st.error("Para habilitar la escritura directa desde la web, recuerda configurar tus Google Credentials JSON en los Secrets de Streamlit.")
            
            # (Opcional) Si configuraste los Secrets con formato de cuenta de servicio completa:
            # conn.update(worksheet="REGISTRO_DIARIO", data=df_actualizado)
            
            st.info(f"**Simulación de Cuadre Exitoso:**\n"
                    f"* Total Ventas: S/. {total_ventas_dia:.2f}\n"
                    f"* Caja Final Esperada: S/. {total_en_caja_final:.2f}")
            
        except Exception as e:
            st.error(f"❌ Error al escribir: {e}")

# ==========================================
# 5. VISUALIZACIÓN DEL HISTORIAL
# ==========================================
st.divider()
st.subheader("🗂️ Historial de Registros Diarios")

if df_registro is not None and not df_registro.empty:
    st.dataframe(df_registro, use_container_width=True, hide_index=True)
else:
    st.info("Aún no hay datos cargados en esta vista.")
