# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 python:3.11-slim

RUN echo 'deb http://deb.debian.org/debian stable main contrib' > /etc/apt/sources.list
RUN apt-get update && apt-get install -y git wget espeak ffmpeg mbrola
RUN mkdir -p /usr/share/mbrola/us1
RUN wget https://github.com/numediart/MBROLA-voices/raw/master/data/us1/us1 -O /usr/share/mbrola/us1/us1
RUN wget https://github.com/numediart/MBROLA-voices/raw/master/data/us1/us1mrpa -O /usr/share/mbrola/us1/us1mrpa

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run app.py when the container launches
CMD ["gunicorn", "main:web_app", "--bind", "0.0.0.0:8080", "-k", "aiohttp.GunicornWebWorker"]