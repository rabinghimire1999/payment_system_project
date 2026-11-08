FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# This ensures transformer can see backend
ENV PYTHONPATH=/app 

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Match the port in your run_transformer.py
EXPOSE 8001

CMD ["python", "run_transformer.py"]