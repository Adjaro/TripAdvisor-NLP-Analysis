# Étape 1 : Utilisation d'une image légère
FROM python:3.9-slim

# Étape 2 : Installation des outils et de Google Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm -rf /var/lib/apt/lists/* /tmp/*

# Étape 3 : Définir le port d'affichage pour Chrome
ENV DISPLAY=:99

# Étape 4 : Définir le répertoire de travail
WORKDIR /app

# Étape 5 : Copier les fichiers nécessaires
COPY . .

# Étape 6 : Mise à jour de pip et installation des dépendances
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Étape 7 : Commande par défaut pour exécuter l'application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
