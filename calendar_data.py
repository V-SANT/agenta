# calendar_data.py

from datetime import date
from typing import List
from dataclasses import dataclass

@dataclass
class CalendarEvent:
    id: str
    title: str
    date: str         
    time: str          
    duration_minutes: int = 60
    location: str = ""
    description: str = ""
    requires_preparation: bool = False

@dataclass
class Task:
    id: str
    title: str
    due_date: str     
    priority: str = "media"   
    completed: bool = False
    notes: str = ""

# ─── DATOS ACTUALIZADOS ────────────────────────
EVENTS: List[CalendarEvent] = [
    CalendarEvent(
        id="e1",
        title="Daily Standup - Echokey",
        date="2026-03-11",
        time="10:00",
        duration_minutes=30,
        location="Videollamada",
        description="Revisión de estado de las tareas de Frontend y bloqueos actuales.",
        requires_preparation=False,
    ),
    CalendarEvent(
        id="e2",
        title="Clase de Teoría de Algoritmos (UBA)",
        date="2026-03-11",
        time="18:00",
        duration_minutes=120,
        location="Facultad de Ingeniería",
        description="Ayudar a los alumnos con ejercicios de programación dinámica y teoría de grafos.",
        requires_preparation=True,
    ),
    CalendarEvent(
        id="e3",
        title="Clase de Yoga",
        date="2026-03-11",
        time="20:30",
        duration_minutes=60,
        location="Estudio",
        description="Sesión para mejorar flexibilidad y recuperar energía.",
        requires_preparation=True,
    ),
    CalendarEvent(
        id="e4",
        title="Reunión de Avance - App Sandwichería",
        date="2026-03-12",
        time="14:00",
        duration_minutes=60,
        location="Videollamada",
        description="Definir la integración de billeteras de pago locales en la aplicación web.",
        requires_preparation=True,
    ),
    CalendarEvent(
        id="e5",
        title="Desarrollo del Chatbot Dino",
        date="2026-03-12",
        time="16:00",
        duration_minutes=120,
        location="Casa",
        description="Ajustar Ollama y el modelo Qwen2:7b para que el bot muestre correctamente su proceso de pensamiento por consola.",
        requires_preparation=False,
    ),
]

TASKS: List[Task] = [
    Task(
        id="t1",
        title="Preparar correcciones de Algoritmos",
        due_date="2026-03-11",
        priority="alta",
        notes="Revisar las entregas de los alumnos antes de la clase de las 18:00.",
    ),
    Task(
        id="t2",
        title="Revisar PRs de la UI",
        due_date="2026-03-11",
        priority="media",
        notes="Hacer code review de los nuevos componentes de React que no estaban renderizando bien las sugerencias.",
    ),
    Task(
        id="t3",
        title="Ajustar endpoint de pagos",
        due_date="2026-03-12",
        priority="alta",
        notes="Probar el comando curl para la API del local de sándwiches.",
    ),
    Task(
        id="t4",
        title="Refactorizar script de Python",
        due_date="2026-03-12",
        priority="media",
        notes="Añadir la visualización de métricas en el script principal del bot de consola.",
    ),
    Task(
        id="t5",
        title="Preparar bolso para yoga",
        due_date="2026-03-12",
        priority="baja",
        notes="Llevar el mat y ropa cómoda.",
    ),
]

def get_events_for_date(target_date: str) -> List[CalendarEvent]:
    return [e for e in EVENTS if e.date == target_date]

def get_tasks_for_date(target_date: str) -> List[Task]:
    return [t for t in TASKS if t.due_date == target_date and not t.completed]

def get_today() -> str:
    return date.today().strftime("%Y-%m-%d")

def get_tomorrow() -> str:
    from datetime import timedelta
    return (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")