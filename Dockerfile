FROM python:3.9-slim

# Install system dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Create a start script to handle different service types
RUN echo '#!/bin/bash\n\
if [ "$PYTHON_SERVICE_TYPE" = "BACKEND" ]; then\n\
    echo "Starting Backend (FastAPI)..."\n\
    python server_signer.py\n\
else\n\
    echo "Starting Frontend (Django)..."\n\
    python Voice2sign/manage.py runserver 0.0.0.0:$PORT\n\
fi' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
