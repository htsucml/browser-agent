FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python3 -m playwright install --with-deps chromium

COPY . .
RUN mkdir -p logs/runs

EXPOSE 8000
ENV PORT=8000
CMD ["sh", "-c", "exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
