import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import io
import pandas as pd

# Inicializar conexión con Supabase
url = st.secrets["url"]
key = st.secrets["key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Carga de Archivos", page_icon="📤")

# Verificar autenticación
if "user" not in st.session_state:
    st.warning("Por favor inicia sesión desde la página de inicio.")
    st.stop()

st.title("📤 Carga de Archivos")
st.write("Sube el archivo de balanza correspondiente al cliente.")

# Mostrar email del usuario actual
user_email = st.session_state["user"]["email"]
st.info(f"Usuario autenticado: {user_email}")

# Selección del año (carpeta dentro del bucket)
año = st.selectbox("Selecciona el año", [2023, 2024, 2025])

# Subir archivo
uploaded_file = st.file_uploader("Selecciona el archivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Leer CSV para verificar estructura
        df = pd.read_csv(uploaded_file)
        expected_columns = [
            "CompanyCode", "Mes", "Año", "NumeroCuenta", "Descripcion",
            "SaldoInicial", "Cargo", "Abono", "SaldoFinal", "FechaData"
        ]
        
        if not all(col in df.columns for col in expected_columns):
            st.error("❌ El archivo no tiene las columnas esperadas.")
        else:
            st.success("✅ Estructura verificada correctamente.")
            
            # Mostrar vista previa
            st.dataframe(df.head())

            # Botón para subir
            if st.button("Guardar archivo en Supabase"):
                # Leer contenido en bytes
                file_bytes = uploaded_file.getvalue()
                file_name = f"{user_email}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                storage_path = f"{año}/{file_name}"

                # Subir al bucket
                supabase.storage.from_("balanzas").upload(storage_path, file_bytes)

                # Insertar metadata
                fecha_data = df["FechaData"].max()  # última fecha en el archivo
                supabase.table("balanzas_metadata").insert({
                    "cliente_email": user_email,
                    "file_name": file_name,
                    "year": año,
                    "upload_timestamp": datetime.now().isoformat(),
                    "fecha_data": fecha_data
                }).execute()

                st.success("🎉 Archivo cargado y metadata registrada exitosamente.")
                st.info(f"Ruta del archivo: `{storage_path}`")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
