FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user
RUN useradd -m -s /bin/bash emulator && \
    chown -R emulator:emulator /app

# Copy requirements first for better caching
COPY --chown=emulator:emulator requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY --chown=emulator:emulator *.py ./
COPY --chown=emulator:emulator config.json ./

# Create necessary directories
RUN mkdir -p logs && chown emulator:emulator logs

# Switch to non-root user
USER emulator

# Expose SSH port
EXPOSE 2222

# Set environment variables for configuration
ENV SSH_EMULATOR_HOST=0.0.0.0
ENV SSH_EMULATOR_PORT=2222

# Run the emulator
CMD ["python", "main.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', 2222)); s.close()"