# Utiliser une image de base Python
FROM python:3.9-slim

# Installer les dépendances système nécessaires pour Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    libappindicator1 \
    fonts-liberation \
    libnss3 \
    libasound2 \
    xdg-utils \
    libu2f-udev \
    ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Installer Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb || true && \
    apt-get -f install -y && \
    rm -rf google-chrome-stable_current_amd64.deb

# Définir le répertoire de travail
WORKDIR /app

# Copier le fichier requirements.txt dans l'image
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source dans le conteneur
COPY . .

# Définir la commande de démarrage
CMD ["python", "main.py"]
