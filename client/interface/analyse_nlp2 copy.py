import streamlit as st
import pandas as pd
from manager import get_db, read_review, read_restaurant, read_date
import List
#A ajouter dans requirements
import string
import nltk
nltk.download('punkt')
nltk.download('stopwords')
ponctuations = list(string.punctuation)
chiffres = list("0123456789")
from nltk.corpus import stopwords
mots_vides = stopwords.words("french")
mots_vides.append('très')
mots_vides.append('avon')
mots_vides.append('plu')


import io 
#pour la tokénisation
from nltk.tokenize import word_tokenize
#lem
from nltk.stem import WordNetLemmatizer
lem = WordNetLemmatizer()
from textblob_fr import PatternTagger, PatternAnalyzer
from textblob import TextBlob
# from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from gensim.models import Word2Vec
import os
from transformers import pipeline
#from bertopic import BERTopic
from nrclex import NRCLex
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np


# Construire le chemin vers fichier de stopwords
# Déterminer le répertoire du script courant
chemin_actuel = os.path.dirname(__file__)  # Répertoire client/interface
# Construire le chemin vers le fichier stopwords-fr.txt en remontant d'un niveau
chemin_stopwords = os.path.join(chemin_actuel, "..", "stopwords-fr.txt")
# Normaliser le chemin pour éviter les problèmes de syntaxe selon le système d'exploitation
chemin_stopwords = os.path.normpath(chemin_stopwords)
try:
    with open(chemin_stopwords, "r", encoding="utf-8") as f:
        stopwords_local = f.read().splitlines()
        mots_vides.extend(stopwords_local)
except FileNotFoundError:
    print(f"Le fichier {chemin_stopwords} n'a pas été trouvé.")


def nettoyage_doc(doc_param):
    # Passage en minuscule
    doc = doc_param.lower()
    # Retrait des \n
    doc = doc.replace("\n", " ")
    # Retrait des ponctuations
    doc = "".join([w for w in doc if w not in ponctuations])
    # Retirer les chiffres
    doc = "".join([w for w in doc if w not in chiffres])
    # Transformer le document en liste de termes par tokénisation
    doc = word_tokenize(doc)
    # Lemmatisation de chaque terme
    doc = [lem.lemmatize(terme) for terme in doc]
    # Retirer les stopwords
    doc = [w for w in doc if w not in mots_vides]
    # Retirer les termes de moins de 3 caractères
    doc = [w for w in doc if len(w) >= 3]
    # Fin
    return doc

def nettoyage_corpus(corpus,vire_vide=True):
    #output
    output = [nettoyage_doc(doc) for doc in corpus if ((len(doc) > 0) or (vire_vide == False))]
    return output

def sentiment_textblob_fr(text: str):
    """
    Renvoie un score de sentiment (polarity) pour un texte en français.
    Polarity varie en général entre -1 (très négatif) et 1 (très positif).
    """
    blob = TextBlob(text, pos_tagger=PatternTagger(), analyzer=PatternAnalyzer())
    return blob.sentiment[0]  # [0] = polarity, [1] = subjectivity (si disponible)

def label_sentiment(polarity):
    """
    Retourne 'Positif' si la polarité >= 0,
    sinon retourne 'Négatif'.
    """
    if polarity >= 0:
        return "Positif"
    else:
        return "Négatif"
    

@st.cache_data(show_spinner=False)
def calculer_emotions(corpus_final):
    # Dictionnaire de mappage des émotions en anglais vers le français
    emotion_mapping = {
        "positive": "Positif",
        "negative": "Négatif",
        "trust": "Confiance",
        "joy": "Joie",
        "fear": "Peur",
        "sadness": "Tristesse",
        "anger": "Colère",
        "disgust": "Dégoût",
        "surprise": "Surprise",
        "anticipation": "Anticipation"
    }
    
    emotions_totales = {}
    for texte in corpus_final:
        emotion_obj = NRCLex(texte)
        for emotion, score in emotion_obj.top_emotions:
            # Ajoute les scores aux émotions traduites
            emotion_fr = emotion_mapping.get(emotion, emotion.capitalize())  # Par défaut, utilise le mot capitalisé
            emotions_totales[emotion_fr] = emotions_totales.get(emotion_fr, 0) + score
    
    # Trier les émotions par score total
    emotions_triees = sorted(emotions_totales.items(), key=lambda x: x[1], reverse=True)
    
    # Créer un DataFrame
    df_emotions = pd.DataFrame(emotions_triees, columns=['Émotion', 'Score'])
    df_emotions.set_index('Émotion', inplace=True)
    
    return df_emotions

@st.cache_data
def calculer_sentiments_mensuels(df):
    # Calculer les sentiments pour chaque avis
    df['polarity'] = df['review'].apply(sentiment_textblob_fr)
    df['sentiment'] = df['polarity'].apply(label_sentiment)
    
    # Créer une colonne combinant année et mois pour le groupement temporel
    df['annee_mois'] = df['annee'].astype(str) + "-" + df['mois'].astype(str).str.zfill(2)
    
    # Grouper par année_mois et sentiment, puis compter les occurrences
    monthly_counts = df.groupby(['annee_mois', 'sentiment']).size().unstack(fill_value=0).sort_index()
    return monthly_counts


@st.cache_resource
def get_word2vec_model(corpus, model_path="word2vec_reviews.model"):
    # Tente de charger le modèle si le fichier existe
    if os.path.exists(model_path):
        model = Word2Vec.load(model_path)
    else:
        # Sinon, entraîne un nouveau modèle et le sauvegarde
        model = Word2Vec(
            sentences=corpus,
            vector_size=100,
            window=5,
            min_count=1,
            workers=4,
            sg=1
            )
        model.save(model_path)
    return model
    















@st.cache_data
def process_emotions_batch(batch_texts: List[str], batch_size: int = 100) -> pd.DataFrame:
    """Process emotions in batches and show progress"""
    emotions_totales = {}
    progress_bar = st.progress(0)
    
    for i in range(0, len(batch_texts), batch_size):
        current_batch = batch_texts[i:i + batch_size]
        for texte in current_batch:
            emotion_obj = NRCLex(texte)
            for emotion, score in emotion_obj.top_emotions:
                emotion_fr = emotion_mapping.get(emotion, emotion.capitalize())
                emotions_totales[emotion_fr] = emotions_totales.get(emotion_fr, 0) + score
        
        # Update progress
        progress = min((i + batch_size) / len(batch_texts), 1.0)
        progress_bar.progress(progress)
        
        # Show intermediate results
        if i % (batch_size * 5) == 0:
            temp_df = pd.DataFrame(
                sorted(emotions_totales.items(), key=lambda x: x[1], reverse=True),
                columns=['Émotion', 'Score']
            ).set_index('Émotion')
            st.dataframe(temp_df, use_container_width=True)
    
    progress_bar.empty()
    return pd.DataFrame(
        sorted(emotions_totales.items(), key=lambda x: x[1], reverse=True),
        columns=['Émotion', 'Score']
    ).set_index('Émotion')

def process_sentiments_stream(df: pd.DataFrame, chunk_size: int = 1000):
    """Process sentiments in streaming fashion"""
    placeholder = st.empty()
    progress_bar = st.progress(0)
    
    chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
    monthly_counts_list = []
    
    for i, chunk in enumerate(chunks):
        # Process chunk
        chunk['polarity'] = chunk['review'].apply(sentiment_textblob_fr)
        chunk['sentiment'] = chunk['polarity'].apply(label_sentiment)
        chunk['annee_mois'] = chunk['annee'].astype(str) + "-" + chunk['mois'].astype(str).str.zfill(2)
        
        # Calculate monthly counts for chunk
        chunk_counts = chunk.groupby(['annee_mois', 'sentiment']).size().unstack(fill_value=0)
        monthly_counts_list.append(chunk_counts)
        
        # Update progress and display intermediate results
        progress = (i + 1) / len(chunks)
        progress_bar.progress(progress)
        
        if len(monthly_counts_list) > 0:
            current_results = pd.concat(monthly_counts_list).groupby(level=0).sum()
            with placeholder.container():
                st.line_chart(current_results)
    
    progress_bar.empty()
    return pd.concat(monthly_counts_list).groupby(level=0).sum().sort_index()

@st.cache_resource
def get_word2vec_model(corpus, model_path="word2vec_reviews.model"):
    """Load or train Word2Vec model with progress indication"""
    if os.path.exists(model_path):
        return Word2Vec.load(model_path)
    
    with st.spinner('Entraînement du modèle Word2Vec...'):
        model = Word2Vec(
            sentences=corpus,
            vector_size=100,
            window=5,
            min_count=1,
            workers=multiprocessing.cpu_count(),
            sg=1
        )
        model.save(model_path)
    return model


def show():
    st.title("Analyse NLP")
    
    # Load data with progress
    with st.spinner('Chargement des données...'):
        db = next(get_db())
        reviews_df = load_data(_db=db)
        db.close()

    # Initialize tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Analyse inter restaurant",
        "WordClouds & Émotions",
        "Recherche de mots",
        "Aperçu & Graphique"
    ])

    # Process global corpus with progress
    with st.spinner('Traitement du corpus...'):
        global_corpus = reviews_df['review'].astype(str).tolist()
        global_corpus_nettoye = nettoyage_corpus_parallel(global_corpus)
        global_corpus_final = [" ".join(doc) for doc in global_corpus_nettoye]

    # Calculate emotions with caching
    with st.spinner('Analyse des émotions...'):
        df_emotions = calculer_emotions_batch(global_corpus_final)

    # Get restaurant selection
    columns = ['nom', 'date', 'review', 'nb_etoiles']
    data = reviews_df[columns]
    restaurant_names = data['nom'].unique().tolist()
    
    selected_restaurant = st.selectbox(
        "Choisissez un restaurant :",
        restaurant_names
    )

    # Filter reviews
    filtered_reviews = data[data['nom'] == selected_restaurant].copy()

    # Process restaurant specific corpus
    with st.spinner('Analyse du restaurant...'):
        corpus = filtered_reviews['review'].astype(str).tolist()
        corpus_nettoye = nettoyage_corpus_parallel(corpus)
        corpus_final = [" ".join(doc) for doc in corpus_nettoye]
        
        # Calculate sentiments
        polarities = [sentiment_textblob_fr(text) for text in corpus_final]
        sentiments = [label_sentiment(pol) for pol in polarities]
        
        # Get Word2Vec model
        model = get_word2vec_model(corpus_nettoye)
        
        # Add sentiments to DataFrame
        filtered_reviews['sentiment'] = sentiments

    # Show tabs content
    with tab1:
        show_restaurant_analysis(reviews_df, global_corpus_nettoye)

    with tab2:
        show_wordcloud_emotions(reviews_df, df_emotions)

    with tab3:
        show_word_search(model)

    with tab4:
        show_timeline_analysis(filtered_reviews)

def show_restaurant_analysis(reviews_df, global_corpus_nettoye):
    st.header("Analyse inter restaurant")
    
    with st.spinner('Génération de la visualisation...'):
        model_all = get_word2vec_model(global_corpus_nettoye)
        restaurant_vectors = calculate_restaurant_vectors(reviews_df, model_all)
        
        if restaurant_vectors:
            plot_restaurant_visualization(restaurant_vectors)
        else:
            st.info("Aucun restaurant avec des données suffisantes.")

def show_wordcloud_emotions(reviews_df, df_emotions):
    st.header("WordClouds & Émotions")
    
    with st.spinner('Création des nuages de mots...'):
        generate_wordclouds(reviews_df)
        
    st.subheader("Émotions globales")
    st.table(df_emotions)

def show_word_search(model):
    st.header("Recherche de mots similaires")
    
    mot_recherche = st.text_input(
        "Entrez un mot :",
        value="parfait"
    )
    
    if mot_recherche:
        show_similar_words(model, mot_recherche)

def show_timeline_analysis(filtered_reviews):
    st.header("Analyse temporelle")
    
    with st.spinner('Génération du graphique...'):
        if filtered_reviews['date'].dtype == 'O':
            filtered_reviews['date'] = pd.to_datetime(filtered_reviews['date'])
        
        show_sentiment_evolution(filtered_reviews)