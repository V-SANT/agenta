# calendar_data.py
# Aquí se definen los eventos y tareas del calendario.

from datetime import date, datetime
from typing import List
from dataclasses import dataclass, field


@dataclass
class CalendarEvent:
    id: str
    title: str
    date: str          # formato: "YYYY-MM-DD"
    time: str          # formato: "HH:MM" o "" si es todo el día
    duration_minutes: int = 60
    location: str = ""
    description: str = ""
    requires_preparation: bool = False


@dataclass
class Task:
    id: str
    title: str
    due_date: str      # formato: "YYYY-MM-DD"
    priority: str = "media"   # alta | media | baja
    completed: bool = False
    notes: str = ""


# ─── DATOS DE EJEMPLO (GENÉRICOS PARA DEMOSTRACIÓN) ────────────────────────
EVENTS: List[CalendarEvent] = [
    CalendarEvent(
        id="e1",
        title="Reunión diaria de sincronización",
        date="2026-02-25",
        time="10:00",
        duration_minutes=30,
        location="Videollamada",
        description="Revisión de estado de las tareas del equipo.",
        requires_preparation=False,
    ),
    CalendarEvent(
        id="e2",
        title="Hacer las compras del supermercado",
        date="2026-02-25",
        time="18:30",
        duration_minutes=60,
        location="Supermercado local",
        description="Comprar víveres para la semana.",
        requires_preparation=True,
    ),
    CalendarEvent(
        id="e3",
        title="Gimnasio",
        date="2026-02-25",
        time="20:00",
        duration_minutes=60,
        location="Gimnasio del barrio",
        description="Día de entrenamiento cardiovascular.",
        requires_preparation=True,
    ),
    CalendarEvent(
        id="e4",
        title="Limpiar la casa",
        date="2026-02-26",
        time="09:00",
        duration_minutes=120,
        location="Casa",
        description="Limpieza general, barrer y organizar el escritorio.",
        requires_preparation=False,
    ),
    CalendarEvent(
        id="e5",
        title="Presentación de métricas mensuales",
        date="2026-02-26",
        time="15:00",
        duration_minutes=60,
        location="Sala de reuniones virtual",
        description="Mostrar el progreso del proyecto al cliente.",
        requires_preparation=True,
    ),
]

TASKS: List[Task] = [
    Task(
        id="t1",
        title="Hacer lista de compras",
        due_date="2026-02-25",
        priority="alta",
        notes="Revisar la alacena antes de salir.",
    ),
    Task(
        id="t2",
        title="Responder correos pendientes",
        due_date="2026-02-25",
        priority="media",
        notes="Priorizar los correos del departamento de diseño.",
    ),
    Task(
        id="t3",
        title="Lavar la ropa",
        due_date="2026-02-26",
        priority="alta",
        notes="Ropa blanca y de color.",
    ),
    Task(
        id="t4",
        title="Pagar servicios de internet y luz",
        due_date="2026-02-26",
        priority="alta",
        notes="Vencen a fin de mes, pagar por la app del banco.",
    ),
    Task(
        id="t5",
        title="Leer 20 páginas del libro",
        due_date="2026-02-26",
        priority="baja",
        notes="Lectura recreativa antes de dormir.",
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