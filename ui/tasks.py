# ui/tasks.py
import streamlit as st
import datetime

def render_tasks(tasks_collection):
    # --- CABECERA Y CONTROLES DE ORDENAMIENTO ---
    col_titulo, col_orden = st.columns([0.6, 0.4], vertical_alignment="center")
    
    with col_titulo:
        st.header("Mis Tareas")
        
    with col_orden:
        # Selector para ordenar las tareas
        opcion_orden = st.selectbox(
            "Ordenar por:", 
            [
                "📅 Fecha (Más próxima primero)", 
                "📅 Fecha (Más lejana primero)", 
                "🔥 Prioridad (Alta a Baja)", 
                "🧊 Prioridad (Baja a Alta)"
            ],
            label_visibility="collapsed"
        )
    
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    
    # --- ESTILOS CSS PARA LA BURBUJA FLOTANTE ---
    st.markdown(
        """
        <style>
        div[data-testid="stPopover"] {
            position: fixed !important;
            bottom: 40px !important;
            right: 40px !important;
            z-index: 9999 !important;
            width: auto !important;
        }
        div[data-testid="stPopover"] > button {
            border-radius: 50% !important;
            width: 65px !important;
            height: 65px !important;
            min-width: 65px !important;
            min-height: 65px !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 32px !important;
            line-height: 1 !important;
            background-color: #FF4B4B !important;
            color: white !important;
            border: none !important;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.3) !important;
            transition: transform 0.2s ease-in-out !important;
        }
        div[data-testid="stPopover"] > button:hover {
            transform: scale(1.08) !important;
            background-color: #FF6666 !important;
            color: white !important;
        }
        div[data-testid="stPopover"] > button:focus {
            border: none !important;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.4) !important;
            outline: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Botón flotante usando st.popover
    with st.popover("➕", help="Agregar nueva tarea"):
        st.markdown("### Nueva Tarea")
        with st.form("add_task_form", clear_on_submit=True):
            titulo = st.text_input("Título de la tarea", placeholder="Ej. Comprar pan")
            fecha = st.date_input("Fecha límite", datetime.date.today())
            prioridad = st.selectbox("Prioridad", ["alta", "media", "baja"], index=1)
            
            submitted = st.form_submit_button("Guardar Tarea")
            if submitted and titulo:
                tasks_collection.insert_one({
                    "title": titulo,
                    "due_date": fecha.strftime('%Y-%m-%d'),
                    "priority": prioridad,
                    "completed": False
                })
                st.toast("¡Tarea agregada exitosamente!", icon="✅")
                st.rerun() # Recargamos para que aparezca instantáneamente
    
    # --- CONSULTA Y LÓGICA DE ORDENAMIENTO ---
    # Obtenemos TODAS las tareas (ya no solo las de hoy) para poder ordenarlas por fecha
    tareas = list(tasks_collection.find())
    
    # Diccionario para darle valor numérico a la prioridad y poder ordenarla
    valor_prioridad = {"alta": 1, "media": 2, "baja": 3}
    
    if opcion_orden == "📅 Fecha (Más próxima primero)":
        tareas.sort(key=lambda x: (x.get("due_date", ""), valor_prioridad.get(x.get("priority"), 2)))
    elif opcion_orden == "📅 Fecha (Más lejana primero)":
        tareas.sort(key=lambda x: (x.get("due_date", ""), valor_prioridad.get(x.get("priority"), 2)), reverse=True)
    elif opcion_orden == "🔥 Prioridad (Alta a Baja)":
        tareas.sort(key=lambda x: (valor_prioridad.get(x.get("priority", "media"), 2), x.get("due_date", "")))
    elif opcion_orden == "🧊 Prioridad (Baja a Alta)":
        tareas.sort(key=lambda x: (valor_prioridad.get(x.get("priority", "media"), 2), x.get("due_date", "")), reverse=True)
    

    # --- RENDERIZADO DE TAREAS EN BLOQUES ---
    if not tareas:
        st.info("No hay tareas pendientes. Puedes agregar una con el botón ➕ o pidiéndoselo a Agenta en el chat.")
    else:
        for t in tareas:
            is_done = t.get("completed", False)
            prioridad = t.get("priority", "media")
            
            # Asignar un color/emoji según la prioridad
            if prioridad == "alta":
                prio_badge = "🔴 Alta"
            elif prioridad == "media":
                prio_badge = "🟡 Media"
            else:
                prio_badge = "🟢 Baja"

            # Creamos un bloque (tarjeta) con borde para cada tarea
            with st.container(border=True):
                # Dividimos el bloque en 3 columnas: Checkbox, Textos, Prioridad
                col1, col2, col3 = st.columns([0.05, 0.75, 0.2], vertical_alignment="center")
                
                with col1:
                    changed = st.checkbox("", value=is_done, key=f"chk_{t['_id']}")
                    if changed != is_done:
                        tasks_collection.update_one({"_id": t["_id"]}, {"$set": {"completed": changed}})
                        if "daily_summary" in st.session_state:
                            del st.session_state["daily_summary"]
                        st.rerun()
                        
                with col2:
                    if is_done:
                        st.markdown(f"~~**{t.get('title', 'Sin título')}**~~")
                    else:
                        st.markdown(f"**{t.get('title', 'Sin título')}**")
                    
                    # Mostrar la fecha en texto pequeño
                    fecha_tarea = t.get('due_date', '')
                    if fecha_tarea == today_str:
                        st.caption("📅 **Hoy**")
                    else:
                        st.caption(f"📅 {fecha_tarea}")
                        
                with col3:
                    # Mostramos la etiqueta de prioridad alineada a la derecha
                    st.markdown(f"<div style='text-align: right;'>{prio_badge}</div>", unsafe_allow_html=True)