FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/
COPY data/ ./data/

# Expose the API port
EXPOSE 8000

# Persist expense data outside the container image if a volume is mounted at /app/data
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
