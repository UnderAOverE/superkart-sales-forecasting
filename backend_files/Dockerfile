# Lightweight Python base image matching the training runtime
FROM python:3.13-slim

# Working directory inside the container
WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API code and the serialized model
COPY app.py superkart_model.joblib ./

# Flask API port
EXPOSE 7860

# Production WSGI server: 2 workers, 4 threads each, bound to all interfaces
CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "120", "--bind", "0.0.0.0:7860", "app:superkart_api"]
