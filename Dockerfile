# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.11-slim

RUN apt-get update && apt-get upgrade -y && apt-get install -y git

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN python -m pip install --upgrade pip poetry
RUN poetry install --only main

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
ENTRYPOINT ["poetry", "run", "gunicorn", "main:web_app", "--bind", "0.0.0.0:8080", "-k", "aiohttp.GunicornWebWorker"]