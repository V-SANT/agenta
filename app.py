# app.py
import streamlit as st
import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1' 

from ui.home import render_home
from ui.chat import render_chat
from ui.tasks import render_tasks

load_dotenv()

# --- CONSTANTES DE GOOGLE ---
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid' 
]
REDIRECT_URI = 'http://localhost:8501'

@st.cache_resource
def get_database():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    return client["agenta_db"]

db = get_database()
tasks_collection = db["tasks"]

# --- 1. MANEJO DEL CALLBACK DE GOOGLE ---
if "code" in st.query_params:
    try:
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        # RECUPERAR EL CÓDIGO DE SEGURIDAD (PKCE VERIFIER)
        if os.path.exists('.oauth_verifier'):
            with open('.oauth_verifier', 'r') as f:
                flow.code_verifier = f.read()

        # Intercambiamos el código temporal por el token definitivo
        flow.fetch_token(code=st.query_params["code"])
        creds = flow.credentials
        
        # Guardamos el token para futuras sesiones
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
        # Limpiamos la URL, borramos el archivo temporal y recargamos
        st.query_params.clear()
        if os.path.exists('.oauth_verifier'):
            os.remove('.oauth_verifier')
            
        st.rerun()
    except Exception as e:
        st.error(f"Error al procesar la autorización de Google: {e}")
        st.query_params.clear() # Limpia la URL incluso si falla para no entrar en bucle

# --- 2. FUNCIÓN PARA OBTENER INFO DE GOOGLE ---
def get_google_user_info():
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json')
            if creds and creds.valid:
                response = requests.get(
                    "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
                    headers={"Authorization": f"Bearer {creds.token}"}
                )
                if response.status_code == 200:
                    return response.json()
        except Exception:
            return None
    return None

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(
    page_title="AGENTA", 
    page_icon="./resources/agenta_logo.png", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INICIALIZAR ESTADO DE NAVEGACIÓN ---
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = "🏠 Home"

# --- PANEL DE NAVEGACIÓN LATERAL (SIDEBAR) ---
with st.sidebar:
    col1, col_img, col3 = st.columns([1, 1.5, 1])
    with col_img:
        if os.path.exists("resources/agenta_logo.png"):
            st.image("resources/agenta_logo.png", use_container_width=True)
    
    st.markdown("<h1 style='text-align: center; margin-top: -40px;'>AGENTA</h1>", unsafe_allow_html=True)

    if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.pagina_actual == "🏠 Home" else "secondary"):
        st.session_state.pagina_actual = "🏠 Home"
        st.rerun()

    if st.button("💬 Chat", use_container_width=True, type="primary" if st.session_state.pagina_actual == "💬 Chat" else "secondary"):
        st.session_state.pagina_actual = "💬 Chat"
        st.rerun()

    if st.button("✅ Tareas", use_container_width=True, type="primary" if st.session_state.pagina_actual == "✅ Tareas" else "secondary"):
        st.session_state.pagina_actual = "✅ Tareas"
        st.rerun()

    # --- 3. LÓGICA DINÁMICA DE GOOGLE CALENDAR ---
    st.divider()
    
    if os.path.exists('token.json'):
        user_info = get_google_user_info()
        if user_info:
            with st.container(border=True):
                # Usamos columnas de espacio para centrar la imagen circularmente
                espacio_izq, col_foto, espacio_der = st.columns([1, 1.5, 1])
                with col_foto:
                    # Obtenemos datos
                    img_url = user_info.get("picture", "https://via.placeholder.com/150")
                    user_email = user_info.get("email", "")
                    
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: center; margin-top: 10px;">
                            <img src="{img_url}" title="{user_email}" referrerpolicy="no-referrer" style="width: 100%; border-radius: 50%; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                st.markdown(f"<h4 style='text-align: center; margin-top: 10px; margin-bottom: 10px;'>{user_info.get('name', 'Usuario')}</h4>", unsafe_allow_html=True)
                
                if st.button("Desconectar", use_container_width=True):
                    os.remove('token.json')
                    st.rerun()
        else:
            st.error("Error leyendo el perfil. El token caducó o es inválido.")
            if st.button("Desconectar y reintentar", use_container_width=True):
                os.remove('token.json')
                st.rerun()
    else:
        # Generamos el enlace de autorización web dinámicamente
        try:
            flow = Flow.from_client_secrets_file(
                'credentials.json',
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            # GUARDAR EL CÓDIGO DE SEGURIDAD (PKCE VERIFIER) ANTES DE IR A GOOGLE
            if hasattr(flow, 'code_verifier'):
                with open('.oauth_verifier', 'w') as f:
                    f.write(flow.code_verifier)
            
            # Inyectamos CSS específico para forzar el centrado del texto en el st.link_button
            st.markdown(
                """
                <style>
                div[data-testid="stLinkButton"] a {
                    text-align: center;
                    display: flex;
                    justify-content: center;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            st.link_button("Conectar con Google Calendar", auth_url, use_container_width=True)
        except Exception as e:
            st.error("No se pudo generar el enlace de inicio de sesión.")
            st.caption(f"Detalle: {e}")

# --- ÁREA DE CONTENIDO PRINCIPAL ---
if st.session_state.pagina_actual == "🏠 Home":
    render_home(tasks_collection)
elif st.session_state.pagina_actual == "💬 Chat":
    render_chat()
elif st.session_state.pagina_actual == "✅ Tareas":
    render_tasks(tasks_collection)