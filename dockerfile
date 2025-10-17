# 1. Schlanker Basis‑Image wählen
FROM python:3.9-slim

# 2. Arbeitsverzeichnis anlegen
WORKDIR /app

# Enviroment Variables
ENV APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    APP_PUBLIC_URL=

# 3. Abhaengigkeiten zuerst kopieren (Layer‑Cache!)
COPY requirements_web.txt .
COPY main.py .
COPY ["data", "./data"]
COPY StudyLogApp StudyLogApp


# 4. Installieren – ohne Cache im Image zu belassen
RUN  ln -sf /usr/share/zoneinfo/Europe/Zurich /etc/timezone && \
     ln -sf /usr/share/zoneinfo/Europe/Zurich /etc/localtime && \
     pip install --no-cache-dir -r requirements_web.txt


# 6. Startkommando
# Start ‑ Shell‑Form, damit $VARs expandieren
CMD sh -c 'textual serve \
            -h "${APP_HOST:-0.0.0.0}" \
            -p "${APP_PORT:-8000}" \
            ${APP_PUBLIC_URL:+-u "${APP_PUBLIC_URL}"} \
            main.py'
