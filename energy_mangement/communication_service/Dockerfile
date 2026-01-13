# Folosim o imagine oficială de Python (ușoară și stabilă)
FROM python:3.10

# Setăm directorul de lucru în container
WORKDIR /app

# Copiem fișierul cu dependențe
COPY ./requirements.txt /app/requirements.txt

# Instalăm dependențele
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copiem codul sursă al aplicației
COPY ./app /app/app

# Expunem portul pe care rulează Uvicorn
EXPOSE 8000

# Comanda de start
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]