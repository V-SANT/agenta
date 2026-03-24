# ui/home.py
import streamlit as st
import datetime
from agent import run_assistant

def render_home(tasks_collection):
    today_str = datetime.date.today().strftime('%Y/%m/%d')

    # --- CABECERA Y BOTÓN EN COLUMNAS ---
    # Dividimos el espacio: 85% para el título, 15% para el botón. 
    # vertical_alignment="center" asegura que queden a la misma altura.
    col_titulo, col_boton = st.columns([0.85, 0.15], vertical_alignment="center")
    
    with col_titulo:
        st.header(f"Resumen Diario - {today_str}")
        
    with col_boton:
        # El botón ahora vive aquí arriba, junto al título
        if st.button("🔄", help="Forzar actualización del resumen"):
            if "daily_summary" in st.session_state:
                del st.session_state["daily_summary"]
            st.rerun()

    st.divider() # Una línea separadora para que quede más prolijo

    # 1. Verificar si hay tareas o eventos para hoy
    tareas_hoy = list(tasks_collection.find({"due_date": today_str}))

    if not tareas_hoy:
        st.info("¡Día libre! No tienes tareas ni eventos programados para hoy. Puedes agregar nuevos desde el chat, en la sección de Tareas o en el Calendario.")

    # 2. Sistema de Caché
    if "daily_summary" not in st.session_state or st.session_state.get("summary_date") != today_str:
        if tareas_hoy: # Solo generamos si hay contenido
            with st.spinner("Generando tu resumen diario automáticamente con IA..."):
                prompt = "Genera un resumen detallado de hoy. Incluye mis eventos del calendario, mis tareas pendientes de la base de datos y un checklist de preparativos para mañana."
                respuesta = run_assistant(prompt)
                
                # Guardamos en caché
                st.session_state.daily_summary = respuesta
                st.session_state.summary_date = today_str
        else:
             st.session_state.daily_summary = ""

    # 3. Mostrar el resumen guardado
    if st.session_state.get("daily_summary"):
        st.markdown(st.session_state.daily_summary)