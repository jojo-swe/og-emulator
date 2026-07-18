FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 10001 emulator

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/runtime \
    && chown -R emulator:emulator /app

USER emulator

EXPOSE 2222

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import socket; s=socket.create_connection(('127.0.0.1', 2222), 2); s.close()"

ENTRYPOINT ["python", "-m", "emulator"]
CMD ["--host", "0.0.0.0", "--port", "2222"]
