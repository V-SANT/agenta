# agent.py
# Agente de Asistente Personal construido con LangGraph + OpenAI + MCP

import os
import sys
import json
import asyncio
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv
from datetime import date, timedelta

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# Librerías cliente de MCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ─── CARGAR API KEY ───────────────────────────────────────────────────────────
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ No se encontró OPENAI_API_KEY.")

# ─── MODELO LLM ───────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model="gpt-4o-mini",       
    temperature=0.3,
    api_key=OPENAI_API_KEY,
)

# ─── FUNCIONES DE FECHA ───────────────────────────────────────────────────────
def get_today() -> str:
    return date.today().strftime("%Y-%m-%d")

def get_tomorrow() -> str:
    return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")


# ─── CLIENTE MCP ──────────────────────────────────────────────────────────────
async def fetch_from_mcp(target_date: str):
    """Se conecta al servidor MCP local para consumir las herramientas de datos."""
    # Usamos sys.executable para asegurarnos de usar el Python del entorno virtual (agenta)
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"],
        env=os.environ.copy()
    )
    
    # Abrimos la conexión síncrona por consola (stdio)
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # El agente ejecuta las herramientas del servidor
            events_result = await session.call_tool("get_events", arguments={"target_date": target_date})
            tasks_result = await session.call_tool("get_tasks", arguments={"status": "pending"})
            
            # FastMCP devuelve el contenido como texto JSON, lo parseamos de vuelta a diccionarios
            events = json.loads(events_result.content[0].text)
            tasks = json.loads(tasks_result.content[0].text)
            
            return events, tasks

# ─── ESTADO DEL GRAFO ─────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[List, add_messages]
    today: str
    tomorrow: str
    today_events: List[dict]
    today_tasks: List[dict]
    tomorrow_events: List[dict]
    tomorrow_tasks: List[dict]
    daily_summary: str
    preparation_tips: str
    user_query: str

# ─── NODOS DEL GRAFO ──────────────────────────────────────────────────────────

def load_calendar_node(state: AgentState) -> AgentState:
    """Carga los datos ejecutando el cliente MCP hacia nuestro servidor."""
    today = get_today()
    tomorrow = get_tomorrow()

    print("\n🔌 [Agente] Conectando al servidor MCP...")
    # Ejecutamos el cliente asíncrono desde nuestro nodo síncrono
    today_events, today_tasks = asyncio.run(fetch_from_mcp(today))
    tomorrow_events, tomorrow_tasks = asyncio.run(fetch_from_mcp(tomorrow))
    print("✅ [Agente] Datos obtenidos mediante MCP con éxito.")

    return {
        **state,
        "today": today,
        "tomorrow": tomorrow,
        "today_events": today_events,
        "today_tasks": today_tasks,
        "tomorrow_events": tomorrow_events,
        "tomorrow_tasks": tomorrow_tasks,
    }


def _format_events(events: List[dict]) -> str:
    if not events:
        return "  (sin eventos)"
    lines = []
    for e in events:
        time_str = f"a las {e.get('time')}" if e.get('time') else "todo el día"
        loc = f" | 📍 {e.get('location')}" if e.get('location') else ""
        prep = " ⚠️ [requiere preparación]" if e.get('requires_preparation') else ""
        lines.append(f"  • {time_str} — {e.get('title')}{loc}{prep}")
        if e.get('description'):
            lines.append(f"      └─ {e.get('description')}")
    return "\n".join(lines)


def _format_tasks(tasks: List[dict]) -> str:
    if not tasks:
        return "  (sin tareas pendientes)"
    priority_icon = {"alta": "🔴", "media": "🟡", "baja": "🟢"}
    lines = []
    for t in tasks:
        priority = t.get('priority', 'media')
        icon = priority_icon.get(priority, "⚪")
        lines.append(f"  {icon} [{priority.upper()}] {t.get('title')}")
        if t.get('notes'):
            lines.append(f"      └─ {t.get('notes')}")
    return "\n".join(lines)


def generate_daily_summary_node(state: AgentState) -> AgentState:
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
2. Lista de eventos de hoy con su contexto.
3. Lista de tareas urgentes de hoy.
4. Un vistazo rápido a lo que viene mañana.
5. Un consejo de productividad.
"""
    response = llm.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
    return {**state, "daily_summary": response.content}


def generate_preparation_tips_node(state: AgentState) -> AgentState:
    tomorrow_events_prep = [e for e in state['tomorrow_events'] if e.get('requires_preparation')]

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
estar listo mañana. Sé específico, práctico y breve. Usa formato de checklist con emojis.
"""
    response = llm.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
    return {**state, "preparation_tips": response.content}


def respond_to_user_node(state: AgentState) -> AgentState:
    if not state.get("user_query"):
        return state

    context = f"""
Eres un asistente personal. Tienes acceso al calendario del usuario.
RESUMEN DEL DÍA ({state['today']}): {state.get('daily_summary', '')}
PREPARATIVOS PARA MAÑANA ({state['tomorrow']}): {state.get('preparation_tips', '')}
Responde la pregunta del usuario de forma directa y útil.
"""
    response = llm.invoke([SystemMessage(content=context), HumanMessage(content=state["user_query"])])

    new_messages = list(state.get("messages", []))
    new_messages.append(HumanMessage(content=state["user_query"]))
    new_messages.append(AIMessage(content=response.content))

    return {**state, "messages": new_messages}


def should_respond_to_query(state: AgentState) -> str:
    if state.get("user_query"):
        return "respond"
    return "end"


# ─── CONSTRUCCIÓN DEL GRAFO ───────────────────────────────────────────────────
def build_agent() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("load_calendar", load_calendar_node)
    graph.add_node("generate_daily_summary", generate_daily_summary_node)
    graph.add_node("generate_preparation_tips", generate_preparation_tips_node)
    graph.add_node("respond_to_user", respond_to_user_node)

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

def run_assistant(user_query: str = "") -> dict:
    agent = build_agent()
    initial_state: AgentState = {
        "messages": [], "today": "", "tomorrow": "",
        "today_events": [], "today_tasks": [], "tomorrow_events": [], "tomorrow_tasks": [],
        "daily_summary": "", "preparation_tips": "", "user_query": user_query,
    }
    return agent.invoke(initial_state)

if __name__ == "__main__":
    print("🤖 Iniciando Asistente Personal con MCP...")
    result = run_assistant()
    print("\n📅 RESUMEN DEL DÍA\n" + "="*60 + f"\n{result['daily_summary']}")
    print("\n🗓️  PREPARATIVOS PARA MAÑANA\n" + "="*60 + f"\n{result['preparation_tips']}")