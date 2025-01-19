# TripAdvisor-NLP-Analysis


An NLP and Text Mining project focused on analyzing TripAdvisor reviews of restaurants in Lyon. Developed as part of the Master 2 SISE program, this project extracts valuable insights from customer feedback using natural language processing (NLP) and text analytics techniques. Key objectives include:

Scraping data for a curated selection of Lyon-based restaurants (e.g., Brasserie Georges), including metadata such as location, presentation, services, ratings, and customer reviews.
Structuring and storing this data in a data warehouse designed for advanced analytics.
Conducting intra-restaurant and inter-restaurant analyses, incorporating geographic dimensions and potentially augmenting with open data (e.g., geographic proximity, socioeconomic factors, transportation, etc.).
Performing NLP-driven sentiment analysis and exploring relationships between customer comments, ratings, and restaurant attributes.
Building an interactive Python-based web application (e.g., Dash, Streamlit, or Bokeh) for dynamic data exploration and analysis, allowing new restaurants to be seamlessly added to the study.
This project integrates web scraping (BeautifulSoup, Selenium), geographic visualization, and dynamic data-driven dashboards while ensuring seamless deployment through Docker."

## **Structure du projet** :

```plaintext
TripAdvisor-NLP-Analysis/
├── client/
│   ├── interface/           # Interfaces utilisateur (frontend)
│   ├── requirements.txt     # Dépendances spécifiques au client
│   └── app.py               # Point d'entrée pour l'application utilisateur
├── server/
│   ├── app/
│   │   ├── data/            # Répertoire pour les fichiers JSON ou CSV
│   │   ├── requirements.txt # Dépendances spécifiques au serveur
│   │   ├── main.py          # Point d'entrée pour l'API backend
│   │   ├── model/           # Définition des modèles de données
│   │   ├── utils/           # Fonctions utilitaires
│   │   └── schemas.py       # Validation des schémas de données
├── requirements.txt         # Liste globale des dépendances Python
└── docker-compose.yml       # Configuration Docker pour orchestrer les services
```

 
## **Clonage et démarrage du projet** :

### 1. **Cloner le projet :**
```bash
git clone https://github.com/Linn2d/TripAdvisor-NLP-Analysis.git
cd TripAdvisor-NLP-Analysis
```
 

### 2. **Installation avec Conda :**

#### Étape 1 : Créer un environnement virtuel
```bash
conda create -n tripAdvisorNLP python=3.9
conda activate tripAdvisorNLP
cd client
```

#### Étape 2 : Installer les dépendances
```bash
pip install -r requirements.txt
```

#### Étape 3 : Lancer le serveur
```bash
uvicorn server.app.main:app --reload --host 0.0.0.0 --port 8000
```
 
#### Étape 4 : Lancer le client
```bash
streamlit  run  app.py
```
### 3. **Installation avec Docker :**

#### Étape 1 : Construire et démarrer les services Docker
```bash
docker-compose up --build
```

#### Étape 2 : Accéder à l’application
- **Backend API** : [http://localhost:8000](http://localhost:8000)  
- **Interface utilisateur** : [http://localhost:8501](http://localhost:8501)

 