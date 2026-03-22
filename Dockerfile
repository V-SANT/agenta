# Usamos una imagen oficial y ligera de Python
FROM python:3.12-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos el archivo de requerimientos e instalamos dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código del proyecto
COPY . .

# Exponemos el puerto que usa Streamlit
EXPOSE 8501

# Comando por defecto para ejecutar la aplicación
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]