# Use the Debian Stretch Python image
FROM python:3.11-slim

# Set environment variables to avoid prompts from Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /data

# Set the timezone
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install locales and generate the desired locale
RUN apt update && apt install -y --no-install-recommends locales && \
    rm -rf /var/lib/apt/lists/* && \
    sed -i '/^#.* ru_RU.UTF-8 /s/^#//' /etc/locale.gen && \
    locale-gen && \
    echo "LANG=ru_RU.UTF-8" >> /etc/default/locale && \
    echo "LC_ALL=ru_RU.UTF-8" >> /etc/default/locale

# Set locale environment variables
ENV LANG=ru_RU.UTF-8 \
    LC_ALL=ru_RU.UTF-8

# Create a non-root user and switch to it
RUN useradd -ms /bin/bash myuser
USER myuser

# Copy the requirements file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot's source code into the container
COPY --chown=myuser:myuser . .

# Command to run the bot
CMD ["python", "Lytkarino_Weather_Bot.py"]
