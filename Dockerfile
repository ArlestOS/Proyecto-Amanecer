FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Este comando es el que Google seguirá sin intentar adivinar nada
CMD ["streamlit", "run", "aria_app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]