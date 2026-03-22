# ui/home.py
import streamlit as st
import datetime
from agent import run_assistant

def render_home(tasks_collection):
    today_str = datetime.date.today().strftime('%Y-%m-%d')

    st.header(f"Resumen Diario - {today_str}")
    
    # 1. Verificar si hay tareas o eventos para hoy
    tareas_hoy = list(tasks_collection.find({"due_date": today_str}))
    
    print(f"Tareas para hoy: {tareas_hoy}") 

    if not tareas_hoy:
        # Mensaje por defecto si no hay nada en la agenda
        st.info("¡Día libre! No tienes tareas ni eventos programados para hoy. Puedes agregar nuevos desde el chat, en la sección de Tareas o en el Calendario.")
        return

    # 2. Sistema de Caché (simula localStorage)
    # Verificamos si ya hay un resumen generado hoy en el session_state
    if "daily_summary" not in st.session_state or st.session_state.get("summary_date") != today_str:
        with st.spinner("Generando tu resumen diario automáticamente con IA..."):
            prompt = "Genera un resumen detallado de hoy. Incluye mis eventos del calendario, mis tareas pendientes de la base de datos y un checklist de preparativos para mañana."
            respuesta = run_assistant(prompt)
            
            # Guardamos en caché
            st.session_state.daily_summary = respuesta
            st.session_state.summary_date = today_str

    # 3. Mostrar el resumen guardado
    st.markdown(st.session_state.daily_summary)
    
    if st.button("🔄 Forzar actualización del resumen"):
        del st.session_state["daily_summary"]
        st.rerun()