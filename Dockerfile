FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY src_fearon_dia/ ./src_fearon_dia/
COPY api/ ./api/

ENV PORT=8000
EXPOSE ${PORT}

CMD python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
