# Lightweight Python base image
FROM python:3.11-slim

WORKDIR /app

# Install the frontend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit app
COPY app.py .

# Streamlit port
EXPOSE 8501

# Backend address inside the Docker network (can be overridden with -e BACKEND_URL=...)
ENV BACKEND_URL=http://superkart-backend:7860

# Run Streamlit on all interfaces (XSRF protection off for the port-forwarded Codespace URL)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableXsrfProtection=false"]
