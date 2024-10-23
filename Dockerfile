# Use the official Python image from Docker Hub
FROM python:3.11-slim

# Set environment variables to avoid prompts from Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /

# Copy the requirements file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot's source code into the container
COPY . .

# Command to run the bot
CMD ["python", "Lytkarino_Weather_Bot.py"]
