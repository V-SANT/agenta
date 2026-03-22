# app.py
import streamlit as st
import os
from pymongo import MongoClient
from dotenv import load_dotenv

from ui.home import render_home
from ui.chat import render_chat
from ui.tasks import render_tasks

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["agenta_db"]
tasks_collection = db["tasks"]

st.set_page_config(page_title="AGENTA", page_icon="🤖", layout="wide")
st.title("🤖 AGENTA")

tab_home, tab_chat, tab_tasks = st.tabs([
    "🏠 Home", "💬 Chat", "✅ Lista de Tareas"
])

with tab_home:
    render_home(tasks_collection)

with tab_chat:
    render_chat()

with tab_tasks:
    render_tasks(tasks_collection) 