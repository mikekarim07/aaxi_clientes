import streamlit as st
from supabase import create_client, Client

# --- Configuración base ---
st.set_page_config(page_title="Inicio - Ajuste Anual por Inflación", page_icon="📊")

url = st.secrets["url"]
key = st.secrets["key"]
supabase: Client = create_client(url, key)

# --- Manejo de sesión ---
if "user" not in st.session_state:
    st.session_state["user"] = None

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
    supabase.auth.sign_out()
    st.success("Sesión cerrada correctamente.")

# --- Interfaz ---
st.title("📊 Ajuste Anual por Inflación")
st.markdown("""
Bienvenido al sistema de cálculo del **Ajuste Anual por Inflación**.

Esta plataforma te permitirá:
- Subir las **balanzas de comprobación** de tus entidades legales.
- Visualizar los periodos cargados.
- Generar y consultar los resultados del cálculo de AAxI.

""")

# --- Si el usuario no está autenticado ---
if not st.session_state["user"]:
    st.subheader("🔐 Inicia sesión para continuar")

    with st.form("login_form"):
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Iniciar sesión")

        if submitted:
            if login(email, password):
                st.success("Inicio de sesión exitoso. Redirigiendo...")
                st.rerun()
else:
    user = st.session_state["user"]
    st.success(f"Sesión iniciada como: {user.email}")
    st.sidebar.button("Cerrar sesión", on_click=logout)
