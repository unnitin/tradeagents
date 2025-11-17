FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (if needed later, add gcc/libssl-dev, etc.)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend ./backend

EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "backend.wsgi:app"]
