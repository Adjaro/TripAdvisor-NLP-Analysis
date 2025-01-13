import streamlit as st

# Configuration de la page principale
st.set_page_config(
    page_title="app",
    page_icon="👋",
)

# Contenu principal
st.write("# Welcome to Streamlit! 👋")
st.sidebar.success("Select a demo above.")

