from dotenv import find_dotenv, load_dotenv
import streamlit as st
from rag_simulation.rag_augmented import AugmentedRAG
from rag_simulation.corpus_ingestion import BDDChunks

load_dotenv(find_dotenv())

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


@st.cache_resource
def instantiate_bdd(path: str) -> BDDChunks:
    # bdd = BDDChunks(embedding_model="paraphrase-xlm-r-multilingual-v1", path=path)
    # bdd = BDDChunks(embedding_model="paraphrase-xlm-r-multilingual-v1", path=path)
    bdd = BDDChunks(embedding_model="paraphrase-multilingual-MiniLM-L12-v2", path="path")

    bdd()
    return bdd

def show():
    # st.title("🤖 ChatBot - Restaurants de Lyon")
    st.markdown("""
        <div class='title-container'>
            <h1>🤖 ChatBot - Restaurants de Lyon</h1>    
        </div>
    """, unsafe_allow_html=True)

    # Configuration initiale
    # path = "./ChromaDB11"
    path = "./"
    # generation_model = "ministral-8b-latest"
    generation_model = "open-codestral-mamba"
    max_tokens = 1000
    temperature = 0.2
    role_prompt = (
        "Tu es un agent conversationnel spécialisé dans les restaurants de Lyon, conçu pour fournir des réponses détaillées et utiles en te basant uniquement sur le contexte fourni. "
        "Ta mission est d'aider les utilisateurs en donnant des recommandations précises, des informations sur les types de cuisine, les emplacements, les horaires d'ouverture, les adresses, ainsi que tout autre détail disponible dans le contexte, comme les commentaires positifs ou négatifs. "
        "Si une information demandée ne figure pas dans le contexte fourni ou si tu n'as pas la réponse toi-même, informe poliment l'utilisateur que tu ne disposes pas de cette information. "
        "Invite-le ensuite à consulter le site suivant pour des informations complémentaires : "
        "https://https://www.tripadvisor.fr/RestaurantSearch?geo=187265&sortOrder=popularity."
    )


    # role_prompt = (
    #     "Tu es un agent conversationnel conçu pour aider les utilisateurs à obtenir des informations sur les restaurants de Lyon en te basant sur le contexte fourni. "
    #     "Ton rôle est de fournir des recommandations précises, des détails sur les types de cuisine, les emplacements ou toute autre information pertinente. "
    #     "Si les informations demandées ne sont pas disponibles dans le contexte, redirige poliment l'utilisateur vers Tripadvisor pour obtenir des réponses supplémentaires."
    # )
    # role_prompt = "Tu es un assistant virtuel qui aide les utilisateurs à répondre à des questions."

    # role_prompt = (
    #     """
    #     Tu es un agent conversationnel conçu pour aider les utilisateurs à obtenir des informations sur les restaurants de Lyon en te basant exclusivement sur le contexte fourni. 
    #     Si les informations demandées ne sont pas disponibles dans le contexte, redirige poliment l'utilisateur vers [Tripadvisor](https://www.tripadvisor.fr/RestaurantSearch?geo=187265&sortOrder=popularity&Search?q=Bouchon+Lyonnais) pour obtenir des réponses supplémentaires.
    #     """
    # )

    # role_prompt = (
    # "Tu es un agent conversationnel spécialisé dans les restaurants de Lyon, conçu pour répondre exclusivement en te basant sur le contexte fourni. "
    # "Ta mission est de fournir des recommandations précises, des informations sur les types de cuisine, les emplacements, ou toute autre donnée pertinente issue du contexte. "
    # "Si tu ne trouves pas l'information demandée dans le contexte fourni, informe l'utilisateur que tu ne disposes pas de cette information et redirige-le poliment vers le site suivant pour des informations complémentaires : "
    # "https://www.tripadvisor.fr/RestaurantSearch?geo=187265&sortOrder=popularity&Search?q=Bouchon+Lyonnais."
    # )


    # Initialisation du modèle
    llm = AugmentedRAG(
        role_prompt=role_prompt,
        generation_model=generation_model,
        bdd_chunks=instantiate_bdd(path=path),
        top_n=1000,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    # Gestion de l'historique des messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Affichage des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Boîte d'entrée utilisateur
    if query := st.chat_input("Posez votre question ici..."):
        if query.strip():
            # Affichage du message utilisateur
            with st.chat_message("user"):
                st.markdown(query)
            st.session_state.messages.append({"role": "user", "content": query})

            # Réponse du chatbot
            response = llm(query=query, history=st.session_state.messages)
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

    # Bouton pour réinitialiser le chat
    if st.button("♻️ Réinitialiser le Chat"):
        st.session_state.messages = []
        st.rerun()
