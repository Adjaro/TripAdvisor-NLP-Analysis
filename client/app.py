import streamlit as st
from interface import (
    accueil, 
    navbar, 
    dashbord, 
    cartographie, 
    analyse_nlp2, 
    scrapper_restaurant, 
    chatbot
)
import time
from typing import Optional
from manager import InitialisationBD

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Accueil"

@st.cache_resource
def init_database() -> Optional[bool]:
    """Initialize database with caching"""
    try:
        InitialisationBD()
        return True
    except Exception as e:
        st.error(f"Database initialization failed: {str(e)}")
        return False

# Page routing dictionary
PAGES = {
    "Accueil": accueil,
    "Analyse NLP2": dashbord,
    "Cartographie": cartographie,
    "Analyse NLP": analyse_nlp2,
    "chatbot": chatbot,
    "Ajouter Restaurant": scrapper_restaurant,
}

def main():
    # Initialize database
    init_success = init_database()
    
    if not init_success:
        st.error("Failed to initialize database")
        return

    # Show navbar and get current page
    current_page = navbar.show()
    
    # Show selected page content
    if current_page in PAGES:
        PAGES[current_page].show()
    else:
        st.error(f"Page {current_page} not found")

if __name__ == "__main__":
    st.set_page_config(
    page_title="Tripadvisor Scraper",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
    )
    
    main()