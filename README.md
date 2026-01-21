# Sistem Distribuit de Monitorizare și Gestionare a Consumului de Energie

Aceasta este o aplicație distribuită bazată pe o arhitectură de microservicii, destinată gestionării dispozitivelor inteligente de măsurare a energiei, monitorizării consumului în timp real și oferirii de suport prin intermediul unui asistent AI.

Sistemul utilizează Docker pentru containerizare, RabbitMQ pentru comunicare asincronă, WebSocket pentru notificări în timp real și Traefik ca API Gateway.

## Arhitectura Sistemului

Aplicația este împărțită în următoarele componente logice:

1.  **Frontend (React):** Interfața utilizator pentru administratori și clienți.
2.  **API Gateway (Traefik):** Punctul unic de intrare care rutează cererile HTTP și WebSocket către microserviciile corespunzătoare.
3.  **Microservicii Backend (FastAPI):**
    * **Auth Service:** Gestionează autentificarea și generarea token-urilor JWT.
    * **User Service:** Gestionează conturile utilizatorilor (CRUD).
    * **Device Service:** Gestionează dispozitivele și maparea acestora la utilizatori.
    * **Monitoring Service:** Procesează datele de la senzori, calculează consumul orar și verifică depășirea limitelor.
    * **Chat Service:** Asistent virtual integrat cu Google Gemini AI pentru suport utilizatori.
    * **Communication Service:** Gestionează conexiunile WebSocket pentru a trimite alerte și mesaje chat către frontend.
4.  **Infrastructură:**
    * **PostgreSQL:** Baza de date relațională (baze de date logice separate pentru fiecare serviciu).
    * **RabbitMQ:** Message Broker pentru comunicarea asincronă între servicii (date senzori, sincronizare, notificări).
5.  **Simulator:** Script Python care generează date simulate de consum pentru dispozitive.

## Tehnologii Utilizate

* **Limbaje:** Python (Backend, Simulator), JavaScript/JSX (Frontend).
* **Framework-uri:** FastAPI, React.
* **Baze de date:** PostgreSQL, SQLAlchemy.
* **Mesagerie:** RabbitMQ (Pika).
* **Containerizare:** Docker, Docker Compose.
* **AI:** Google Generative AI (Gemini 1.5 Flash).
* **Altele:** Axios, Chart.js, React Toastify.

## Configurare și Instalare

### Cerințe preliminare

* Docker și Docker Desktop instalate.
* O cheie API validă pentru Google Gemini (pentru funcționalitatea de chat).

### Pași de instalare

1.  Clonați repository-ul proiectului.
2.  Configurați variabila de mediu pentru cheia API Google Gemini în fișierul `docker-compose.yml` la secțiunea `chat_service`:
    ```yaml
    environment:
      GEMINI_API_KEY: "CHEIA_TA_AICI"
    ```
3.  Porniți întreaga stivă de aplicații folosind Docker Compose:
    ```bash
    docker-compose up -d --build
    ```
4.  Așteptați inițializarea containerelor. Puteți verifica starea acestora cu:
    ```bash
    docker ps
    ```

## Utilizare

### Accesarea Aplicației

Aplicația Frontend este accesibilă prin browser la adresa: `http://localhost`

### Fluxuri Principale

1.  **Autentificare:**
    * Logați-vă cu un cont de administrator (configurat în scripturile de inițializare) sau creați un cont nou prin pagina de înregistrare.

2.  **Administrare (Admin Dashboard):**
    * Creați utilizatori noi cu rolul de "Client" sau "Administrator".
    * Creați dispozitive noi, setați descrierea, adresa și consumul maxim orar.
    * Asignați dispozitivele utilizatorilor prin specificarea `Owner ID`.

3.  **Monitorizare (Client Dashboard):**
    * Utilizatorii pot vizualiza lista dispozitivelor proprii.
    * Accesarea detaliilor unui dispozitiv afișează istoricul consumului sub formă de grafice (date recente, ultimele 24h, istoric complet).

4.  **Simulare Senzori:**
    * Configurați scriptul simulatorului sau fișierul de configurare al acestuia pentru a trimite date către un `device_id` existent.
    * Datele sunt trimise prin coada RabbitMQ `sensor_data`.
    * Dacă valoarea depășește limita setată, o notificare vizuală va apărea în interfață.

5.  **Chat și Suport:**
    * Utilizați widget-ul de chat pentru a adresa întrebări.
    * Sistemul folosește AI pentru a răspunde la întrebări generale sau rutează cererea către un operator dacă este necesar.

## Structura API și Porturi

Deși serviciile rulează pe porturi interne, Traefik le expune pe portul 80 folosind prefixe URL:

* **Frontend:** `http://localhost/`
* **Auth Service:** `http://localhost/auth`
* **User Service:** `http://localhost/users`
* **Device Service:** `http://localhost/devices`
* **Monitoring Service:** `http://localhost/monitoring`
* **Chat Service:** `http://localhost/chat`
* **WebSocket:** `ws://localhost/ws`

## Dezvoltare și Depanare

Pentru a vizualiza log-urile unui serviciu specific în timp real:

```bash
docker-compose logs -f nume_serviciu