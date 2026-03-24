# ui/tasks.py
import streamlit as st
import datetime

def render_tasks(tasks_collection):
    # --- CABECERA Y CONTROLES DE FILTRO/ORDENAMIENTO ---
    col_titulo, col_filtro, col_orden = st.columns([0.4, 0.3, 0.3], vertical_alignment="center")
    
    with col_titulo:
        st.header("Mis Tareas")

    with col_filtro:
        opcion_filtro = st.selectbox(
            "Mostrar:", 
            ["Todas", "Pendientes", "Completadas"],
            label_visibility="collapsed"
        )
        
    with col_orden:
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
        
        /* Ajuste para que los botones de eliminar/editar dentro de la lista no hereden el estilo flotante */
        div[data-testid="stVerticalBlock"] div[data-testid="stPopover"],
        div[data-testid="stVerticalBlock"] div[data-testid="stPopover"] > button {
            position: static !important;
            width: auto !important;
            height: auto !important;
            min-width: 0 !important;
            min-height: 0 !important;
            border-radius: 8px !important;
            background-color: transparent !important;
            color: inherit !important;
            box-shadow: none !important;
            font-size: 1rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # --- BOTÓN FLOTANTE PARA NUEVA TAREA ---
    with st.popover("➕", help="Agregar nueva tarea"):
        st.markdown("### Nueva Tarea")
        with st.form("add_task_form", clear_on_submit=True):
            titulo = st.text_input("Título de la tarea", placeholder="Ej. Comprar pan")
            fecha_input = st.date_input("Fecha límite", datetime.date.today())
            prioridad = st.selectbox("Prioridad", ["alta", "media", "baja"], index=1)
            
            if st.form_submit_button("Guardar Tarea"):
                if titulo.strip():
                    nueva_tarea = {
                        "title": titulo.strip(),
                        "due_date": fecha_input.strftime('%Y-%m-%d'),
                        "priority": prioridad,
                        "completed": False
                    }
                    resultado = tasks_collection.insert_one(nueva_tarea)
                    if resultado.inserted_id:
                        if "daily_summary" in st.session_state:
                            del st.session_state["daily_summary"]
                        st.toast("¡Tarea agregada exitosamente!", icon="✅")
                        st.rerun()
                else:
                    st.error("El título de la tarea no puede estar vacío.")
    
    # --- CONSULTA, FILTRADO Y LÓGICA DE ORDENAMIENTO ---
    todas_las_tareas = list(tasks_collection.find())
    
    if opcion_filtro == "Pendientes":
        tareas = [t for t in todas_las_tareas if not t.get("completed", False)]
    elif opcion_filtro == "Completadas":
        tareas = [t for t in todas_las_tareas if t.get("completed", False)]
    else:
        tareas = todas_las_tareas
    
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
        st.info("No hay tareas para mostrar con los filtros actuales.")
    else:
        for t in tareas:
            # Convertimos el ID de mongo a string para usarlo en las keys de Streamlit
            tarea_id = str(t['_id'])
            is_done = t.get("completed", False)
            prioridad = t.get("priority", "media")
            
            if prioridad == "alta":
                prio_badge = "🔴 Alta"
            elif prioridad == "media":
                prio_badge = "🟡 Media"
            else:
                prio_badge = "🟢 Baja"

            with st.container(border=True):
                # Aumentamos el tamaño de col2 (0.65) para empujar el resto a la derecha.
                # Reducimos el ancho de col4 y col5 (0.07) para que los botones queden justos.
                col1, col2, col3, col4, col5 = st.columns([0.05, 0.65, 0.16, 0.07, 0.07], vertical_alignment="center")
                
                with col1:
                    changed = st.checkbox("", value=is_done, key=f"chk_{tarea_id}")
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
                    
                    fecha_tarea = t.get('due_date', '')
                    if fecha_tarea == today_str:
                        st.caption("📅 **Hoy**")
                    else:
                        st.caption(f"📅 {fecha_tarea}")
                        
                with col3:
                    st.markdown(f"<div style='text-align: right;'>{prio_badge}</div>", unsafe_allow_html=True)
                
                with col4:
                    # Botón de edición (despliega un formulario)
                    with st.popover("✏️", help="Editar tarea"):
                        st.markdown("**Editar Tarea**")
                        # ... (resto del código del formulario de edición intacto) ...
                        with st.form(f"edit_form_{tarea_id}"):
                            nuevo_titulo = st.text_input("Título", value=t.get("title", ""))
                            
                            try:
                                fecha_actual = datetime.datetime.strptime(t.get("due_date", ""), "%Y-%m-%d").date()
                            except ValueError:
                                fecha_actual = datetime.date.today()
                                
                            nueva_fecha = st.date_input("Fecha límite", value=fecha_actual)
                            
                            prioridades_lista = ["alta", "media", "baja"]
                            prio_actual = t.get("priority", "media")
                            idx_prio = prioridades_lista.index(prio_actual) if prio_actual in prioridades_lista else 1
                            
                            nueva_prioridad = st.selectbox("Prioridad", prioridades_lista, index=idx_prio)
                            
                            if st.form_submit_button("Guardar Cambios"):
                                if nuevo_titulo.strip():
                                    tasks_collection.update_one(
                                        {"_id": t["_id"]},
                                        {"$set": {
                                            "title": nuevo_titulo.strip(),
                                            "due_date": nueva_fecha.strftime("%Y-%m-%d"),
                                            "priority": nueva_prioridad
                                        }}
                                    )
                                    if "daily_summary" in st.session_state:
                                        del st.session_state["daily_summary"]
                                    st.toast("¡Tarea actualizada!", icon="🔄")
                                    st.rerun()
                                else:
                                    st.error("El título no puede estar vacío.")

                with col5:
                    # Botón de eliminar
                    if st.button("🗑️", key=f"del_{tarea_id}", help="Eliminar tarea"):
                        tasks_collection.delete_one({"_id": t["_id"]})
                        if "daily_summary" in st.session_state:
                            del st.session_state["daily_summary"]
                        st.toast("Tarea eliminada", icon="🗑️")
                        st.rerun()