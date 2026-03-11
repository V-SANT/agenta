# mcp_server.py
from fastmcp import FastMCP
from typing import List, Dict

# Inicializamos el servidor MCP dándole un nombre descriptivo
mcp = FastMCP("AgentaDataServer")

# Usamos el decorador @mcp.tool() para exponer esta función a los agentes
@mcp.tool()
def get_events(target_date: str) -> List[Dict]:
    """
    Obtiene los eventos del calendario para una fecha específica.
    Formato de fecha esperado: YYYY-MM-DD
    """
    # TODO: Aquí implementaremos la conexión con la API de Google Calendar usando OAuth
    print(f"[MCP] Buscando eventos para la fecha: {target_date}")
    return [
        {
            "id": "e1",
            "title": "Reunión de sincronización (Mock)",
            "time": "10:00",
            "requires_preparation": False
        }
    ]

@mcp.tool()
def get_tasks(status: str = "pending") -> List[Dict]:
    """
    Obtiene las tareas del usuario. status puede ser 'pending' o 'completed'.
    """
    # TODO: Aquí implementaremos la lectura/escritura con Amazon DynamoDB mediante boto3
    print(f"[MCP] Buscando tareas con estado: {status}")
    return [
        {
            "id": "t1",
            "title": "Configurar DynamoDB en AWS",
            "priority": "alta",
            "completed": False
        }
    ]

if __name__ == "__main__":
    # Ejecuta el servidor para que se quede escuchando peticiones
    print("🚀 Iniciando Servidor FastMCP para Agenta...")
    mcp.run()