# 🤖 AGENTA - Asistente Personal con LangGraph + OpenAI

Agente de IA que actúa como tu asistente personal: te recuerda tus tareas del
día y te sugiere preparativos para el día siguiente, usando LangGraph y GPT.

---

## 📁 Estructura del proyecto

```
personal-assistant-agent/
├── .env                ← Archivo de configuración para tu API key
├── requirements.txt    ← Dependencias del proyecto
├── calendar_data.py    ← Tus eventos y tareas del calendario
└── agent.py            ← El agente LangGraph (lógica principal)
```

---

## 🔑 Dónde poner tu API Key de OpenAI

1. Copia el archivo `.env.example` y renómbralo `.env`:
   ```bash
   cp .env.example .env
   ```

2. Abre `.env` y reemplaza la clave de ejemplo:
   ```
   OPENAI_API_KEY=sk-tu-clave-real-aqui
   ```

3. ¡Listo! El agente la leerá automáticamente al iniciar.

---

## 🚀 Instalación y ejecución

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Agregar tus eventos y tareas
Abre `calendar_data.py` y edita las listas `EVENTS` y `TASKS` con tus
datos reales. Cada evento tiene estos campos:

```python
CalendarEvent(
    id="e1",
    title="Nombre del evento",
    date="2025-02-20",        # formato YYYY-MM-DD
    time="09:00",             # formato HH:MM
    duration_minutes=60,
    location="Lugar opcional",
    description="Descripción",
    requires_preparation=True,  # ¿Necesita prep previa?
)

Task(
    id="t1",
    title="Nombre de la tarea",
    due_date="2025-02-20",
    priority="alta",          # alta | media | baja
    notes="Notas opcionales",
)
```

### 3. Ejecutar el agente
```bash
python agent.py
```

---

## 🧠 Arquitectura del Grafo (LangGraph)

```
[load_calendar]
       │
       ▼
[generate_daily_summary]   ← LLM genera resumen del día
       │
       ▼
[generate_preparation_tips] ← LLM genera preparativos para mañana
       │
       ├── ¿hay pregunta del usuario? ──► [respond_to_user] ──► END
       │
       └── no ──────────────────────────────────────────────► END
```

### Descripción de cada nodo:

| Nodo | Descripción |
|------|-------------|
| `load_calendar` | Carga eventos y tareas de hoy y mañana desde `calendar_data.py` |
| `generate_daily_summary` | GPT genera un resumen motivador del día con contexto |
| `generate_preparation_tips` | GPT sugiere preparativos concretos para el día siguiente |
| `respond_to_user` | Responde preguntas específicas del usuario sobre su agenda |

---

## 💬 Ejemplos de preguntas que puedes hacerle

- *"¿A qué hora es mi primera reunión?"*
- *"¿Cuánto tiempo tengo entre el almuerzo y la siguiente reunión?"*
- *"¿Qué debo preparar para la presentación de mañana?"*
- *"¿Cuál es mi tarea más urgente de hoy?"*

---

## ⚙️ Personalización

### Cambiar el modelo de OpenAI
En `agent.py`, línea del `ChatOpenAI`:
```python
llm = ChatOpenAI(
    model="gpt-4o",        # Más potente (más caro)
    # model="gpt-4o-mini",  # Más económico (por defecto)
    temperature=0.3,
)
```

---

## 🔒 Seguridad

- Nunca expongas tu `.env` públicamente.
- Agrega `.env` a `.gitignore`:
