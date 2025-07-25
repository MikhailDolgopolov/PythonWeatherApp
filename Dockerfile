FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Moscow

# Set working directory
WORKDIR /app

# Create directories and set permissions as root
RUN mkdir -p /app/data /app/.cache /app/Images /app/data/images

# Create a non-root user
RUN useradd -ms /bin/bash python_user && chown -R python_user:python_user /app

RUN apt update && apt install -y --no-install-recommends ca-certificates \
    curl iputils-ping && \
    rm -rf /var/lib/apt/lists/*

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install locales
RUN apt update && apt install -y --no-install-recommends locales && \
    rm -rf /var/lib/apt/lists/* && \
    sed -i '/^#.* ru_RU /s/^#//' /etc/locale.gen && \
    locale-gen && \
    echo "LANG=ru_RU.UTF-8" >> /etc/default/locale && \
    echo "LC_ALL=ru_RU.UTF-8" >> /etc/default/locale

ENV LANG=ru_RU.UTF-8 \
    LC_ALL=ru_RU.UTF-8

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Switch to non-root user
USER python_user

# Copy the rest of the code
COPY --chown=python_user:python_user . .

# Start the bot
CMD ["python", "Lytkarino_Weather_Bot.py"]
