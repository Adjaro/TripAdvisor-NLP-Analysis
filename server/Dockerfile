FROM python:3.9

# Installer les dépendances
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libxss1 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    fonts-liberation \
    xdg-utils

# Installer Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Installer chromedriver
RUN wget -q https://chromedriver.storage.googleapis.com/$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

RUN mkdir -p /root/.local/share/undetected_chromedriver && chmod -R 777 /root/.local/share/undetected_chromedriver

# Étape 4 : Définir le répertoire de travail
WORKDIR /app

# Étape 5 : Copier les fichiers nécessaires
COPY . .

# Étape 6 : Mise à jour de pip et installation des dépendances
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
RUN pip install undetected-chromedriver

# Étape 7 : Commande par défaut pour exécuter l'application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]