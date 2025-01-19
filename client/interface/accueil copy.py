import os
import re
import time
import math
import random
import logging
import shutil
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import undetected_chromedriver as uc
import streamlit as st

# Classe principale pour le scraping sur Tripadvisor
class TripadvisorScraper:
    def __init__(self, url):
        self.url = url
        self.nom_restaurant = None
        self.nb_total_commentaires = None
        self.nb_pages = None
        self.nb_commentaires_par_page = None
        self.data = None
        self.driver = None

    # Création du driver Selenium avec configuration
    def create_driver(self):
        service = Service('chromedriver.exe')
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        ]
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--incognito")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        user_agent = random.choice(user_agents)
        options.add_argument(f'--user-agent={user_agent}')
        return uc.Chrome(options=options, service=service)

    # Gestion de la bannière cookies
    def handle_cookies(self):
        try:
            WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='onetrust-accept-btn-handler']"))
            ).click()
        except TimeoutException:
            print("Pas de bannière cookies trouvée.")

    # Recherche du nom du restaurant
    def find_restaurant_name(self):
        try:
            name_element = self.driver.find_element(By.XPATH, "//h1[@class='biGQs _P egaXP rRtyp']")
            print(f"Nom trouvé : {name_element.text}")
            self.nom_restaurant = name_element.text
            return name_element.text
        except NoSuchElementException:
            print("Nom du restaurant introuvable.")
            return None

    # Extraction des informations sur le nombre de pages et de commentaires
    def extraire_infos(self, texte):
        texte = texte.replace("\u202f", "")
        chiffres = [int(s) for s in re.findall(r'\d+', texte)]
        if len(chiffres) >= 2:
            nb_commentaires_par_page = chiffres[1]
            nb_total_commentaires = chiffres[-1]
            nb_pages = math.ceil(nb_total_commentaires / nb_commentaires_par_page)
            self.nb_total_commentaires = nb_total_commentaires
            self.nb_pages = nb_pages
            self.nb_commentaires_par_page = nb_commentaires_par_page
            return nb_commentaires_par_page, nb_total_commentaires, nb_pages
        else:
            return None, None, None

    # Fonction principale de scraping des informations du restaurant
    def scraper_infos_restaurant(self):
        try:
            nom = self.driver.find_element(By.XPATH, "//h1[@class='biGQs _P egaXP rRtyp']").text
            adresse = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Emplacement et coordonnées')]/following::span[contains(@class, 'biGQs _P pZUbB hmDzD')][1]").text
            note_globale = re.search(r"(\d+,\d+)", self.driver.find_elements(By.XPATH, "//div[@class='biGQs _P vvmrG']")[0].text).group(1)

            # Exemple simplifié (à compléter si nécessaire pour d'autres éléments)
            return {
                "nom": nom,
                "adresse": adresse,
                "note_globale": note_globale,
            }
        except Exception as e:
            print(f"Erreur lors de l'extraction des informations : {e}")
            return {}

    # Fonction pour le nettoyage du driver
    def cleanup(self):
        if self.driver:
            self.driver.quit()
            time.sleep(2)

    # Fonction pour initialiser et exécuter le scraping
    def scrapper(self):
        found = False
        attempts = 0
        max_attempts = 5

        while not found and attempts < max_attempts:
            self.driver = self.create_driver()
            try:
                self.driver.get(self.url)
                time.sleep(3)
                self.handle_cookies()
                if self.find_restaurant_name():
                    found = True
            except Exception as e:
                print(f"Tentative {attempts + 1} échouée : {e}")
                attempts += 1
                self.cleanup()

        if not found:
            print("Impossible de trouver les informations après plusieurs tentatives.")
            self.cleanup()
        else:
            print("Scraping réussi.")
            self.cleanup()

    
# def main():
#     url = "https://www.tripadvisor.fr/Restaurant_Review-g187265-d5539701-Reviews-L_Institut_Restaurant-Lyon_Rhone_Auvergne_Rhone_Alpes.html"
#     scraper = TripadvisorScraper(url)
#     scraper.scrapper()
#     data = scraper.data
#     print(data)

# if __name__ == "__main__":
#     main()

# Fonction principale Streamlit
def show():
    st.title("Scraping de restaurant TripAdvisor")
    st.write(
        "Entrez une URL de restaurant TripAdvisor pour collecter des informations principales et les avis."
    )

    # Entrée URL
    url = st.text_input("URL du restaurant TripAdvisor", "")

    if url:
        if st.button("Démarrer le scraping"):
            scraper = TripadvisorScraper(url)
             
 
            # scraper.driver = scraper.create_driver()
            with st.spinner("Scraping en cours..."):
                data = scraper.scrapper()
                 
            if data:
                st.success("Scraping terminé avec succès.")
                st.json(data)
            else:
                st.error("Une erreur est survenue pendant le scraping.")


if __name__ == "__main__":
    main()
