from dotenv import find_dotenv, load_dotenv
import numpy
import streamlit as st
from rag_simulation.rag import SimpleRAG
from rag_simulation.rag_augmented import AugmentedRAG
from rag_simulation.corpus_ingestion import BDDChunks

load_dotenv(find_dotenv())

st.set_page_config(
    page_title="ChatBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource  # cache_data permet de ne pas avoir à reload la fonction à chaque fois que l'on fait une action sur l'application
def instantiate_bdd(path: str) -> BDDChunks:
    bdd = BDDChunks(embedding_model="paraphrase-multilingual-MiniLM-L12-v2", path=path)
    bdd()
    return bdd


col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    generation_model = st.selectbox(
        label="Choose your LLM",
        options=[
            "ministral-8b-latest",
            "open-codestral-mamba",
        ],
    )

with col2:
    role_prompt = st.text_area(
        label="Le rôle du chatbot",
        value="""Tu es un agent conversationnel. Ton rôle est d'aider les élèves du Master 2 SISE.
    Si tu n'as pas l'information nécessaire pour répondre, tu peux rediriger l'élève vers les responsables du Master.""",
    )

with col3:
    path = st.text_input(label="Path to PDF", value="C:/Users/ediad/Documents/llm/TD2/ressources/Pratique_Methodes_Factorielles.pdf")

col_max_tokens, col_temperature, _ = st.columns([0.25, 0.25, 0.5])
with col_max_tokens:
    max_tokens = st.select_slider(
        label="Output max tokens", options=list(range(200, 2000, 50))
    )

with col_temperature:
    range_temperature = [round(x, 2) for x in list(numpy.linspace(0, 5, num=50))]
    temperature = st.select_slider(label="Temperature", options=range_temperature)

if path:
    llm = AugmentedRAG(
        role_prompt=role_prompt,
        generation_model=generation_model,
        bdd_chunks=instantiate_bdd(path=path),
        top_n=2,
        max_tokens=max_tokens,
        temperature=temperature,
    )


if "messages" not in st.session_state:
    st.session_state.messages = []

# On affiche les messages de l'utilisateur et de l'IA entre chaque message
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Si présence d'un input par l'utilisateur,
if query := st.chat_input(""):
    if not path:
        st.error("You forgot to define a path!! 😱")
    else:
        if query.strip():
            # On affiche le message de l'utilisateur
            with st.chat_message("user"):
                st.markdown(query)
            # On ajoute le message de l'utilisateur dans l'historique de la conversation
            st.session_state.messages.append({"role": "user", "content": query})
            # On récupère la réponse du chatbot à la question de l'utilisateur
            response = llm(
                query=query,
                history=st.session_state.messages,
            )
            # On affiche la réponse du chatbot
            with st.chat_message("assistant"):
                st.markdown(response['response'])
                # st.markdown(llm.latency)
                # st.markdown(llm.input_tokens)
                # st.markdown(llm.output_tokens)
                # st.markdown(llm.llm)
                # st.markdown(llm.dollor_cost)
                # st.markdown(llm.)
            # On ajoute le message du chatbot dans l'historique de la conversation
            st.session_state.messages.append({"role": "assistant", "content": response})
        # On ajoute un bouton pour réinitialiser le chat
if st.button("Réinitialiser le Chat", type="primary"):
    st.session_state.messages = []
    st.rerun()
