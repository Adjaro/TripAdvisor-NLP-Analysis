import streamlit as st
import pandas as pd
import numpy as np
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from typing import List, Dict, Tuple
from sklearn.manifold import TSNE
import plotly.graph_objects as go
from gensim.models import Word2Vec
from nrclex import NRCLex
import os
import string
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob
from textblob_fr import PatternTagger, PatternAnalyzer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from manager import get_db, read_review, read_restaurant, read_date

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Initialize constants
ponctuations = list(string.punctuation)
chiffres = list("0123456789")
mots_vides = stopwords.words("french")
mots_vides.extend(['très', 'avon', 'plu'])
lem = WordNetLemmatizer()

# Define emotion mapping
emotion_mapping = {
    "anger": "colère",
    "anticipation": "anticipation",
    "disgust": "dégoût",
    "fear": "peur",
    "joy": "joie",
    "sadness": "tristesse",
    "surprise": "surprise",
    "trust": "confiance"
}

# Optimize data loading
@st.cache_data(ttl=3600)
def load_data(_db) -> pd.DataFrame:
    try:
        return pd.merge(
            pd.merge(
                read_restaurant(db=_db, limit=100000),
                read_review(db=_db, limit=100000),
                on='id_restaurant'
            ),
            read_date(db=_db, limit=100000),
            on='id_date'
        )
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Optimize text processing
@lru_cache(maxsize=1000)
def nettoyage_doc(doc_param: str) -> List[str]:
    doc = doc_param.lower()
    doc = doc.replace("\n", " ")
    exclude = set(ponctuations + chiffres)
    doc = "".join(c for c in doc if c not in exclude)
    doc = word_tokenize(doc)
    doc = [lem.lemmatize(terme, pos=wordnet.VERB) for terme in doc]
    stop_words = set(mots_vides)
    doc = [w for w in doc if w not in stop_words and len(w) >= 3]
    return doc

# Parallel corpus processing
def process_corpus_chunk(chunk: List[str]) -> List[List[str]]:
    return [nettoyage_doc(doc) for doc in chunk if len(doc) > 0]

def nettoyage_corpus_parallel(corpus: List[str], vire_vide: bool = True) -> List[List[str]]:
    if not corpus:
        return []
    
    n_cores = multiprocessing.cpu_count()
    chunk_size = max(1, len(corpus) // n_cores)
    chunks = [corpus[i:i + chunk_size] for i in range(0, len(corpus), chunk_size)]
    
    with ThreadPoolExecutor(max_workers=n_cores) as executor:
        results = list(executor.map(process_corpus_chunk, chunks))
    
    return [item for sublist in results for item in sublist]

# Optimize Word2Vec model loading
@st.cache_resource
def get_word2vec_model(corpus: List[List[str]], model_path: str = "word2vec_reviews.model") -> Word2Vec:
    if os.path.exists(model_path):
        return Word2Vec.load(model_path)
    
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

# Optimize emotion calculation
@st.cache_data
def calculer_emotions_batch(texts: List[str], batch_size: int = 100) -> pd.DataFrame:
    emotions_totales = {}
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for texte in batch:
            emotion_obj = NRCLex(texte)
            for emotion, score in emotion_obj.top_emotions:
                emotion_fr = emotion_mapping.get(emotion, emotion.capitalize())
                emotions_totales[emotion_fr] = emotions_totales.get(emotion_fr, 0) + score
    
    df_emotions = pd.DataFrame(sorted(emotions_totales.items(), 
                                    key=lambda x: x[1], 
                                    reverse=True),
                             columns=['Émotion', 'Score'])
    return df_emotions.set_index('Émotion')

# Define sentiment analysis function
def sentiment_textblob_fr(text: str) -> float:
    blob = TextBlob(text, pos_tagger=PatternTagger(), analyzer=PatternAnalyzer())
    return blob.sentiment[0]

def label_sentiment(polarity: float) -> str:
    if polarity > 0:
        return "positif"
    elif polarity < 0:
        return "négatif"
    else:
        return "neutre"

def show():
    st.title("Analyse NLP")

    db = next(get_db())
    reviews_df = load_data(_db=db)
    db.close()

    global_corpus = reviews_df['review'].astype(str).tolist()
    global_corpus_nettoye = nettoyage_corpus_parallel(global_corpus)
    global_corpus_final = [" ".join(doc) for doc in global_corpus_nettoye]

    df_emotions = calculer_emotions_batch(global_corpus_final)

    columns = ['nom','date','review','nb_etoiles']
    data = reviews_df[columns]

    restaurant_names = data['nom'].unique().tolist()
    selected_restaurant = st.selectbox("Choisissez un restaurant :", restaurant_names)

    filtered_reviews = data[data['nom'] == selected_restaurant].copy()
    col1, col2 = st.columns([1, 4])

    tab1, tab2, tab3, tab4 = st.tabs(["Analyse inter restaurant","WordClouds & Émotions", "Recherche de mots", "Aperçu & Graphique"])

    corpus = filtered_reviews['review'].astype(str).tolist()
    corpus_nettoye = nettoyage_corpus_parallel(corpus)
    corpus_final = [" ".join(doc) for doc in corpus_nettoye]
    polarities = [sentiment_textblob_fr(text) for text in corpus_final]
    sentiments = [label_sentiment(pol) for pol in polarities]
    model = get_word2vec_model(corpus_nettoye)
    filtered_reviews['sentiment'] = sentiments

    with tab1:
        st.header("Analyse inter restaurant")

        model_all = get_word2vec_model(global_corpus_nettoye)

        restaurant_groups = reviews_df.groupby('nom')['review'].apply(list).reset_index()

        restaurant_names = []
        restaurant_vectors = []
        for _, row in restaurant_groups.iterrows():
            nom = row['nom']
            avis = row['review']
            tokens = nettoyage_corpus_parallel(avis)
            tokens = [mot for doc in tokens for mot in doc if mot in model_all.wv.key_to_index]
            
            if tokens:
                word_vectors = [model_all.wv[mot] for mot in tokens]
                mean_vector = np.mean(word_vectors, axis=0)
                restaurant_names.append(nom)
                restaurant_vectors.append(mean_vector)

        if restaurant_vectors:
            restaurant_vectors_np = np.array(restaurant_vectors)
            perplexity_value = min(30, len(restaurant_vectors_np) - 1)

            tsne = TSNE(n_components=3, random_state=42, perplexity=perplexity_value)
            vectors_3d = tsne.fit_transform(restaurant_vectors_np)
            
            fig = go.Figure(data=[go.Scatter3d(
                x=vectors_3d[:, 0],
                y=vectors_3d[:, 1],
                z=vectors_3d[:, 2],
                mode='markers+text',
                text=restaurant_names,
                textposition="top center",
                marker=dict(
                    size=5,
                    color=vectors_3d[:, 2],
                    colorscale='Viridis',
                    opacity=0.8
                )
            )])

            fig.update_layout(
                title="Proximité inter restaurant basée sur Word2Vec et t-SNE",
                scene=dict(
                    xaxis_title='Dimension 1',
                    yaxis_title='Dimension 2',
                    zaxis_title='Dimension 3'
                ),
                width=1000,
                height=800
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun restaurant avec des données suffisantes pour la visualisation.")

    with tab2:
        st.header("WordClouds pour les avis positifs et négatifs")
        global_negatifs = reviews_df[reviews_df['nb_etoiles'].isin([1, 2])]
        global_positifs = reviews_df[reviews_df['nb_etoiles'].isin([4, 5])]

        negatifs_nettoyes = nettoyage_corpus_parallel(global_negatifs['review'].astype(str).tolist(), vire_vide=False)
        positifs_nettoyes = nettoyage_corpus_parallel(global_positifs['review'].astype(str).tolist(), vire_vide=False)

        texte_negatif = " ".join([" ".join(doc) for doc in negatifs_nettoyes])
        texte_positif = " ".join([" ".join(doc) for doc in positifs_nettoyes])

        stopwords_wc = set(WordCloud().stopwords)
        stopwords_wc.update(["tres", "très", "plu", "plus", "avon", "comme","cest", "restaurant","donc","alors","nest","foi"])

        wordcloud_negatif = WordCloud(
            stopwords=stopwords_wc,
            max_words=80,
            width=400,
            height=200,
        ).generate(texte_negatif if texte_negatif.strip() else "vide")

        wordcloud_positif = WordCloud(
            stopwords=stopwords_wc,
            max_words=80,
            width=400,
            height=200,
        ).generate(texte_positif if texte_positif.strip() else "vide")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("WordCloud - Notes 1 & 2")
            if texte_negatif.strip():
                fig_neg, ax_neg = plt.subplots(figsize=(4, 2), dpi=100)
                ax_neg.imshow(wordcloud_negatif, interpolation='bilinear')
                ax_neg.axis("off")
                plt.tight_layout()
                st.pyplot(fig_neg)
            else:
                st.info("Aucun commentaire pour les notes 1 & 2.")

        with col2:
            st.subheader("WordCloud - Notes 4 & 5")
            if texte_positif.strip():
                fig_pos, ax_pos = plt.subplots(figsize=(4, 2), dpi=100)
                ax_pos.imshow(wordcloud_positif, interpolation='bilinear')
                ax_pos.axis("off")
                plt.tight_layout()
                st.pyplot(fig_pos)
            else:
                st.info("Aucun commentaire pour les notes 4 & 5.")    
            
        st.subheader("Émotions globales pour l'ensemble des commentaires")
        st.table(df_emotions)

    with tab3:
        st.header("Recherche de mots similaires avec Word2Vec")
        mot_recherche = st.text_input("Entrez un mot pour trouver des mots similaires :", value="parfait")
        
        if mot_recherche:
            if mot_recherche in model.wv.key_to_index:
                nb_resultats = st.slider("Nombre de mots à afficher :", 1, 20, 10)

                similarites = [
                    (mot, model.wv.similarity(mot_recherche, mot))
                    for mot in model.wv.key_to_index
                    if mot != mot_recherche
                ]

                df_similarites = pd.DataFrame(similarites, columns=["Mot", "Score"]).set_index("Mot")
                df_similarites = df_similarites.sort_values(by="Score", ascending=False)

                meilleurs_scores = df_similarites.head(nb_resultats)
                pires_scores = df_similarites.tail(nb_resultats)

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Mots les plus proches")
                    st.table(meilleurs_scores.style.format({"Score": "{:.4f}"}))

                with col2:
                    st.subheader("Mots les moins proches")
                    st.table(pires_scores.style.format({"Score": "{:.4f}"}))
            else:
                st.warning(f"Le mot '{mot_recherche}' n'est pas dans le vocabulaire du modèle Word2Vec.")

    with tab4:
        st.header("Aperçu des commentaires et évolution mensuelle")

        if filtered_reviews['date'].dtype == 'O':
            filtered_reviews['date'] = pd.to_datetime(filtered_reviews['date'])

        filtered_reviews = filtered_reviews.sort_values(by='date', ascending=False)
        filtered_reviews['date'] = filtered_reviews['date'].dt.date

        st.dataframe(filtered_reviews.reset_index(drop=True))

        buffer = io.BytesIO()
        filtered_reviews.to_csv(buffer, index=False, sep=";", encoding="utf-8-sig")
        buffer.seek(0)
        st.download_button(
            label="Télécharger les commentaires",
            data=buffer.getvalue(),
            file_name="commentaires.csv",
            mime="text/csv"
        )

        if filtered_reviews['date'].dtype == 'O':
            filtered_reviews['date'] = pd.to_datetime(filtered_reviews['date'])

        sentiments_mensuels = (
            filtered_reviews.groupby([filtered_reviews['date'].dt.to_period('M'), 'sentiment'])
            .size()
            .unstack(fill_value=0)
        )

        sentiments_mensuels.index = sentiments_mensuels.index.astype(str)
        st.line_chart(sentiments_mensuels)