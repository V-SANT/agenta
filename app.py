# app.py
import streamlit as st
import os
from pymongo import MongoClient
from dotenv import load_dotenv

from ui.home import render_home
from ui.chat import render_chat
from ui.tasks import render_tasks

load_dotenv()

@st.cache_resource
def get_database():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    return client["agenta_db"]

db = get_database()
tasks_collection = db["tasks"]

# Configuración inicial de la página
st.set_page_config(
    page_title="AGENTA", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INICIALIZAR ESTADO DE NAVEGACIÓN ---
# Si es la primera vez que entramos, establecemos el Home por defecto
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = "🏠 Home"

# --- PANEL DE NAVEGACIÓN LATERAL (SIDEBAR) ---
with st.sidebar:
    # 1. Centramos el logo usando columnas (dejamos espacio vacío a los lados)
    col1, col_img, col3 = st.columns([1, 1.5, 1])
    with col_img:
        # Verifica que exista para no lanzar un error feo si mueves la carpeta
        if os.path.exists("resources/agenta_logo.png"):
            st.image("resources/agenta_logo.png", use_container_width=True)
    
    # 2. Centramos el título usando HTML
    st.markdown("<h1 style='text-align: center; margin-top: -40px;'>AGENTA</h1>", unsafe_allow_html=True)

    # Creamos botones de ancho completo. 
    # Si el botón coincide con la página actual, se pinta de color ("primary").
    if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.pagina_actual == "🏠 Home" else "secondary"):
        st.session_state.pagina_actual = "🏠 Home"
        st.rerun() # Fuerza a recargar para actualizar los colores inmediatamente

    if st.button("💬 Chat", use_container_width=True, type="primary" if st.session_state.pagina_actual == "💬 Chat" else "secondary"):
        st.session_state.pagina_actual = "💬 Chat"
        st.rerun()

    if st.button("✅ Tareas", use_container_width=True, type="primary" if st.session_state.pagina_actual == "✅ Tareas" else "secondary"):
        st.session_state.pagina_actual = "✅ Tareas"
        st.rerun()

# --- ÁREA DE CONTENIDO PRINCIPAL ---
# Renderizamos la vista correspondiente según el estado guardado
if st.session_state.pagina_actual == "🏠 Home":
    render_home(tasks_collection)

elif st.session_state.pagina_actual == "💬 Chat":
    render_chat()

elif st.session_state.pagina_actual == "✅ Tareas":
    render_tasks(tasks_collection)