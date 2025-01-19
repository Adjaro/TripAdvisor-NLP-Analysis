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

def load_css():
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .title-container {
            background: linear-gradient(to right, #1e3c72, #2a5298);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
        }
        .feature-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin: 1rem 0;
        }
        .team-card {
            text-align: center;
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stat-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)



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
    

def show():
    
    # st.title("Analyse NLP")
    st.markdown("""
        <div class='title-container'>
            <h1> ☁️ Analyse NLP</h1>    
        </div>
    """, unsafe_allow_html=True)

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
    #df_emotions_styled = df_emotions.style.format({'Score': '{:.2f}'})

    #st.dataframe(reviews_df2.head())
    columns = ['nom','date','review','nb_etoiles']
    data = reviews_df[columns]

        # Filtre sous le titre
    restaurant_names = data['nom'].unique().tolist()
    selected_restaurant = st.selectbox("Choisissez un restaurant à analyser :", restaurant_names)

    # Filtrer les avis en fonction du restaurant sélectionné
    filtered_reviews = data[data['nom'] == selected_restaurant].copy()
    # Disposition avec colonne pour le filtre et onglets à droite
    col1, col2 = st.columns([1, 4])

    #st.dataframe(reviews_df)


    tab1, tab2, tab3, tab4 = st.tabs(["Analyse inter restaurant","WordClouds & Émotions", "Recherche de mots", "Aperçu & Graphique"])
    
    #  # -- Ajout du filtre sur les notes (1 à 5)
    # possible_notes = sorted(filtered_reviews['nb_etoiles'].unique())
    # selected_notes = st.multiselect(
    #     "Filtrer par note(s) :", possible_notes
    # )

    #  # Filtrer sur les notes choisies
    # filtered_reviews = filtered_reviews[filtered_reviews['nb_etoiles'].isin(selected_notes)]
    # filtered_reviews = filtered_reviews[columns].reset_index(drop=True)
    
    # Nettoyage et calcul de la polarité
    
    corpus = filtered_reviews['review'].astype(str).tolist()
    corpus_nettoye = nettoyage_corpus(corpus)
    corpus_final = [" ".join(doc) for doc in corpus_nettoye]
    polarities = [sentiment_textblob_fr(text) for text in corpus_final]
    # Convertir la polarité numérique en label (positif/negatif)
    sentiments = [label_sentiment(pol) for pol in polarities]
    # Plus tard dans votre code, pour obtenir le modèle :
    model = get_word2vec_model(corpus_nettoye)
    # Ajouter au DataFrame
    #filtered_reviews['review_clean'] = corpus_final
    #filtered_reviews['polarity'] = polarities
    filtered_reviews['sentiment'] = sentiments


    
    with tab1:
        st.header("Analyse globale inter restaurant")


    # Charger le modèle Word2Vec global
        model_all = get_word2vec_model(global_corpus_nettoye)

        # Regrouper les avis par restaurant
        restaurant_groups = reviews_df.groupby('nom')['review'].apply(list).reset_index()

        restaurant_names = []
        restaurant_vectors = []
        # Calcul des vecteurs moyens par restaurant
        for _, row in restaurant_groups.iterrows():
            nom = row['nom']
            avis = row['review']
            # Nettoyer et tokeniser les avis
            tokens = nettoyage_corpus(avis)
            # Filtrer les tokens présents dans le vocabulaire Word2Vec
            tokens = [mot for doc in tokens for mot in doc if mot in model_all.wv.key_to_index]
            
            if tokens:
                # Calculer la moyenne des vecteurs de mots pour le restaurant
                word_vectors = [model_all.wv[mot] for mot in tokens]
                mean_vector = np.mean(word_vectors, axis=0)
                restaurant_names.append(nom)
                restaurant_vectors.append(mean_vector)

        if restaurant_vectors:
            restaurant_vectors_np = np.array(restaurant_vectors)
            perplexity_value = min(30, len(restaurant_vectors_np) - 1)

            # Réduire à 3 dimensions avec t-SNE
            tsne = TSNE(n_components=3, random_state=42, perplexity=perplexity_value)
            vectors_3d = tsne.fit_transform(restaurant_vectors_np)
            
            # Créer une figure 3D interactive avec Plotly
            fig = go.Figure(data=[go.Scatter3d(
                x=vectors_3d[:, 0],
                y=vectors_3d[:, 1],
                z=vectors_3d[:, 2],
                mode='markers+text',
                text=restaurant_names,  # Annote chaque point avec le nom du restaurant
                textposition="top center",
                marker=dict(
                    size=5,
                    color=vectors_3d[:, 2],  # Couleur basée sur la troisième dimension par exemple
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
                width=1000,   # largeur souhaitée en pixels
                height=800    # hauteur souhaitée en pixels
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun restaurant avec des données suffisantes pour la visualisation.")

    with tab2:
        st.header("WordClouds pour les avis positifs et négatifs")
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
        # Saisie utilisateur pour le mot de recherche
        mot_recherche = st.text_input("Entrez un mot pour trouver des mots similaires :", value="parfait")
        
        # Affichage des mots similaires
        if mot_recherche:
            if mot_recherche in model.wv.key_to_index:
                nb_resultats = st.slider("Nombre de mots à afficher :", 1, 20, 10)

                # Calculer la similarité avec tous les mots du vocabulaire
                similarites = [
                    (mot, model.wv.similarity(mot_recherche, mot))
                    for mot in model.wv.key_to_index
                    if mot != mot_recherche  # Exclure le mot recherché
                ]

                # Créer un DataFrame pour trier les mots
                df_similarites = pd.DataFrame(similarites, columns=["Mot", "Score"]).set_index("Mot")

                # Trier par score (du plus proche au moins proche)
                df_similarites = df_similarites.sort_values(by="Score", ascending=False)

                # Séparer les meilleurs et les pires scores
                meilleurs_scores = df_similarites.head(nb_resultats)
                pires_scores = df_similarites.tail(nb_resultats)

                # Afficher les résultats
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

        # Convertir 'date' en datetime si ce n'est pas déjà le cas
        if filtered_reviews['date'].dtype == 'O':  # Objet indique string pour pandas
            filtered_reviews['date'] = pd.to_datetime(filtered_reviews['date'])

        # Trier par ordre décroissant de la date
        filtered_reviews = filtered_reviews.sort_values(by='date', ascending=False)

                # Afficher uniquement la date sans l'heure dans la vue tout en conservant datetime
        filtered_reviews['date'] = filtered_reviews['date'].dt.date

        # Affichage des commentaires triés par date
        st.dataframe(filtered_reviews.reset_index(drop=True))

        # Créer un buffer pour stocker les données CSV
        buffer = io.BytesIO()

        # Convertir les données filtrées en CSV avec l'encodage et le séparateur souhaité
        filtered_reviews.to_csv(buffer, index=False, sep=";", encoding="utf-8-sig")
        # Revenir au début du buffer
        buffer.seek(0)
        # Ajouter le bouton de téléchargement avec le contenu du buffer
        st.download_button(
            label="Télécharger les commentaires",
            data=buffer.getvalue(),
            file_name="commentaires.csv",
            mime="text/csv"
        )

        # CONVERTIR date en format datetime
        if filtered_reviews['date'].dtype == 'O':  # Objet indique string pour pandas
            filtered_reviews['date'] = pd.to_datetime(filtered_reviews['date'])

        sentiments_mensuels = (
            filtered_reviews.groupby([filtered_reviews['date'].dt.to_period('M'), 'sentiment'])
            .size()
            .unstack(fill_value=0)
        )

        # Restituer les périodes en format string pour un affichage clair
        sentiments_mensuels.index = sentiments_mensuels.index.astype(str)
        sentiments_mensuels.reset_index(inplace=True)
        sentiments_mensuels.rename(columns={'index': 'date'}, inplace=True)

        available_years = sorted(filtered_reviews['date'].dt.year.unique())

        selected_years = st.multiselect(
            "Choisissez une ou plusieurs années :",
            available_years,
            default=[2024]
        )

        # Filtrer les périodes correspondant aux années sélectionnées
        if selected_years:
            filtered_sentiments = sentiments_mensuels[
                sentiments_mensuels['date'].str[:4].isin(map(str, selected_years))
            ]

            # Afficher le graphique
            st.subheader("Évolution mensuelle des sentiments")
            if not filtered_sentiments.empty:
                st.line_chart(filtered_sentiments.set_index('date')[['Positif', 'Négatif']])
            else:
                st.info("Aucune donnée disponible pour les années sélectionnées.")
        else:
            st.info("Veuillez sélectionner au moins une année.")

