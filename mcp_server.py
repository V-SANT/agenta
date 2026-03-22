from fastmcp import FastMCP
from typing import List, Dict
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
import logging
import sys

# --- CONEXIÓN A MONGODB ---
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["agenta_db"]
    tasks_collection = db["tasks"]
    logging.info("✅ Conexión exitosa a MongoDB")
except Exception as e:
    logging.error(f"❌ Error conectando a MongoDB: {e}")
    raise e

# Inicializamos el servidor MCP dándole un nombre descriptivo
mcp = FastMCP("AgentaDataServer")

@mcp.tool()
def get_events(target_date: str) -> List[Dict]:
    """Obtiene eventos del calendario (Versión temporal simulada)."""
    logging.info(f"🤖 La IA solicitó 'get_events' para la fecha: {target_date}")
    
    # Devolvemos un evento de prueba para que la IA no se quede con las manos vacías
    return [
        {
            "id": "mock_1",
            "title": "Reunión de prueba (Google Calendar Pendiente)",
            "time": "15:00",
            "location": "Virtual",
            "description": "Falta descargar credentials.json para ver eventos reales.",
            "requires_preparation": False
        }
    ]

@mcp.tool()
def get_tasks(status: str = "pending") -> List[Dict]:
    """Obtiene las tareas del usuario desde MongoDB. status puede ser 'pending' o 'completed'."""
    logging.info(f"🤖 La IA solicitó 'get_tasks' con estado: {status}")
    is_completed = True if status == "completed" else False
    
    # Buscar en la base de datos
    tasks = list(tasks_collection.find({"completed": is_completed}))
    
    # Formatear el ObjectId de Mongo a string para que sea compatible con JSON
    formatted_tasks = []
    for t in tasks:
        formatted_tasks.append({
            "id": str(t["_id"]),
            "title": t.get("title", "Sin título"),
            "priority": t.get("priority", "media"),
            "due_date": t.get("due_date", ""),
            "completed": t.get("completed", False)
        })
    return formatted_tasks

@mcp.tool()
def add_task(title: str, priority: str = "media", due_date: str = "") -> str:
    """Guarda una nueva tarea en la base de datos MongoDB. Devuelve un mensaje de éxito."""
    logging.info(f"🤖 La IA solicitó 'add_task': {title}")
    new_task = {
        "title": title,
        "priority": priority,
        "due_date": due_date,
        "completed": False
    }
    result = tasks_collection.insert_one(new_task)
    return f"Tarea '{title}' guardada exitosamente en la base de datos con ID: {str(result.inserted_id)}"

@mcp.tool()
def complete_task(task_id: str) -> str:
    """Marca una tarea como completada en la base de datos usando su ID."""
    logging.info(f"🤖 La IA solicitó 'complete_task' para el ID: {task_id}")
    try:
        result = tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"completed": True}}
        )
        if result.modified_count > 0:
            return f"La tarea {task_id} ha sido marcada como completada."
        else:
            return "No se encontró la tarea o ya estaba completada previamente."
    except Exception as e:
        return f"Error al actualizar la base de datos: {str(e)}"

if __name__ == "__main__":
    # ❌ ELIMINAMOS EL PRINT: print("🚀 Iniciando Servidor FastMCP para Agenta...")
    # ✅ Usamos logging (que ahora va a stderr) si queremos ver el mensaje en la consola de Docker
    logging.info("🚀 Iniciando Servidor FastMCP para Agenta...")
    mcp.run()