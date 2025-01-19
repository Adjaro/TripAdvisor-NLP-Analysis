import streamlit as st

def show():
    # CSS Styles
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            .sidebar .sidebar-content {
                background-image: linear-gradient(180deg, #2E3B4E 0%, #1F2937 100%);
            }
            
            .sidebar-title {
                background: linear-gradient(45deg, #1e3c72 30%, #2a5298 90%);
                padding: 1rem;
                border-radius: 10px;
                color: white;
                text-align: center;
                margin-bottom: 2rem;
                box-shadow: 0 3px 5px 2px rgba(30, 60, 114, .3);
            }
            
            .menu-item {
                padding: 0.75rem;
                margin: 0.5rem 0;
                border-radius: 7px;
                background: rgba(255, 255, 255, 0.05);
                transition: all 0.3s ease;
                cursor: pointer;
                color: #E5E7EB;
            }
            
            .menu-item:hover {
                background: rgba(255, 255, 255, 0.1);
                transform: translateX(5px);
            }
            
            .menu-icon {
                margin-right: 10px;
                color: #60A5FA;
            }
            
            .menu-text {
                font-size: 1.1rem;
                font-weight: 500;
            }
            
            .separator {
                height: 1px;
                background: linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0) 100%);
                margin: 1rem 0;
            }
            
            .footer {
                position: fixed;
                bottom: 0;
                padding: 1rem;
                text-align: center;
                color: #9CA3AF;
                font-size: 0.875rem;
            }
        </style>
    """, unsafe_allow_html=True)

    # Sidebar Header
    st.sidebar.markdown("""
        <div class="sidebar-title">
            <h1><i class="fas fa-utensils"></i> TripAdvisor NLP</h1>
        </div>
    """, unsafe_allow_html=True)

    # Menu Items
    st.sidebar.markdown("""
        <div class="menu-item">
            <i class="fas fa-home menu-icon"></i>
            <span class="menu-text">Accueil</span>
        </div>
        
        <div class="menu-item">
            <i class="fas fa-chart-bar menu-icon"></i>
            <span class="menu-text">Analyse NLP</span>
        </div>
        
        <div class="separator"></div>
        
        <div class="menu-item">
            <i class="fas fa-map-marked-alt menu-icon"></i>
            <span class="menu-text">Carte</span>
        </div>
        
        <div class="menu-item">
            <i class="fas fa-cloud-sun menu-icon"></i>
            <span class="menu-text">Word Cloud</span>
        </div>
        
        <div class="separator"></div>
        
        <div class="menu-item">
            <i class="fas fa-cog menu-icon"></i>
            <span class="menu-text">Paramètres</span>
        </div>
    """, unsafe_allow_html=True)

    # Footer
    st.sidebar.markdown("""
        <div class="footer">
            <p>© 2024 TripAdvisor NLP Analysis</p>
            <p>Développé par Adjaro, Lin & Nancy</p>
        </div>
    """, unsafe_allow_html=True)

    # Add some state management
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'Accueil'

    return st.session_state.current_page