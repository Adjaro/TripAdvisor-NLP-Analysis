import streamlit as st
import pandas as pd
from manager import get_db, read_review, read_restaurant

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
import gensim
from gensim.models import Word2Vec
import os
from transformers import pipeline
from gensim import corpora
from bertopic import BERTopic
from nrclex import NRCLex
from collections import Counter

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
            read_restaurant(db=db, limit=100000000),
            read_review(db=db, limit=100000000),
            on='id_restaurant'
        )
    finally:
        db.close()

    restaurant_names = reviews_df['nom'].unique().tolist()
    selected_restaurant = st.selectbox("Choisissez un restaurant :", restaurant_names)

    filtered_reviews = reviews_df[reviews_df['nom'] == selected_restaurant].copy()
    
     # -- Ajout du filtre sur les notes (1 à 5)
    possible_notes = sorted(filtered_reviews['nb_etoiles'].unique())
    selected_notes = st.multiselect(
        "Filtrer par note(s) :", possible_notes
    )

     # Filtrer sur les notes choisies
    filtered_reviews = filtered_reviews[filtered_reviews['nb_etoiles'].isin(selected_notes)]


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
    colonnes_affichage = ['review', 'nb_etoiles', 'polarity', 'sentiment']
    df_pour_affichage = filtered_reviews[colonnes_affichage].reset_index(drop=True)
    st.dataframe(df_pour_affichage)

    # # -- Création des textes pour chaque sentiment
    # # Positif
    # positif_text = " ".join(
    #     filtered_reviews.loc[filtered_reviews['sentiment'] == 'Positif', 'review_clean']
    # )
    # # Négatif
    # negatif_text = " ".join(
    #     filtered_reviews.loc[filtered_reviews['sentiment'] == 'Négatif', 'review_clean']
    # )

    #     # 1) On récupère les stopwords par défaut de WordCloud
    # stopwords_wc = set(WordCloud().stopwords)
    # # 2) On y ajoute nos mots spécifiques
    # stopwords_wc.update(["tres", "très", "plu", "plus", "avon", "comme",])

    # # -- Générer deux wordclouds --
    # # WordCloud pour les avis positifs
    # wordcloud_pos = WordCloud(
    #     background_color='white',
    #     max_words=80,
    #     colormap='Greens',
    #     stopwords=stopwords_wc
    # ).generate(positif_text if positif_text else "vide")

    # # WordCloud pour les avis négatifs
    # wordcloud_neg = WordCloud(
    #     background_color='white',
    #     max_words=80,
    #     colormap='Reds',
    #     stopwords=stopwords_wc
    # ).generate(negatif_text if negatif_text else "vide")

    # # -- Affichage côte à côte --
    # col1, col2 = st.columns(2)

    # with col1:
    #     st.subheader("WordCloud - Avis Positifs")
    #     fig_pos, ax_pos = plt.subplots()
    #     ax_pos.imshow(wordcloud_pos, interpolation='bilinear')
    #     ax_pos.axis("off")
    #     st.pyplot(fig_pos)

    # with col2:
    #     st.subheader("WordCloud - Avis Négatifs")
    #     fig_neg, ax_neg = plt.subplots()
    #     ax_neg.imshow(wordcloud_neg, interpolation='bilinear')
    #     ax_neg.axis("off")
    #     st.pyplot(fig_neg)


    # 3) Création d'un seul WordCloud à partir des commentaires filtrés
    corpus = filtered_reviews['review'].astype(str).tolist()
    corpus_nettoye = nettoyage_corpus(corpus)

    # On transforme la liste de listes en un seul gros string
    text_for_wordcloud = " ".join([" ".join(doc) for doc in corpus_nettoye])

    if not text_for_wordcloud.strip():
        # S’il n’y a aucun mot dans le texte, on affiche un message
        st.info("Aucun avis selectionné.")
    else:
        # Stopwords personnalisés
        stopwords_wc = set(WordCloud().stopwords)
        stopwords_wc.update(["tres", "très", "plu", "plus", "avon", "comme", "restaurant", "lyon"])

        # Génération du WordCloud
        wordcloud = WordCloud(
            background_color='white',
            stopwords=stopwords_wc,
            max_words=80,
            width=400,      # Largeur du canvas du WordCloud
            height=200,     # Hauteur du canvas du WordCloud
        ).generate(text_for_wordcloud)

        # 4) Affichage dans Streamlit
        st.subheader("WordCloud")
        fig, ax = plt.subplots(figsize=(3, 2), dpi=100)
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        plt.tight_layout()
        
        st.pyplot(fig)


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

    # Plus tard dans votre code, pour obtenir le modèle :
    model = get_word2vec_model(corpus_nettoye)

    st.title("Recherche de mots similaires avec Word2Vec")

    # Saisie utilisateur pour le mot de recherche
    mot_recherche = st.text_input("Entrez un mot pour trouver des mots similaires :", value="service")
    # Affichage des mots similaires
    if mot_recherche:
        # Vérifier si le mot est dans le vocabulaire du modèle
        if mot_recherche in model.wv.key_to_index:
            nb_resultats = st.slider("Nombre de résultats :", 1, 20, 5)
            similaires = model.wv.most_similar(mot_recherche, topn=nb_resultats)
            st.write(f"Mots similaires à '{mot_recherche}':")
            for mot, score in similaires:
                st.write(f"- {mot}: {score:.4f}")
        else:
            st.warning(f"Le mot '{mot_recherche}' n'est pas dans le vocabulaire du modèle Word2Vec.")

    

    # # Créer et ajuster le modèle
    # topic_model = BERTopic(language="french")  # Spécifiez la langue si nécessaire
    # topics, probs = topic_model.fit_transform(corpus_final)  # corpus_final : vos textes nettoyés

    # # Voir les thèmes
    # topic_info = topic_model.get_topic_info()
    # st.write(topic_info)

    # # Pour chaque sujet, afficher les mots principaux
    # for topic_id in topic_info.Topic:
    #     st.write(f"Thème {topic_id}: {topic_model.get_topic(topic_id)}")

    # st.header("Thèmes et leurs 5 mots associés")

    # # Récupérer les informations sur les sujets
    # topic_info = topic_model.get_topic_info()

    # # Filtrer pour exclure le thème -1 et sélectionner les 5 premiers thèmes
    # valid_topics = topic_info[topic_info.Topic != -1].head(5)

    # for _, row in valid_topics.iterrows():
    #     topic_id = row['Topic']
    #     # Obtenir les mots clés et leurs poids pour le sujet
    #     topic_words = topic_model.get_topic(topic_id)
    #     if not topic_words:
    #         continue  # Si aucun mot n'est trouvé, passer au suivant
        
    #     # Limiter à 5 mots
    #     top_words = topic_words[:5]
        
    #     # Décomposer en deux listes : mots et scores
    #     mots = [word for word, _ in top_words]
    #     scores = [score for _, score in top_words]
        
    #     st.subheader(f"Thème {topic_id}")
    #     st.write(f"Top 5 Mots clés : {', '.join(mots)}")
        
    #     # Création du graphique en barres pour ce sujet
    #     fig, ax = plt.subplots()
    #     ax.barh(mots, scores, color="skyblue")
    #     ax.invert_yaxis()  # Afficher le mot le plus important en haut
    #     ax.set_xlabel("Poids")
    #     ax.set_title(f"Mots clés du Thème {topic_id}")
        
    #     st.pyplot(fig)

        # Supposons que 'corpus_final' est une liste de commentaires nettoyés
    emotions_totales = {}

    for texte in corpus_final:
        emotion_obj = NRCLex(texte)
        # Ajouter ou cumuler les scores d'émotion
        for emotion, score in emotion_obj.top_emotions:
            emotions_totales[emotion] = emotions_totales.get(emotion, 0) + score

    # Trier les émotions par score total
    emotions_triees = sorted(emotions_totales.items(), key=lambda x: x[1], reverse=True)

    st.write("Émotions globales pour l'ensemble des commentaires :")
    for emotion, score in emotions_triees:
        st.write(f"- {emotion.capitalize()}: {score:.2f}")