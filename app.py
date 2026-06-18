import streamlit as st

st.title("Mi Control de Ventas 🚀")
nombre_cliente = st.text_input("Nombre del Cliente:")
monto = st.number_input("Monto de la Venta ($):", min_value=0.0)

if st.button("Registrar Venta"):
    st.success(f"¡Venta registrada para {nombre_cliente} por ${monto}!")
