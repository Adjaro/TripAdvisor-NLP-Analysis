import streamlit as st
import pandas as pd
from manager import get_db, read_review, read_restaurant

#A ajouter dans requirements
import string
import nltk
ponctuations = list(string.punctuation)
chiffres = list("0123456789")
from nltk.corpus import stopwords
mots_vides = stopwords.words("french")
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
    
def show():
    st.title("Analyse NLP")

    db = next(get_db())
    try:
        # Charger et fusionner les données
        reviews_df = pd.merge(
            read_restaurant(db=db, limit=10000),
            read_review(db=db, limit=10000),
            on='id_restaurant'
        )
    finally:
        db.close()

    # Aperçu global
    st.dataframe(reviews_df.head())

    restaurant_names = reviews_df['nom'].unique().tolist()
    selected_restaurant = st.selectbox("Choisissez un restaurant :", restaurant_names)

    filtered_reviews = reviews_df[reviews_df['nom'] == selected_restaurant].copy()
    
    # Nettoyage et calcul de la polarité
    corpus = filtered_reviews['review'].astype(str).tolist()
    corpus_nettoye = nettoyage_corpus(corpus)
    corpus_final = [" ".join(doc) for doc in corpus_nettoye]

    polarities = [sentiment_textblob_fr(text) for text in corpus_final]
    
    # Convertir la polarité numérique en label (positif/negatif/neutre)
    sentiments = [label_sentiment(pol) for pol in polarities]

    # Ajouter au DataFrame
    filtered_reviews['review_clean'] = corpus_final
    filtered_reviews['polarity'] = polarities
    filtered_reviews['sentiment'] = sentiments

    

    st.subheader(f"Commentaires pour {selected_restaurant}")
    st.dataframe(filtered_reviews[['nom', 'review','sentiment']])

    # -- Création des textes pour chaque sentiment
    # Positif
    positif_text = " ".join(
        filtered_reviews.loc[filtered_reviews['sentiment'] == 'Positif', 'review_clean']
    )
    # Négatif
    negatif_text = " ".join(
        filtered_reviews.loc[filtered_reviews['sentiment'] == 'Négatif', 'review_clean']
    )

        # 1) On récupère les stopwords par défaut de WordCloud
    stopwords_wc = set(WordCloud().stopwords)
    # 2) On y ajoute nos mots spécifiques
    stopwords_wc.update(["tres", "très", "plu", "plus", "avon", "comme",])

    # -- Générer deux wordclouds --
    # WordCloud pour les avis positifs
    wordcloud_pos = WordCloud(
        background_color='white',
        max_words=80,
        colormap='Greens',
        stopwords=stopwords_wc
    ).generate(positif_text if positif_text else "vide")

    # WordCloud pour les avis négatifs
    wordcloud_neg = WordCloud(
        background_color='white',
        max_words=80,
        colormap='Reds',
        stopwords=stopwords_wc
    ).generate(negatif_text if negatif_text else "vide")

    # -- Affichage côte à côte --
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("WordCloud - Avis Positifs")
        fig_pos, ax_pos = plt.subplots()
        ax_pos.imshow(wordcloud_pos, interpolation='bilinear')
        ax_pos.axis("off")
        st.pyplot(fig_pos)

    with col2:
        st.subheader("WordCloud - Avis Négatifs")
        fig_neg, ax_neg = plt.subplots()
        ax_neg.imshow(wordcloud_neg, interpolation='bilinear')
        ax_neg.axis("off")
        st.pyplot(fig_neg)

