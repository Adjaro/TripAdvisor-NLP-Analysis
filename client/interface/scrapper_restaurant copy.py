import streamlit as st
from scraper import TripadvisorScraper
import json
import pandas as pd
from datetime import datetime

def show():
    st.title("🍽️ Ajouter un Restaurant")
    
    # Custom styling
    st.markdown("""
        <style>
        .success-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #d1fae5;
            border: 1px solid #059669;
        }
        .error-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #fee2e2;
            border: 1px solid #dc2626;
        }
        .info-card {
            background-color: white;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # URL Input
    url = st.text_input(
        "URL du restaurant TripAdvisor",
        placeholder="https://www.tripadvisor.fr/Restaurant_Review-..."
    )

    if st.button("🔄 Scraper le restaurant", use_container_width=True):
        if not url:
            st.error("Veuillez entrer une URL valide")
            return
            
        try:
            with st.spinner("⏳ Récupération des données..."):
                # Initialize scraper
                scraper = TripadvisorScraper(url)
                
                # Create progress container
                progress_container = st.empty()
                progress_container.info("Démarrage du scraping...")
                
                # Start scraping
                scraper.scrapper()
                data = scraper.data
                
                if not data:
                    st.error("Aucune donnée n'a pu être récupérée")
                    return
                
                # Show success message
                st.success(f"✅ Restaurant '{data['nom']}' scrapé avec succès!")
                
                # Display restaurant info
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                        <div class='info-card'>
                            <h3>📍 Informations générales</h3>
                            <hr>
                    """, unsafe_allow_html=True)
                    st.write(f"**Nom:** {data['nom']}")
                    st.write(f"**Adresse:** {data['adresse']}")
                    st.write(f"**Note globale:** ⭐ {data['note_globale']}/5")
                    st.write(f"**Classement:** #{data['classement']}")
                
                with col2:
                    st.markdown("""
                        <div class='info-card'>
                            <h3>🏆 Notes détaillées</h3>
                            <hr>
                    """, unsafe_allow_html=True)
                    st.write(f"**Cuisine:** ⭐ {data['note_cuisine']}/5")
                    st.write(f"**Service:** ⭐ {data['note_service']}/5")
                    st.write(f"**Rapport qualité/prix:** ⭐ {data['note_rapportqualiteprix']}/5")
                    st.write(f"**Ambiance:** ⭐ {data['note_ambiance']}/5")
                
                # Show reviews preview
                st.markdown("""
                    <div class='info-card'>
                        <h3>💬 Aperçu des avis</h3>
                        <hr>
                    """, unsafe_allow_html=True)
                
                df_reviews = pd.DataFrame(data['avis'])
                st.dataframe(
                    df_reviews.head(5),
                    use_container_width=True
                )
                
                # Save data option
                if st.button("💾 Sauvegarder les données", use_container_width=True):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"restaurant_data_{timestamp}.json"
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    st.success(f"Données sauvegardées dans {filename}")
                
        except Exception as e:
            st.error(f"Une erreur est survenue: {str(e)}")
            
    # Help section
    with st.expander("ℹ️ Comment utiliser le scraper ?"):
        st.markdown("""
        1. Copiez l'URL d'un restaurant depuis TripAdvisor
        2. Collez l'URL dans le champ ci-dessus
        3. Cliquez sur "Scraper le restaurant"
        4. Attendez la fin du processus
        5. Sauvegardez les données si nécessaire
        """)