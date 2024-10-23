FROM python:stretch

# Set environment variables to avoid prompts from Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /

#RUN useradd -ms /bin/bash myuser
#
#USER myuser

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Устанавливаем локаль
RUN apt update && apt install -y --no-install-recommends locales; rm -rf /var/lib/apt/lists/*; sed -i '/^#.* ru_RU.UTF-8 /s/^#//' /etc/locale.gen; locale-gen

RUN locale -a

ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8

# Copy the requirements file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot's source code into the container
COPY . .

# Command to run the bot
CMD ["python", "Lytkarino_Weather_Bot.py"]
