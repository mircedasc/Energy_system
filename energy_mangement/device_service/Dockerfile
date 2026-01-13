# Folosește o imagine oficială Python
FROM python:3.10-slim

# Setează directorul de lucru în container
WORKDIR /app

# Copiază fișierul de cerințe
COPY ./requirements.txt /app/requirements.txt

# Instalează dependențele
RUN pip install --no-cache-dir -r requirements.txt

# Copiază codul aplicației (directorul 'app' local în directorul 'app' din container)
COPY ./app /app/app

# Expune portul pe care rulează serverul
EXPOSE 8000

# Comanda de start pentru a rula aplicația FastAPI
# Calea este "app.main:app" deoarece main.py este în directorul 'app'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]