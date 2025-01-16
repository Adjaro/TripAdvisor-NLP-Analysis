import streamlit as st
from manager import read_restaurant, read_location, get_db
import pandas as pd
# from openai import OpenAI



def show():
    st.title("Restaurant Assistant 🍽️")
    db = next(get_db())
    try:
        # Charger et fusionner les données
        restaurants = pd.merge(
            read_restaurant(db=db),
            read_location(db=db),
            on='id_location'
        )

        if restaurants.empty:
            st.error("Aucune donnée disponible.")
            return
    except Exception as e:
        st.error(f"Erreur de chargement des données: {e}")
        return
    
    # ajouter une  liste deroulante pour les restaurants
    restaurant = st.selectbox(
        "Choisissez un restaurant",
        restaurants['nom']
    )
    # client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "max_messages" not in st.session_state:
        # Counting both user and assistant messages, so 10 rounds of conversation
        st.session_state.max_messages = 20

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if len(st.session_state.messages) >= st.session_state.max_messages:
        st.info(
            """Notice: The maximum message limit for this demo version has been reached. We value your interest!
            We encourage you to experience further interactions by building your own application with instructions
            from Streamlit's [Build a basic LLM chat app](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)
            tutorial. Thank you for your understanding."""
        )

    else:
        if prompt := st.chat_input("What is up?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    # stream = client.chat.completions.create(
                    #     model=st.session_state["openai_model"],
                    #     messages=[
                    #         {"role": m["role"], "content": m["content"]}
                    #         for m in st.session_state.messages
                    #     ],
                    #     stream=True,
                    # )
                    # response = st.write_stream(stream)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": "response"}
                    )
                except:
                    st.session_state.max_messages = len(st.session_state.messages)
                    rate_limit_message = """
                        Oops! Sorry, I can't talk now. Too many people have used
                        this service recently.
                    """
                    st.session_state.messages.append(
                        {"role": "assistant", "content": rate_limit_message}
                    )
                    st.rerun()