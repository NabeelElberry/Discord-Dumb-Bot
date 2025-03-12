# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

COPY requirements.txt /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY . /app

# Set environment variables
ENV DISCORD_TOKEN="" \
GPT_KEY="" 

# Run the application
CMD ["python", "main.py"]