import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- Configuración inicial ---
st.set_page_config(page_title="Carga de Balanzas", page_icon="📊")

url = st.secrets["url"]
key = st.secrets["key"]
supabase: Client = create_client(url, key)

# --- Manejo de sesión ---
if "user" not in st.session_state:
    st.session_state["user"] = None

# --- Función para iniciar sesión ---
def login(email, password):
    try:
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state["user"] = result.user
        st.session_state["access_token"] = result.session.access_token
        return True
    except Exception as e:
        st.error("Error al iniciar sesión. Verifica tus credenciales.")
        st.write(e)
        return False

# --- Función para cerrar sesión ---
def logout():
    st.session_state["user"] = None
    supabase.auth.sign_out()
    st.success("Sesión cerrada correctamente.")

# --- Si no hay usuario autenticado, mostrar login ---
if not st.session_state["user"]:
    st.title("🔐 Iniciar sesión")
    email = st.text_input("Correo electrónico")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión"):
        if login(email, password):
            st.rerun()
else:
    # --- Usuario autenticado ---
    user = st.session_state["user"]
    st.sidebar.success(f"Usuario: {user.email}")

    # --- Botón de logout ---
    if st.sidebar.button("Cerrar sesión"):
        logout()
        st.rerun()

    # --- Obtener metadatos del usuario (cliente_id, rol, etc.) ---
    user_metadata = user.user_metadata
    cliente_id = user_metadata.get("cliente_id")
    rol = user_metadata.get("rol", "usuario")

    st.title("📊 Carga de Balanzas Contables")
    st.info(f"Bienvenido {user.email} — Rol: {rol}")

    # --- Subir archivo ---
    uploaded_file = st.file_uploader("Selecciona tu archivo CSV", type=["csv"])
    if uploaded_file is not None:
        st.success(f"Archivo seleccionado: {uploaded_file.name}")
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())

        if st.button("🚀 Subir archivo y registrar metadata"):
            periodo = datetime.now().strftime("%Y-%m")
            filename = f"balanza_{cliente_id}_{periodo}.csv"

            res = supabase.storage.from_("balanzas").upload(filename, uploaded_file.getvalue(), {"content-type": "text/csv"})
            if res:
                # Insertar metadata
                metadata = {
                    "cliente_id": cliente_id,
                    "periodo": periodo,
                    "filename": filename,
                    "storage_path": filename,
                    "usuario_carga": user.id,
                    "fecha_carga": datetime.now().isoformat(),
                    "entidades_legales": [],
                    "activo": True
                }
                result = supabase.table("balanzas_metadata").insert(metadata).execute()
                if result.data:
                    st.success("✅ Archivo subido y metadata registrada correctamente.")
                    st.write(result.data)
                else:
                    st.error("❌ Error al registrar metadata.")
            else:
                st.error("❌ Error al subir archivo al bucket.")
