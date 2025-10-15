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

# --- Inicializar sesión ---
if "user" not in st.session_state:
    st.session_state["user"] = None
if "access_token" not in st.session_state:
    st.session_state["access_token"] = None

# --- Función de login segura ---
def login(email, password):
    try:
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if result.user is None:
            st.error("Error al iniciar sesión. Verifica tus credenciales.")
            return False
        st.session_state["user"] = result.user
        st.session_state["access_token"] = result.session.access_token
        return True
    except Exception as e:
        if "Invalid login credentials" in str(e):
            st.error("Error al iniciar sesión. Verifica tus credenciales.")
        else:
            st.error("Ocurrió un error inesperado al iniciar sesión.")
        return False

# --- Función de logout ---
def logout():
    st.session_state["user"] = None
    st.session_state["access_token"] = None
    supabase.auth.sign_out()
    st.success("Sesión cerrada correctamente.")
    st.experimental_rerun()  # recarga la página para mostrar login

# --- Si el usuario no está autenticado ---
if not st.session_state["user"]:
    st.subheader("🔐 Inicia sesión para continuar")

    with st.form("login_form"):
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar sesión")

        if submitted:
            if login(email, password):
                st.success("Inicio de sesión exitoso. Puedes continuar con la carga de archivos.")
                st.experimental_rerun()  # recarga para mostrar contenido de la página
else:
    # --- Usuario autenticado ---
    user = st.session_state["user"]
    st.success(f"Sesión iniciada como: {user.email}")

    # Botón de cerrar sesión
    st.sidebar.button("🔒 Cerrar sesión", on_click=logout)

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
                    file_name = f"{user.email}_{timestamp}.csv"
                    storage_path = f"{año}/{file_name}"

                    # Subir al bucket 'balanzas'
                    upload_res = supabase.storage.from_("balanzas").upload(storage_path, file_bytes, {"content-type": "text/csv"})
                    if upload_res:
                        # Insertar metadata
                        fecha_data = df["FechaData"].max()
                        supabase.table("balanzas_metadata").insert({
                            "cliente_email": user.email,
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
