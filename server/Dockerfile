FROM python:3.11-slim

ENV HOST=0.0.0.0 \
    PORT=5000 \
    MAX_UPLOAD_BYTES=5505024 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY server.py /app/server.py

RUN mkdir -p "${FILED_DIR}"
VOLUME ["/data"]

EXPOSE 5000
CMD ["python", "server.py"]