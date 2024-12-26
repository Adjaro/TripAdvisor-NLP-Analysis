import streamlit as st

def show():
    # Charger la bibliothèque FontAwesome
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    """, unsafe_allow_html=True)



    # Titre avec une icône dans la barre latérale
    st.sidebar.markdown("""
        <style>
            .sidebar-title {
                display: flex;
                align-items: justify;
                color: green;
                    
                
            }
            .sidebar-title img {
                margin-right: 5px;   
            }
            .sidebar-button {
                font-size: 12em;
                margin: 0;
            }
                        
        </style>
        <div class='sidebar-title'>
            <img src='https://static.tacdn.com/img2/brand_refresh/Tripadvisor_lockup_horizontal_secondary_registered.svg' width='200'/>
            <h1>Scraping</h1>
        </div>
    """, unsafe_allow_html=True)

 

    # Boutons de navigation dans le menu latéral
    if st.sidebar.button("🏠 Accueil"):
        st.session_state.page = 'Accueil'

    if st.sidebar.button("📈 Dashbord"):
        st.session_state.page = 'Dashbord'

    if st.sidebar.button("🗺️ Cartographie"):
        st.session_state.page = 'Cartographie'

    if st.sidebar.button("💡 Analyse NLP"):
        st.session_state.page = 'Analyse NLP'

    if st.sidebar.button("📊 Visualisation data"):
        st.session_state.page = 'Visualisation data'

    if st.sidebar.button("📡 Scrapper Restaurant"):
        st.session_state.page = 'Scrapper Restaurant' 

    if st.sidebar.button("📚 Rapport"):
        st.session_state.page = 'Rapport'

    st.sidebar.markdown("<div class='footer'>Edina ,Nancy ,Linh© 2024</div>", unsafe_allow_html=True)