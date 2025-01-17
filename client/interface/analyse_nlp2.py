import streamlit as st
import pandas as pd
from manager import get_db, read_review, read_restaurant, read_date

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
    

@st.cache_data(show_spinner=False)
def calculer_emotions(corpus_final):
    emotions_totales = {}
    for texte in corpus_final:
        emotion_obj = NRCLex(texte)
        for emotion, score in emotion_obj.top_emotions:
            emotions_totales[emotion] = emotions_totales.get(emotion, 0) + score
    emotions_triees = sorted(emotions_totales.items(), key=lambda x: x[1], reverse=True)
    df_emotions = pd.DataFrame(emotions_triees, columns=['Émotion', 'Score'])
    df_emotions['Émotion'] = df_emotions['Émotion'].str.capitalize()
    df_emotions.set_index('Émotion', inplace=True)
    return df_emotions

@st.cache_data(show_spinner=False)
def calculer_sentiments_mensuels(df):
    # Calculer les sentiments pour chaque avis
    df['polarity'] = df['review'].apply(sentiment_textblob_fr)
    df['sentiment'] = df['polarity'].apply(label_sentiment)
    
    # Créer une colonne combinant année et mois pour le groupement temporel
    df['annee_mois'] = df['annee'].astype(str) + "-" + df['mois'].astype(str).str.zfill(2)
    
    # Grouper par année_mois et sentiment, puis compter les occurrences
    monthly_counts = df.groupby(['annee_mois', 'sentiment']).size().unstack(fill_value=0).sort_index()
    return monthly_counts


def show():
    st.title("Analyse NLP")

    db = next(get_db())
    try:
        reviews_df = pd.merge(
            pd.merge(
                read_restaurant(db=db, limit=100000),
                read_review(db=db, limit=100000),
                on='id_restaurant'
            ),
            read_date(db=db, limit=100000),
            on='id_date'
)
    finally:
        db.close()


        # Après avoir chargé reviews_df complet
    global_corpus = reviews_df['review'].astype(str).tolist()
    global_corpus_nettoye = nettoyage_corpus(global_corpus)
    global_corpus_final = [" ".join(doc) for doc in global_corpus_nettoye]
    df_emotions = calculer_emotions(global_corpus_final)
    df_emotions_styled = df_emotions.style.format({'Score': '{:.2f}'})

    #st.dataframe(reviews_df2.head())
    columns = ['nom','date','review','nb_etoiles']
    data = reviews_df[columns]


    # Calculer les émotions globales une seule fois et mettre en cache
    df_emotions = calculer_emotions(global_corpus_final)

    #st.dataframe(reviews_df)

    restaurant_names = reviews_df['nom'].unique().tolist()
    selected_restaurant = st.selectbox("Choisissez un restaurant :", restaurant_names)

    filtered_reviews = data[reviews_df['nom'] == selected_restaurant].copy()
    
     # -- Ajout du filtre sur les notes (1 à 5)
    possible_notes = sorted(filtered_reviews['nb_etoiles'].unique())
    selected_notes = st.multiselect(
        "Filtrer par note(s) :", possible_notes
    )

     # Filtrer sur les notes choisies
    filtered_reviews = filtered_reviews[filtered_reviews['nb_etoiles'].isin(selected_notes)]
    filtered_reviews = filtered_reviews[columns].reset_index(drop=True)
    

    # Nettoyage et calcul de la polarité
    corpus = filtered_reviews['review'].astype(str).tolist()
    corpus_nettoye = nettoyage_corpus(corpus)
    corpus_final = [" ".join(doc) for doc in corpus_nettoye]

    polarities = [sentiment_textblob_fr(text) for text in corpus_final]
    
    # Convertir la polarité numérique en label (positif/negatif)
    sentiments = [label_sentiment(pol) for pol in polarities]

    # Ajouter au DataFrame
    #filtered_reviews['review_clean'] = corpus_final
    #filtered_reviews['polarity'] = polarities
    filtered_reviews['sentiment'] = sentiments

        #Affichage commentaires & dates
    st.dataframe(filtered_reviews)

    # st.subheader(f"Commentaires pour {selected_restaurant}")
    # colonnes_affichage = ['review', 'nb_etoiles', 'polarity', 'sentiment']
    # df_pour_affichage = filtered_reviews[colonnes_affichage].reset_index(drop=True)
    # st.dataframe(df_pour_affichage)

    # # -- Création des textes pour chaque sentiment
    # # Positif
    # positif_text = " ".join(
    #     filtered_reviews.loc[filtered_reviews['sentiment'] == 'Positif', 'review_clean']
    # )
    # # Négatif
    # negatif_text = " ".join(
    #     filtered_reviews.loc[filtered_reviews['sentiment'] == 'Négatif', 'review_clean']
    # )

# --- Section 3 : WordClouds globaux pour notes 1&2 et 4&5 ---

    st.header("WordClouds pour les avis postifs et négatifs")

    # Filtrer les commentaires par notes
    global_negatifs = reviews_df[reviews_df['nb_etoiles'].isin([1, 2])]
    global_positifs = reviews_df[reviews_df['nb_etoiles'].isin([4, 5])]

    # Nettoyage et applatissage des textes pour chaque groupe
    negatifs_nettoyes = nettoyage_corpus(global_negatifs['review'].astype(str).tolist(), vire_vide=False)
    positifs_nettoyes = nettoyage_corpus(global_positifs['review'].astype(str).tolist(), vire_vide=False)

    texte_negatif = " ".join([" ".join(doc) for doc in negatifs_nettoyes])
    texte_positif = " ".join([" ".join(doc) for doc in positifs_nettoyes])

      # 1) On récupère les stopwords par défaut de WordCloud
    stopwords_wc = set(WordCloud().stopwords)
    # 2) On y ajoute nos mots spécifiques
    stopwords_wc.update(["tres", "très", "plu", "plus", "avon", "comme","cest", "restaurant","donc","alors","nest","foi"])

    # Générer les WordClouds
    wordcloud_negatif = WordCloud(
        background_color='white',
        stopwords=stopwords_wc,
        max_words=80,
        width=400,
        height=200,
    ).generate(texte_negatif if texte_negatif.strip() else "vide")

    wordcloud_positif = WordCloud(
        background_color='white',
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


    #Evolution des sentiments
    # Calcul des sentiments mensuels globaux en tenant compte de l'année et du mois
    monthly_counts = calculer_sentiments_mensuels(reviews_df)

    # Extraire les années disponibles
    available_years = sorted(reviews_df['annee'].unique())

    # Définir 2024 comme l'année par défaut si elle est présente, sinon prendre la première année
    default_year_index = available_years.index(2024) if 2024 in available_years else 0

    # Ajouter un filtre sur l'année
    selected_year = st.selectbox(
        "Choisissez une année pour le graphique :",
        available_years,
        index=default_year_index  # Sélectionne 2024 par défaut si disponible
    )

    # Filtrer les données mensuelles pour l'année sélectionnée
    if selected_year:
        filtered_monthly_counts = monthly_counts.loc[monthly_counts.index.str.startswith(str(selected_year))]

        st.subheader(f"Évolution mensuelle des sentiments en {selected_year}")
        
        # Vérifier que les colonnes 'Positif' et 'Négatif' existent
        columns_to_plot = []
        if 'Positif' in filtered_monthly_counts.columns:
            columns_to_plot.append('Positif')
        if 'Négatif' in filtered_monthly_counts.columns:
            columns_to_plot.append('Négatif')

        if not filtered_monthly_counts.empty and columns_to_plot:
            st.line_chart(filtered_monthly_counts[columns_to_plot])
        else:
            st.info("Aucune donnée disponible pour l'année sélectionnée.")

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


    # # 3) Création d'un seul WordCloud à partir des commentaires filtrés
    # corpus = filtered_reviews['review'].astype(str).tolist()
    # corpus_nettoye = nettoyage_corpus(corpus)

    # # On transforme la liste de listes en un seul gros string
    # text_for_wordcloud = " ".join([" ".join(doc) for doc in corpus_nettoye])

    # if not text_for_wordcloud.strip():
    #     # S’il n’y a aucun mot dans le texte, on affiche un message
    #     st.info("Aucun avis selectionné.")
    # else:
    #     # Stopwords personnalisés
    #     stopwords_wc = set(WordCloud().stopwords)
    #     stopwords_wc.update(["tres", "très", "plu", "plus", "avon", "comme", "restaurant", "lyon"])

    #     # Génération du WordCloud
    #     wordcloud = WordCloud(
    #         background_color='white',
    #         stopwords=stopwords_wc,
    #         max_words=80,
    #         width=400,      # Largeur du canvas du WordCloud
    #         height=200,     # Hauteur du canvas du WordCloud
    #     ).generate(text_for_wordcloud)

    #     # 4) Affichage dans Streamlit
    #     st.subheader("WordCloud")
    #     fig, ax = plt.subplots(figsize=(3, 2), dpi=100)
    #     ax.imshow(wordcloud, interpolation='bilinear')
    #     ax.axis("off")
    #     plt.tight_layout()
        
    #     st.pyplot(fig)


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
        if mot_recherche in model.wv.key_to_index:
            nb_resultats = st.slider("Nombre de résultats :", 1, 20, 5)
            similaires = model.wv.most_similar(mot_recherche, topn=nb_resultats)
            
            # Créer un DataFrame pour les résultats
            df_similaires = pd.DataFrame(similaires, columns=["Mot", "Score de similarité"])
            # Définir la colonne "Mot" comme index pour un affichage plus épuré
            df_similaires.set_index("Mot", inplace=True)
            # Styliser le DataFrame pour formater les scores
            df_styled = df_similaires.style.format({"Score de similarité": "{:.4f}"})
            
            # Afficher le tableau épuré
            st.table(df_styled)
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
    # ...
    st.subheader("Émotions globales pour l'ensemble des commentaires")
    st.table(df_emotions_styled)