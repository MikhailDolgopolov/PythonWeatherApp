# Use the official Python image from Docker Hub
FROM python:3.11

# Set environment variables to avoid prompts from Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /

RUN useradd -ms /bin/bash myuser

USER myuser

# Install necessary packages for locales and sudo
RUN apt-get update && apt-get install -y \
    locales \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Generate the desired locale (e.g., Russian)
RUN locale-gen ru_RU.UTF-8

RUN SUDO update-locale

# Set the locale environment variable
ENV LANG=ru_RU.UTF-8 \
    LANGUAGE=ru_RU:ru \
    LC_ALL=ru_RU.UTF-8


# Copy the requirements file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot's source code into the container
COPY . .

# Command to run the bot
CMD ["python", "Lytkarino_Weather_Bot.py"]
