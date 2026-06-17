FROM python:3.12-slim

# ============================
# Instalar dependencias del sistema para WeasyPrint
# ============================
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# ============================
# Configuración del contenedor
# ============================
WORKDIR /app

# Copiar dependencias
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Exponer puerto para Railway
EXPOSE 8080

# ============================
# Comando de inicio (Gunicorn)
# ============================
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:8080"]
