import streamlit as st

def show():
    # Initialize session state for navigation
    # if 'current_page' not in st.session_state:
    #     st.session_state.current_page = 'home'

    st.markdown("""
        <style>
            .sidebar .sidebar-content {
                background: linear-gradient(180deg, #2E3B4E 0%, #1F2937 100%);
            }
            
            .menu-button {
                width: 100%;
                padding: 0.75rem;
                margin: 0.5rem 0;
                border-radius: 7px;
                background: rgba(255, 255, 255, 0.05);
                color: #E5E7EB;
                border: none;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .menu-button:hover {
                background: rgba(255, 255, 255, 0.1);
                transform: translateX(5px);
            }
            
            .menu-button.active {
                background: linear-gradient(45deg, #2563EB 30%, #3B82F6 90%);
                color: white;
                box-shadow: 0 3px 5px rgba(37, 99, 235, 0.2);
            }
            
            .chatbot-button {
                width: 100%;
                background: linear-gradient(45deg, #2563EB 30%, #3B82F6 90%);
                padding: 0.75rem;
                border-radius: 10px;
                color: white;
                border: none;
                cursor: pointer;
                margin: 1rem 0;
                box-shadow: 0 3px 5px rgba(37, 99, 235, 0.2);
                transition: all 0.3s ease;
            }
        </style>
    """, unsafe_allow_html=True)

    # Navigation items with working buttons
    menu_items = {
        "🏠 Accueil": "Accueil",
        "🗺️ Carte": "Cartographie",
        "📊 Analyse": "Analyse NLP2",
        "🤖 ChatBot" : "chatbot",
        "☁️ NLP": "Analyse NLP",
        #Ajouter restaurant
        "🍽️ Ajouter Restaurant": "Ajouter Restaurant",
        
    }
        # Sidebar Header
    # st.sidebar.markdown("""
    #     <div class="sidebar-title">
    #         <h1><i class="fas fa-utensils"></i> TripAdvisor NLP</h1>
    #     </div>
    # """, unsafe_allow_html=True)

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
            <h1>ML</h1>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("<hr>", unsafe_allow_html=True)

    # Create buttons for each menu item
    for label, page in menu_items.items():
        if st.sidebar.button(
            label,
            key=f"btn_{page}",
            help=f"Aller à {label}",
            use_container_width=True
        ):
            st.session_state.current_page = page
    
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    st.sidebar.markdown("""
        <div style='text-align: center'>
            <p>Made with ❤️ by Team: </p>
            <p>Adjaro, Linh nhi & Nancy</p>
            <p>Master Data Science - 2024</p>
        </div>
    """, unsafe_allow_html=True)
    return st.session_state.current_page