FROM python:3.12-slim

# Librerías del sistema necesarias para WeasyPrint (Pango, Cairo, GObject, etc.)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . /app

EXPOSE 8080

CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:8080"]
