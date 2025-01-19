import streamlit as st
import pandas as pd
import string
import nltk
from manager import get_db, read_review, read_restaurant, read_date
from typing import List
import io
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nrclex import NRCLex
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from gensim.models import Word2Vec
import multiprocessing
import numpy as np
from sklearn.manifold import TSNE
import plotly.graph_objects as go
from textblob import TextBlob
from textblob_fr import PatternTagger, PatternAnalyzer
import os

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

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

@st.cache_data
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

def nettoyage_doc(doc_param: str) -> List[str]:
    doc = doc_param.lower().replace("\n", " ")
    exclude = set(ponctuations + chiffres)
    doc = "".join(c for c in doc if c not in exclude)
    doc = word_tokenize(doc)
    doc = [lem.lemmatize(terme) for terme in doc if terme not in mots_vides and len(terme) >= 3]
    return doc

def process_corpus_chunk(chunk: List[str]) -> List[List[str]]:
    return [nettoyage_doc(doc) for doc in chunk if len(doc) > 0]

def nettoyage_corpus_parallel(corpus: List[str], vire_vide: bool = True) -> List[List[str]]:
    if not corpus:
        return []
    
    n_cores = multiprocessing.cpu_count()
    chunk_size = max(1, len(corpus) // n_cores)
    chunks = [corpus[i:i + chunk_size] for i in range(0, len(corpus), chunk_size)]
    
    with multiprocessing.Pool(n_cores) as pool:
        results = pool.map(process_corpus_chunk, chunks)
    
    return [item for sublist in results for item in sublist]

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

@st.cache_data
def calculer_emotions_batch(texts: List[str], batch_size: int = 100) -> pd.DataFrame:
    emotions_totales = {}
    progress_bar = st.progress(0)
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        for texte in batch:
            emotion_obj = NRCLex(texte)
            for emotion, score in emotion_obj.top_emotions:
                emotion_fr = emotion_mapping.get(emotion, emotion.capitalize())
                emotions_totales[emotion_fr] = emotions_totales.get(emotion_fr, 0) + score
        
        progress = min((i + batch_size) / len(texts), 1.0)
        progress_bar.progress(progress)
    
    progress_bar.empty()
    return pd.DataFrame(
        sorted(emotions_totales.items(), key=lambda x: x[1], reverse=True),
        columns=['Émotion', 'Score']
    ).set_index('Émotion')

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
    
    with st.spinner('Chargement des données...'):
        db = next(get_db())
        reviews_df = load_data(_db=db)
        db.close()

    tab1, tab2, tab3, tab4 = st.tabs([
        "Analyse inter restaurant",
        "WordClouds & Émotions",
        "Recherche de mots",
        "Aperçu & Graphique"
    ])

    with st.spinner('Traitement du corpus...'):
        global_corpus = reviews_df['review'].astype(str).tolist()
        global_corpus_nettoye = nettoyage_corpus_parallel(global_corpus)
        global_corpus_final = [" ".join(doc) for doc in global_corpus_nettoye]

    with st.spinner('Analyse des émotions...'):
        df_emotions = calculer_emotions_batch(global_corpus_final)

    columns = ['nom', 'date', 'review', 'nb_etoiles']
    data = reviews_df[columns]
    restaurant_names = data['nom'].unique().tolist()
    
    selected_restaurant = st.selectbox(
        "Choisissez un restaurant :",
        restaurant_names
    )

    filtered_reviews = data[data['nom'] == selected_restaurant].copy()

    with st.spinner('Analyse du restaurant...'):
        corpus = filtered_reviews['review'].astype(str).tolist()
        corpus_nettoye = nettoyage_corpus_parallel(corpus)
        corpus_final = [" ".join(doc) for doc in corpus_nettoye]
        
        polarities = [sentiment_textblob_fr(text) for text in corpus_final]
        sentiments = [label_sentiment(pol) for pol in polarities]
        
        model = get_word2vec_model(corpus_nettoye)
        
        filtered_reviews['sentiment'] = sentiments

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

def calculate_restaurant_vectors(reviews_df, model_all):
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
    
    return restaurant_names, restaurant_vectors

def plot_restaurant_visualization(restaurant_vectors):
    restaurant_names, restaurant_vectors_np = restaurant_vectors
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

def generate_wordclouds(reviews_df):
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

def show_similar_words(model, mot_recherche):
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

def show_sentiment_evolution(filtered_reviews):
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