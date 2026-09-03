FROM python:3.12-slim

WORKDIR /app

COPY core/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ ./core/
COPY core/data/real_prerace_dataset.csv ./core/data/real_prerace_dataset.csv
COPY core/models/apex_core_v1_model.joblib ./core/models/apex_core_v1_model.joblib

ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "core.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
