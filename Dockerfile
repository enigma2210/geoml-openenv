# Use a lightweight version of Python to ensure we build fast and use little RAM
FROM python:3.11-slim

# Prevent Python from writing .pyc files and keep stdout unbuffered for logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install the necessary libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the rest of our environment files into the container
COPY . .

# OpenEnv handles the execution port automatically, so we just expose the default
EXPOSE 8000