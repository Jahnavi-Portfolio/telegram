# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    pango1.0-tools \
    libpangocairo-1.0-0 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# The command to run on container startup will be taken from the Procfile
# by the hosting platform (e.g., Render, Railway).
# The CMD is not strictly necessary when using a Procfile but can be a good fallback.
# Expose the port the app runs on
EXPOSE 8000

# The Procfile will define the 'web' and 'worker' commands, so CMD is not strictly needed
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
