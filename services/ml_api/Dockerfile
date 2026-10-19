FROM python:3.11-slim

WORKDIR /app

COPY services/ml_api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy services, data, and models
COPY services /app/services
COPY data /app/data

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "services.ml_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
