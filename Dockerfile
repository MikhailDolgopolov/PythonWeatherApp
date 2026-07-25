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
RUN sed -i '/^#.* ru_RU.UTF-8 /s/^#//' /etc/locale.gen \
    && locale-gen ru_RU.UTF-8 \
    && echo "LANG=ru_RU.UTF-8" > /etc/default/locale \
    && echo "LC_ALL=ru_RU.UTF-8" >> /etc/default/locale

ENV LANG=ru_RU.UTF-8 \
    LC_ALL=ru_RU.UTF-8

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
