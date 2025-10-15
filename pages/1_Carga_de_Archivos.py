import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

# --- Configuración de página ---
st.set_page_config(page_title="Carga de Archivos", page_icon="📤")

# --- Conexión a Supabase ---
url = st.secrets["url"]
key = st.secrets["key"]
supabase: Client = create_client(url, key)

# --- Inicializar flags en session_state ---
if "go_to_inicio" not in st.session_state:
    st.session_state["go_to_inicio"] = False

# --- Manejo de redirección a Inicio ---
if st.session_state.get("go_to_inicio"):
    st.session_state["go_to_inicio"] = False
    st.stop()  # Detiene la ejecución para que Inicio.py se muestre

# --- Verificar autenticación ---
user = st.session_state.get("user", None)

if not user:
    st.warning("🔒 Por favor inicia sesión desde la página de inicio para continuar.")

    if st.button("⬅️ Ir a Inicio"):
        st.session_state["user"] = None
        st.session_state["go_to_inicio"] = True
    st.stop()

# --- Botón Cerrar sesión ---
if st.button("🔒 Cerrar sesión"):
    st.session_state["user"] = None
    st.session_state["go_to_inicio"] = True
    st.stop()  # Detiene ejecución para que Inicio.py se muestre

# --- Obtener email del usuario ---
if hasattr(user, "email"):
    user_email = user.email
elif isinstance(user, dict):
    user_email = user.get("email")
else:
    st.error("❌ No se pudo obtener el email del usuario.")
    st.stop()

st.info(f"Usuario autenticado: {user_email}")

# --- Interfaz de carga ---
st.title("📤 Carga de Archivos de Balanzas")
st.write("Sube tu archivo CSV con la balanza consolidada del cliente.")

# Selección del año
año = st.selectbox("Selecciona el año", [2023, 2024, 2025])

# Subir archivo CSV
uploaded_file = st.file_uploader("Selecciona el archivo CSV", type=["csv"])

if uploaded_file is not None:
    try:
        # Leer CSV
        df = pd.read_csv(uploaded_file)
        expected_columns = [
            "CompanyCode", "Mes", "Año", "NumeroCuenta", "Descripcion",
            "SaldoInicial", "Cargo", "Abono", "SaldoFinal", "FechaData"
        ]

        # Validar columnas
        if not all(col in df.columns for col in expected_columns):
            st.error("❌ El archivo no tiene las columnas esperadas.")
        else:
            st.success("✅ Estructura del archivo verificada correctamente.")
            st.dataframe(df.head())

            # Botón para guardar archivo
            if st.button("Guardar archivo en Supabase"):
                file_bytes = uploaded_file.getvalue()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{user_email}_{timestamp}.csv"
                storage_path = f"{año}/{file_name}"

                # Subir al bucket 'balanzas'
                upload_res = supabase.storage.from_("balanzas").upload(storage_path, file_bytes, {"content-type": "text/csv"})
                if upload_res:
                    # Insertar metadata
                    fecha_data = df["FechaData"].max()
                    supabase.table("balanzas_metadata").insert({
                        "cliente_email": user_email,
                        "file_name": file_name,
                        "year": año,
                        "upload_timestamp": datetime.now().isoformat(),
                        "fecha_data": fecha_data,
                        "storage_path": storage_path,
                        "activo": True
                    }).execute()

                    st.success("🎉 Archivo cargado y metadata registrada exitosamente.")
                    st.info(f"Ruta del archivo en Supabase: `{storage_path}`")
                else:
                    st.error("❌ Error al subir el archivo al bucket.")
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
