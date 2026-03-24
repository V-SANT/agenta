import os
import sys
import json
import asyncio
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
import datetime

# LangChain y LangGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

# Cliente MCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ─── 1. CONFIGURACIÓN DEL LLM ────────────────────────────────────────────────
load_dotenv()
# Usamos un LLM con temperatura 0 para que sea preciso al tomar decisiones
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# ─── 2. PUENTE ENTRE LANGCHAIN Y MCP ─────────────────────────────────────────
async def call_mcp_tool(tool_name: str, arguments: dict):
    """Función maestra que levanta el cliente MCP de forma invisible y ejecuta una herramienta."""
    server_params = StdioServerParameters(command=sys.executable, args=["mcp_server.py"], env=os.environ.copy())
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            res = await session.call_tool(tool_name, arguments=arguments)
            
            if not res.content:
                return "[]"

            text_response = res.content[0].text
            
            # Intentamos parsearlo como JSON (para listas de tareas o eventos)
            try:
                return json.loads(text_response)
            # Si es texto normal (como el mensaje de éxito de add_task), lo devolvemos tal cual
            except json.JSONDecodeError:
                return text_response

# ─── 3. CREACIÓN DE LAS HERRAMIENTAS (TOOLS) PARA LOS AGENTES ────────────────
@tool
def add_task_tool(title: str, priority: str = "media", due_date: str = "") -> str:
    """Guarda una nueva tarea en la base de datos MongoDB."""
    return asyncio.run(call_mcp_tool("add_task", {"title": title, "priority": priority, "due_date": due_date}))

@tool
def get_tasks_tool(status: str = "pending") -> str:
    """Obtiene la lista de tareas pendientes desde MongoDB."""
    return str(asyncio.run(call_mcp_tool("get_tasks", {"status": status})))

@tool
def complete_task_tool(task_id: str) -> str:
    """Marca una tarea como completada en MongoDB usando su ID."""
    return asyncio.run(call_mcp_tool("complete_task", {"task_id": task_id}))

@tool
def get_events_tool(target_date: str) -> str:
    """Obtiene eventos del calendario. (Ej formato: YYYY-MM-DD)."""
    return str(asyncio.run(call_mcp_tool("get_events", {"target_date": target_date})))


# ─── 4. ESTADO GLOBAL DEL ECOSISTEMA A2A ─────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages] # Guarda el historial del chat
    next_agent: str                         # Guarda quién es el siguiente en actuar

# ─── 5. CREACIÓN DE LOS AGENTES ESPECIALIZADOS (WORKERS) ─────────────────────
# Usamos create_react_agent que les da la capacidad de pensar y usar herramientas

task_agent = create_react_agent(
    llm,
    tools=[add_task_tool, get_tasks_tool, complete_task_tool],
    prompt="Eres un Gestor de Tareas. Usa tus herramientas para leer, agregar o completar tareas en la base de datos de MongoDB. Sé breve y confirma los cambios."
)

calendar_agent = create_react_agent(
    llm,
    tools=[get_events_tool],
    prompt="Eres un Asistente de Calendario. Consulta las reuniones del usuario usando tu herramienta. Devuelve un resumen claro y ordenado."
)

summary_agent = create_react_agent(
    llm,
    tools=[get_tasks_tool, get_events_tool], 
    prompt="Eres un Asistente Personal. Tu rol es conversar con el usuario, saludar, dar tips de productividad, y generar resúmenes diarios usando tus herramientas para consultar eventos y tareas pendientes." \
           "Jamás inventes tareas o eventos, solo consulta usando las herramientas y resume la información. Sé amigable y útil."
           "Si las tareas son anteriores a la fecha actual, ignóralas. Concéntrate solo en lo relevante para hoy." \
           "Si las tareas estan completadas, colocalas con un check ✅. Para los eventos, muestra la hora y el título. Si no hay tareas o eventos, díselo al usuario de forma empática." \
           "Para los preparativos de mañana, utiliza las tareas y eventos que tengas programados para el día siguiente como referencia, y sugiere un checklist de cosas a preparar (ej. documentos, materiales, etc)."

)

# Envolturas (Nodos) para integrar los agentes al grafo principal
def task_node(state: AgentState):
    result = task_agent.invoke({"messages": state["messages"]})
    return {"messages": [result["messages"][-1]]}

def calendar_node(state: AgentState):
    result = calendar_agent.invoke({"messages": state["messages"]})
    return {"messages": [result["messages"][-1]]}

def summary_node(state: AgentState):
    result = summary_agent.invoke({"messages": state["messages"]})
    return {"messages": [result["messages"][-1]]}


# ─── 6. EL AGENTE SUPERVISOR (ROUTER) ────────────────────────────────────────
class Router(BaseModel):
    next_agent: Literal["task_agent", "calendar_agent", "summary_agent", "FINISH"] = Field(
        description="El agente que debe actuar. FINISH si el último mensaje ya responde la pregunta."
    )

def supervisor_node(state: AgentState):
    # Mecanismo de seguridad: Si ya respondió uno de los sub-agentes, terminamos el flujo.
    if len(state["messages"]) > 1 and state["messages"][-1].type == "ai":
        return {"next_agent": "FINISH"}

    system_prompt = """Eres el Supervisor A2A. Tu tarea es leer la petición del usuario y derivarla al agente especialista correcto.
    - task_agent: Si pide agregar, ver o completar tareas y pendientes.
    - calendar_agent: Si hace preguntas sobre su agenda, eventos, reuniones o disponibilidad.
    - summary_agent: Si es una charla general, saludos o pide tips de productividad.
    - FINISH: Si la consulta del usuario ya fue resuelta."""

    router = llm.with_structured_output(Router)
    result = router.invoke([SystemMessage(content=system_prompt)] + state["messages"])
    return {"next_agent": result.next_agent}


# ─── 7. CONSTRUCCIÓN DEL GRAFO A2A ───────────────────────────────────────────
workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_node)
workflow.add_node("task_agent", task_node)
workflow.add_node("calendar_agent", calendar_node)
workflow.add_node("summary_agent", summary_node)

workflow.add_edge(START, "supervisor")

# El supervisor decide el próximo paso condicionalmente
def route(state: AgentState):
    if state["next_agent"] == "FINISH":
        return END
    return state["next_agent"]

workflow.add_conditional_edges("supervisor", route)

# Después de que un agente actúa, vuelve al supervisor para que evalúe (y finalice)
workflow.add_edge("task_agent", "supervisor")
workflow.add_edge("calendar_agent", "supervisor")
workflow.add_edge("summary_agent", "supervisor")

# Compilamos la aplicación
agent_app = workflow.compile()

# ─── FUNCIÓN PARA EJECUTAR ───────────────────────────────────────────────────
def run_assistant(user_query: str) -> str:
    """Función principal que inicia el flujo y devuelve la respuesta del agente."""
    
    # 1. Calculamos la fecha y hora exacta en el momento de la consulta
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    # 2. Le inyectamos la fecha al agente de forma invisible (como si fuera parte de tu mensaje)
    mensaje_enriquecido = f"[Contexto del sistema: Ten en cuenta que la fecha de hoy es {today}].\n\nConsulta del usuario: {user_query}"
    
    initial_state = {"messages": [HumanMessage(content=mensaje_enriquecido)]}
    result = agent_app.invoke(initial_state)
    return result["messages"][-1].content

# Pruebas en consola (solo se ejecuta si corres python agent.py)
if __name__ == "__main__":
    print("🤖 Sistema Multi-Agente A2A Iniciado (Escribe 'salir' para terminar)")
    while True:
        query = input("\nUsuario: ")
        if query.lower() == "salir":
            break
        respuesta = run_assistant(query)
        print(f"\nAgente: {respuesta}")