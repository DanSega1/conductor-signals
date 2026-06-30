FROM python:3.14-slim AS builder

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir .

COPY app/ app/

FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /app /app

EXPOSE 8000

CMD ["uvicorn", "app.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
