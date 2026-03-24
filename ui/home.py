# ui/home.py
import streamlit as st
import datetime
import asyncio
from agent import run_assistant, call_mcp_tool

def render_home(tasks_collection):
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    today_title = datetime.date.today().strftime('%Y/%m/%d')

    # --- CABECERA Y BOTÓN EN COLUMNAS ---
    # Dividimos el espacio: 85% para el título, 15% para el botón. 
    col_titulo, col_boton = st.columns([0.85, 0.15], vertical_alignment="center")
    
    with col_titulo:
        st.header(f"Resumen Diario - {today_title}")
        
    with col_boton:
        # El botón ahora vive aquí arriba, junto al título
        if st.button("🔄", help="Forzar actualización del resumen"):
            if "daily_summary" in st.session_state:
                del st.session_state["daily_summary"]
            st.rerun()

    st.divider() # Una línea separadora para que quede más prolijo

    # 1. Verificar si hay tareas para hoy en MongoDB
    tareas_hoy = list(tasks_collection.find({"due_date": today_str}))

    # 2. Verificar si hay eventos para hoy usando MCP directamente (sin gastar IA)
    try:
        eventos_hoy = asyncio.run(call_mcp_tool("get_events", {"target_date": today_str}))
        # call_mcp_tool intenta devolver un JSON parseado (lista). 
        # Evaluamos si es una lista con elementos o un texto válido.
        if isinstance(eventos_hoy, list):
            hay_eventos = len(eventos_hoy) > 0
        else:
            hay_eventos = bool(eventos_hoy and str(eventos_hoy).strip() not in ["", "[]"])
    except Exception:
        # En caso de error de conexión, asumimos False para que no se rompa la app
        hay_eventos = False

    # 3. Mostrar el mensaje SOLO si no hay ni tareas ni eventos
    if not tareas_hoy and not hay_eventos:
        st.info("¡Día libre! No tienes tareas ni eventos programados para hoy. Puedes agregar nuevos desde el Chat o en la sección de Tareas.")

    # 4. Sistema de Caché y Generación con IA
    if "daily_summary" not in st.session_state or st.session_state.get("summary_date") != today_str:
        # Ahora generamos el resumen si hay tareas O si hay eventos
        if tareas_hoy or hay_eventos: 
            with st.spinner("Generando tu resumen diario automáticamente con IA..."):
                prompt = "Genera un resumen detallado de hoy. Incluye mis eventos del calendario, mis tareas pendientes de la base de datos y un checklist de preparativos para mañana."
                respuesta = run_assistant(prompt)
                
                # Guardamos en caché
                st.session_state.daily_summary = respuesta
                st.session_state.summary_date = today_str
        else:
             st.session_state.daily_summary = ""

    # 5. Mostrar el resumen guardado
    if st.session_state.get("daily_summary"):
        st.markdown(st.session_state.daily_summary)