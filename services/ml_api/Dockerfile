FROM python:3.11-slim

WORKDIR /app

COPY services/ml_api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy models and code
COPY services/ml /app/services/ml
COPY services/ml_api /app/services/ml_api
COPY data /app/data

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "services.ml_api.main:app", "--host", "0.0.0.0", "--port", "8001"]
