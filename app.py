import streamlit as st
from agent import run_assistant

# Configuración básica de la página
st.set_page_config(page_title="Agenta", page_icon="🤖", layout="wide")

st.title("Agenta - Tu Asistente Personal para la Agenda Diaria")

# Inicializar el estado de la sesión
if "messages" not in st.session_state:
    st.session_state.messages = []
    
    # Ejecutar el agente por primera vez sin query para obtener el resumen del día
    with st.spinner("Cargando tu agenda y preparando el día..."):
        initial_data = run_assistant()
        st.session_state.summary = initial_data.get("daily_summary", "")
        st.session_state.tips = initial_data.get("preparation_tips", "")

# --- BARRA LATERAL (Resúmenes) ---
with st.sidebar:
    st.header("📅 Resumen del Día")
    st.write(st.session_state.summary)
    
    st.divider()
    
    st.header("🗓️ Preparativos para Mañana")
    st.write(st.session_state.tips)

# --- INTERFAZ DE CHAT PRINCIPAL ---
# Mostrar el historial visual de los mensajes
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input de texto para el usuario en la parte inferior
if prompt := st.chat_input("¿Tienes alguna pregunta sobre tu agenda?"):
    
    # Guardar y mostrar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Llamar al agente con la consulta
    with st.spinner("Pensando..."):
        # Se invoca la función run_assistant pasándole la consulta del usuario
        response_data = run_assistant(user_query=prompt)
        
        # El agente guarda los mensajes en la lista 'messages' de su estado
        if response_data.get("messages"):
            ai_response = response_data["messages"][-1].content
        else:
            ai_response = "Lo siento, hubo un problema al generar la respuesta."

    # Guardar y mostrar la respuesta de la IA
    with st.chat_message("assistant"):
        st.markdown(ai_response)
    st.session_state.messages.append({"role": "assistant", "content": ai_response})