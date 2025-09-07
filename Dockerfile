# Use Python 3.13 slim image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY src/ /app/

# Create logs directory
RUN mkdir -p /app/logs

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port (Railway will set this automatically)
EXPOSE 8000

# Run gunicorn (Railway-optimized)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "jeycentre.wsgi:application"]
