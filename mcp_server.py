from fastmcp import FastMCP
from typing import List, Dict
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
import logging
import datetime
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

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

def get_calendar_service():
    """Maneja la autenticación y devuelve el servicio de la API."""
    creds = None
    # Buscamos el token en la ruta actual
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # Si no hay credenciales o no son válidas
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Guardamos el token refrescado
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        else:
            raise Exception("No se encontró token.json válido en Docker. Por favor generarlo localmente.")
            
    return build('calendar', 'v3', credentials=creds)

@mcp.tool()
def get_events(target_date: str) -> List[Dict]:
    """Obtiene eventos reales del calendario del usuario."""
    logging.info(f"🤖 La IA solicitó 'get_events' para la fecha: {target_date}")
    try:
        service = get_calendar_service()
        
        # Convertir YYYY-MM-DD a formato RFC3339 requerido por Google
        start_of_day = datetime.datetime.strptime(target_date, "%Y-%m-%d")
        end_of_day = start_of_day + datetime.timedelta(days=1)
        
        time_min = start_of_day.isoformat() + 'Z'
        time_max = end_of_day.isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min,
            timeMax=time_max, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        formatted_events = []
        
        for event in events:
            # Capturar hora de inicio (puede ser evento de todo el día sin 'dateTime')
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            formatted_events.append({
                "id": event.get('id'),
                "title": event.get('summary', 'Sin título'),
                "time": start,
                "location": event.get('location', 'Virtual/No especificada'),
                "description": event.get('description', '')
            })
            
        return formatted_events
    except Exception as e:
        logging.error(f"Error accediendo a Calendar API: {e}")
        return [{"error": "No se pudo acceder a Google Calendar. Revisa las credenciales."}]

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