FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Moscow

WORKDIR /app

# System packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        locales \
        curl \
        iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Russian locale
RUN apt update && apt install -y --no-install-recommends locales && \
    sed -i 's/^# *\(ru_RU.UTF-8 UTF-8\)/\1/' /etc/locale.gen && \
    locale-gen ru_RU.UTF-8 && \
    update-locale LANG=ru_RU.UTF-8 LC_ALL=ru_RU.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=ru_RU.UTF-8
ENV LC_ALL=ru_RU.UTF-8

# Timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Application user
RUN useradd --create-home --shell /bin/bash python_user

# Application directories
RUN mkdir -p \
        /app/data \
        /app/.cache \
        /app/Images \
        /app/data/images \
    && chown -R python_user:python_user /app

# Dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Application files
COPY --chown=python_user:python_user . .

USER python_user

CMD ["python", "Lytkarino_Weather_Bot.py"]
