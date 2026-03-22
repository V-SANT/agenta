# ui/chat.py
import streamlit as st
import datetime
from agent import run_assistant

def render_chat():
    today_str = datetime.date.today().isoformat()
    if "chat_date" not in st.session_state or st.session_state.chat_date != today_str:
        st.session_state.chat_date = today_str
        st.session_state.messages = [] 

    # Renderizar historial de mensajes
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input del usuario
    if prompt := st.chat_input("Agrega una tarea, consulta tu agenda o charla con Agenta..."):
        # Guardar y mostrar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Consultar al Sistema Multi-Agente
        with st.chat_message("assistant"):
            with st.spinner("Agenta está pensando..."):
                respuesta = run_assistant(prompt)
                st.markdown(respuesta)
        st.session_state.messages.append({"role": "assistant", "content": respuesta})