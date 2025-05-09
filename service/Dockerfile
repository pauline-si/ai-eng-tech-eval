# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if any (e.g., for psycopg2-binary if using PostgreSQL)
# RUN apt-get update && apt-get install -y ... && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the app when the container launches
# The `fastapi dev` command already includes --reload for development
CMD ["fastapi", "dev", "main.py", "--host", "0.0.0.0", "--port", "8000"]
