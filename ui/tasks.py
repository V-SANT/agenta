# ui/tasks.py
import streamlit as st
import datetime

def render_tasks(tasks_collection):
    st.header("Tareas Diarias")
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    
    # Botón + (Formulario desplegable para agregar tarea)
    with st.expander("➕ Agregar nueva tarea", expanded=False):
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
            # Muestra una notificación flotante
            st.toast("¡Tarea agregada exitosamente!", icon="✅")

    st.divider()
    
    # Consultar tareas del día
    tareas_hoy = list(tasks_collection.find({"due_date": today_str}))
    
    if not tareas_hoy:
        st.info(f"No hay tareas pendientes para hoy ({today_str}). Puedes agregar una con el botón  o pidiéndoselo a Agenta en el chat.")
    else:
        st.subheader(f"Tus tareas para hoy")
        for t in tareas_hoy:
            is_done = t.get("completed", False)
            col1, col2 = st.columns([0.05, 0.95])
            
            with col1:
                # Checkbox interactivo que actualiza MongoDB en tiempo real
                changed = st.checkbox("", value=is_done, key=f"chk_{t['_id']}")
                if changed != is_done:
                    tasks_collection.update_one({"_id": t["_id"]}, {"$set": {"completed": changed}})
                    # Forzamos actualizar el resumen en el home si completamos tareas
                    if "daily_summary" in st.session_state:
                        del st.session_state["daily_summary"]
                    st.rerun()
                    
            with col2:
                # Tachado si está completada
                if is_done:
                    st.markdown(f"~~{t.get('title', 'Sin título')}~~ *(Completada)*")
                else:
                    st.markdown(f"**{t.get('title', 'Sin título')}** (Prioridad: {t.get('priority', 'media')})")