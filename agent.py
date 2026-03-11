# agent.py
# Agente de Asistente Personal construido con LangGraph + OpenAI

import os
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from calendar_data import (
    get_events_for_date,
    get_tasks_for_date,
    get_today,
    get_tomorrow,
    CalendarEvent,
    Task,
)

# ─── CARGAR API KEY ───────────────────────────────────────────────────────────
# La API key se lee desde el archivo .env (variable OPENAI_API_KEY)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "❌ No se encontró OPENAI_API_KEY. "
        "Crea un archivo .env con: OPENAI_API_KEY=sk-tu-clave-aqui"
    )

# ─── MODELO LLM ───────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model="gpt-4o-mini",       
    temperature=0.3,
    api_key=OPENAI_API_KEY,
)


# ─── ESTADO DEL GRAFO ─────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    today: str
    tomorrow: str
    today_events: List[CalendarEvent]
    today_tasks: List[Task]
    tomorrow_events: List[CalendarEvent]
    tomorrow_tasks: List[Task]
    daily_summary: str
    preparation_tips: str
    user_query: str


# ─── NODOS DEL GRAFO ──────────────────────────────────────────────────────────

def load_calendar_node(state: AgentState) -> AgentState:
    """Carga los eventos y tareas del día de hoy y mañana."""
    today = get_today()
    tomorrow = get_tomorrow()

    return {
        **state,
        "today": today,
        "tomorrow": tomorrow,
        "today_events": get_events_for_date(today),
        "today_tasks": get_tasks_for_date(today),
        "tomorrow_events": get_events_for_date(tomorrow),
        "tomorrow_tasks": get_tasks_for_date(tomorrow),
    }


def _format_events(events: List[CalendarEvent]) -> str:
    if not events:
        return "  (sin eventos)"
    lines = []
    for e in events:
        time_str = f"a las {e.time}" if e.time else "todo el día"
        loc = f" | 📍 {e.location}" if e.location else ""
        prep = " ⚠️ [requiere preparación]" if e.requires_preparation else ""
        lines.append(f"  • {time_str} — {e.title}{loc}{prep}")
        if e.description:
            lines.append(f"      └─ {e.description}")
    return "\n".join(lines)


def _format_tasks(tasks: List[Task]) -> str:
    if not tasks:
        return "  (sin tareas pendientes)"
    priority_icon = {"alta": "🔴", "media": "🟡", "baja": "🟢"}
    lines = []
    for t in tasks:
        icon = priority_icon.get(t.priority, "⚪")
        lines.append(f"  {icon} [{t.priority.upper()}] {t.title}")
        if t.notes:
            lines.append(f"      └─ {t.notes}")
    return "\n".join(lines)


def generate_daily_summary_node(state: AgentState) -> AgentState:
    """Genera el resumen del día usando el LLM."""
    context = f"""
Eres un asistente personal inteligente y organizado. Tu tarea es generar un 
resumen claro, motivador y accionable del día para el usuario.

=== FECHA DE HOY: {state['today']} ===

EVENTOS DE HOY:
{_format_events(state['today_events'])}

TAREAS PENDIENTES HOY:
{_format_tasks(state['today_tasks'])}

=== MAÑANA: {state['tomorrow']} ===

EVENTOS DE MAÑANA:
{_format_events(state['tomorrow_events'])}

TAREAS PENDIENTES MAÑANA:
{_format_tasks(state['tomorrow_tasks'])}
"""

    prompt = """
Genera un resumen del día de hoy con:
1. Un saludo breve y motivador.
2. Lista de eventos de hoy con su contexto (qué hacer en cada uno).
3. Lista de tareas urgentes de hoy, ordenadas por prioridad.
4. Un vistazo rápido a lo que viene mañana.
5. Un consejo de productividad relevante al día.
6. Una frase de motivadora de una persona famosa relacionada con la productividad o el éxito.

Usa un tono amable, claro y profesional. Usa emojis con moderación.
"""

    response = llm.invoke([
        SystemMessage(content=context),
        HumanMessage(content=prompt),
    ])

    return {**state, "daily_summary": response.content}


def generate_preparation_tips_node(state: AgentState) -> AgentState:
    """Genera consejos de preparación para el día siguiente usando el LLM."""
    tomorrow_events_prep = [e for e in state['tomorrow_events'] if e.requires_preparation]

    if not tomorrow_events_prep and not state['tomorrow_tasks']:
        tips = "✅ Mañana parece un día tranquilo. ¡Aprovecha para avanzar en proyectos de largo plazo!"
        return {**state, "preparation_tips": tips}

    context = f"""
Eres un asistente personal. Ayuda al usuario a prepararse para mañana ({state['tomorrow']}).

EVENTOS DE MAÑANA QUE REQUIEREN PREPARACIÓN:
{_format_events(tomorrow_events_prep)}

TAREAS DE MAÑANA:
{_format_tasks(state['tomorrow_tasks'])}
"""

    prompt = """
Genera una lista concreta de preparativos que el usuario puede hacer HOY para 
estar listo mañana. Incluye:
- Qué materiales/documentos preparar
- Qué revisar o estudiar
- Acciones logísticas (confirmar ubicaciones, preparar ropa, etc.)
- Tiempo estimado para cada preparativo

Sé específico, práctico y breve. Usa formato de checklist con emojis.
"""

    response = llm.invoke([
        SystemMessage(content=context),
        HumanMessage(content=prompt),
    ])

    return {**state, "preparation_tips": response.content}


def respond_to_user_node(state: AgentState) -> AgentState:
    """Responde preguntas específicas del usuario sobre su agenda."""
    if not state.get("user_query"):
        return state

    context = f"""
Eres un asistente personal. Tienes acceso al calendario del usuario.

RESUMEN DEL DÍA ({state['today']}):
{state.get('daily_summary', '')}

PREPARATIVOS PARA MAÑANA ({state['tomorrow']}):
{state.get('preparation_tips', '')}

Responde la pregunta del usuario de forma directa y útil.
"""

    response = llm.invoke([
        SystemMessage(content=context),
        HumanMessage(content=state["user_query"]),
    ])

    new_messages = list(state.get("messages", []))
    new_messages.append(HumanMessage(content=state["user_query"]))
    new_messages.append(AIMessage(content=response.content))

    return {**state, "messages": new_messages}


def should_respond_to_query(state: AgentState) -> str:
    """Decide si hay una consulta del usuario para responder."""
    if state.get("user_query"):
        return "respond"
    return "end"


# ─── CONSTRUCCIÓN DEL GRAFO ───────────────────────────────────────────────────

def build_agent() -> StateGraph:
    graph = StateGraph(AgentState)

    # Agregar nodos
    graph.add_node("load_calendar", load_calendar_node)
    graph.add_node("generate_daily_summary", generate_daily_summary_node)
    graph.add_node("generate_preparation_tips", generate_preparation_tips_node)
    graph.add_node("respond_to_user", respond_to_user_node)

    # Definir flujo
    graph.set_entry_point("load_calendar")
    graph.add_edge("load_calendar", "generate_daily_summary")
    graph.add_edge("generate_daily_summary", "generate_preparation_tips")
    graph.add_conditional_edges(
        "generate_preparation_tips",
        should_respond_to_query,
        {"respond": "respond_to_user", "end": END},
    )
    graph.add_edge("respond_to_user", END)

    return graph.compile()


# ─── FUNCIÓN PRINCIPAL ────────────────────────────────────────────────────────

def run_assistant(user_query: str = "") -> dict:
    """
    Ejecuta el agente asistente personal.
    
    Args:
        user_query: Pregunta opcional del usuario sobre su agenda.
    
    Returns:
        Estado final con resumen y preparativos.
    """
    agent = build_agent()

    initial_state: AgentState = {
        "messages": [],
        "today": "",
        "tomorrow": "",
        "today_events": [],
        "today_tasks": [],
        "tomorrow_events": [],
        "tomorrow_tasks": [],
        "daily_summary": "",
        "preparation_tips": "",
        "user_query": user_query,
    }

    result = agent.invoke(initial_state)
    return result


# ─── EJECUCIÓN DIRECTA ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🤖 Iniciando Asistente Personal...\n")
    print("=" * 60)

    # Ejecución automática: resumen del día + preparativos
    result = run_assistant()

    print("📅 RESUMEN DEL DÍA")
    print("=" * 60)
    print(result["daily_summary"])

    print("\n" + "=" * 60)
    print("🗓️  PREPARATIVOS PARA MAÑANA")
    print("=" * 60)
    print(result["preparation_tips"])

    # Modo conversacional: el usuario puede hacer preguntas
    print("\n" + "=" * 60)
    print("💬 MODO CONVERSACIONAL (escribe 'salir' para terminar)")
    print("=" * 60)

    while True:
        query = input("\n¿Tienes alguna pregunta sobre tu agenda? > ").strip()
        if query.lower() in ("salir", "exit", "quit", ""):
            print("👋 ¡Hasta luego! Que tengas un excelente día.")
            break

        response = run_assistant(user_query=query)
        if response.get("messages"):
            last_message = response["messages"][-1]
            print(f"\n🤖 {last_message.content}")