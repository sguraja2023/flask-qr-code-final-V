# Use the official Python image as a base
FROM python:3.9-slim

# Set environment variables to prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy the application code and requirements file into the container
COPY . /app/

# Install system dependencies for Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8080

# Run the application
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
