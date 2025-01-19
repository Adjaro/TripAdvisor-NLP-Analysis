import streamlit as st

def show():
    # Custom CSS with improved styling
    st.markdown("""
        <style>
            .sidebar .sidebar-content {
                background: linear-gradient(180deg, #2E3B4E 0%, #1F2937 100%);
            }
            
            .menu-button {
                width: 100%;
                padding: 0.75rem;
                margin: 0.25rem 0;
                border-radius: 7px;
                background: rgba(255, 255, 255, 0.05);
                color: #E5E7EB;
                border: none;
                cursor: pointer;
                transition: all 0.2s ease;
                font-weight: 500;
            }
            
            .menu-button:hover {
                background: rgba(255, 255, 255, 0.1);
                transform: translateX(3px);
            }
            
            .menu-button.active {
                background: linear-gradient(45deg, #2563EB 30%, #3B82F6 90%);
                color: white;
                box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
            }
            
            .sidebar-title {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 1rem 0;
            }
            
            .sidebar-title img {
                max-width: 160px;
                height: auto;
            }
            
            .sidebar-title h1 {
                color: #10B981;
                font-size: 1.5rem;
                margin: 0;
                padding: 0;
            }
            
            .sidebar-footer {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                padding: 1rem;
                text-align: center;
                background: rgba(31, 41, 55, 0.9);
                font-size: 0.875rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # Navigation items
    menu_items = {
        "🏠 Accueil": "Accueil",
        "🗺️ Carte": "Cartographie", 
        "📊 Analyse": "Analyse NLP2",
        "☁️ NLP": "Analyse NLP",
        "🤖 ChatBot": "chatbot",
        "🍽️ Ajouter Restaurant": "Ajouter Restaurant"
    }

    # Sidebar Header
    st.sidebar.markdown("""
        <div class='sidebar-title'>
            <img src='https://static.tacdn.com/img2/brand_refresh/Tripadvisor_lockup_horizontal_secondary_registered.svg'/>
            <h1>ML</h1>
        </div>
        <hr>
    """, unsafe_allow_html=True)

    # Create buttons for each menu item
    for label, page in menu_items.items():
        button_class = "menu-button active" if st.session_state.get('current_page') == page else "menu-button"
        if st.sidebar.button(
            label,
            key=f"btn_{page}",
            help=f"Aller à {label}",
            use_container_width=True
        ):
            st.session_state.current_page = page

    # Footer
    st.sidebar.markdown("""
        <div class='sidebar-footer'>
            <p>Made with ❤️ by Team:<br>
            Adjaro, Lin & Nancy<br>
            Master Data Science - 2024</p>
        </div>
    """, unsafe_allow_html=True)

    return st.session_state.current_page