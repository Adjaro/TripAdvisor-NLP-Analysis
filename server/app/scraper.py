import time
import math
import re
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
 
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import os
import logging
import shutil
import time
from pathlib import Path
import undetected_chromedriver as uc
 


class TripadvisorScraper:
    def __init__(self, url):
        self.url = url
        self.nom_restaurant = None
        self.nb_total_commentaires = None
        self.nb_pages = None
        self.nb_commentaires_par_page = None
        self.data = None
        
        self.driver = None

    def create_driver(self):
        browser_executable_path = shutil.which("chromium")

        Path('selenium.log').unlink(missing_ok=True)
        time.sleep(1)

        options = uc.ChromeOptions()
        user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        ]
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-features=NetworkService")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--disable-features=VizDisplayCompositor")

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--incognito")
         
        
        user_agent = random.choice(user_agents)
        options.add_argument(f'--user-agent={user_agent}')

        return uc.Chrome(browser_executable_path=browser_executable_path,
                options=options,
                use_subprocess=False,
                log_level=logging.DEBUG,
                service_log_path='selenium.log')
    
    def handle_cookies(self):
        try:
            WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='onetrust-accept-btn-handler']"))
            ).click()
        except TimeoutException:
            print("Pas de bannière cookies trouvée.")

    def find_restaurant_name(self):
        try:
            name_element = self.driver.find_element(By.XPATH, "//h1[@class='biGQs _P egaXP rRtyp']")
            print(f"Nom trouvé : {name_element.text}")
            self.nom_restaurant = name_element.text
            return name_element.text
        except NoSuchElementException:
            return None

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
            # return nb_commentaires_par_page, nb_total_commentaires, nb_pages
            return nb_commentaires_par_page, nb_total_commentaires, 2
        else:
            return None, None, None

    def scraper_infos_restaurant(self):
        try:
            nom = self.driver.find_element(By.XPATH, "//h1[@class='biGQs _P egaXP rRtyp']").text
            adresse = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Emplacement et coordonnées')]/following::span[contains(@class, 'biGQs _P pZUbB hmDzD')][1]").text
            note_globale = re.search(r"(\d+,\d+)", self.driver.find_elements(By.XPATH, "//div[@class='biGQs _P vvmrG']")[0].text).group(1)
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span//button[@class='ypcsE _S wSSLS']"))).click()
            horaires = [
                f"{lines[0]} : {' - '.join(lines[1:])}"
                for e in self.driver.find_elements("xpath", "//div[@class='VFyGJ Pi']")
                if len(lines := e.text.splitlines()) >= 2
            ]

            time.sleep(3)
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span//button[@class='ypcsE _S wSSLS']"))).click()

            notes = self.driver.find_elements(By.XPATH, "//div[@class='khxWm f e Q3']/div/div")
            note_cuisine = re.search(r'<title[^>]*>([\d.,]+) sur [\d.,]+', notes[1].get_attribute("innerHTML")).group(1)
            note_service = re.search(r'<title[^>]*>([\d.,]+) sur [\d.,]+', notes[3].get_attribute("innerHTML")).group(1)
            note_rapportqualiteprix = re.search(r'<title[^>]*>([\d.,]+) sur [\d.,]+', notes[5].get_attribute("innerHTML")).group(1)
            note_ambiance = re.search(r'<title[^>]*>([\d.,]+) sur [\d.,]+', notes[7].get_attribute("innerHTML")).group(1)
            classement_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'biGQs _P pZUbB hmDzD')]//b/span").text.strip()
            classement = (re.search(r'\d+', classement_element).group())

            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button[class='UikNM _G B- _S _W _T c G_ wSSLS ACvVd']"))).click()
            time.sleep(2)

            try:
                infos_pratiques = self.driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'Infos pratiques')]]/following-sibling::div[contains(@class, 'biGQs')]").text.strip()
            except Exception:
                infos_pratiques = "Non renseigné"

            try:
                fourchette_prix = self.driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'FOURCHETTE DE PRIX')]]/following-sibling::div[contains(@class, 'biGQs _P pZUbB alXOW oCpZu GzNcM nvOhm UTQMg ZTpaU W hmDzD')]").text.strip().replace("€", "").replace("\xa0", "")
            except Exception:
                fourchette_prix = "Non renseigné"

            try:
                types_cuisines = [item.strip() for item in self.driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'CUISINES')]]/following-sibling::div[contains(@class, 'biGQs _P pZUbB alXOW oCpZu GzNcM nvOhm UTQMg ZTpaU W hmDzD')]").text.strip().split(",")]
            except Exception:
                types_cuisines = "Non renseigné"

            try:
                regimes = [item.strip() for item in self.driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'Régimes spéciaux')]]/following-sibling::div[contains(@class, 'biGQs _P pZUbB alXOW oCpZu GzNcM nvOhm UTQMg ZTpaU W hmDzD')]").text.strip().split(",")]
            except Exception:
                regimes = "Non renseigné"

            try:
                repas = [item.strip() for item in self.driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'Repas')]]/following-sibling::div[contains(@class, 'biGQs _P pZUbB alXOW eWlDX GzNcM ATzgx UTQMg TwpTY hmDzD')]").text.strip().split(",")]
            except Exception:
                repas = "Non renseigné"

            try:
                fonctionnalites = [item.strip() for item in self.driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'FONCTIONNALITÉS')]]/following-sibling::div[contains(@class, 'biGQs')]").text.strip().split(",")]
            except Exception:
                fonctionnalites = "Non renseigné"

            time.sleep(5)
            self.driver.find_element(By.XPATH, "//button[@aria-label='Fermer']").click()
            time.sleep(2)

            try:
                google_maps_link = self.driver.find_element(By.XPATH,"//div[@class='akmhy e j']//a[@class='BMQDV _F Gv wSSLS SwZTJ FGwzt ukgoS']").get_attribute("href")
                if "@" in google_maps_link:
                    coordinates = google_maps_link.split("@")[1].split(",")[:2]
                    latitude, longitude = coordinates[0], coordinates[1]
                else:
                    latitude, longitude = "Non renseigné", "Non renseigné"
                    print("Coordonnées introuvables dans le lien.")
            except NoSuchElementException:
                latitude, longitude = "Non renseigné", "Non renseigné"
                print("Lien Google Maps introuvable.")

            return {
                "nom": nom,
                "adresse": adresse,
                "classement": classement,
                "horaires": horaires,
                "note_globale": note_globale,
                "note_cuisine": note_cuisine,
                "note_service": note_service,
                "note_rapportqualiteprix": note_rapportqualiteprix,
                "note_ambiance": note_ambiance,
                "infos_pratiques": infos_pratiques,
                "repas": repas,
                "regimes": regimes,
                "fonctionnalites": fonctionnalites,
                "fourchette_prix": fourchette_prix,
                "types_cuisines": types_cuisines,
                "latitude": latitude,
                "longitude": longitude
            }
        except Exception as e:
            print(f"Erreur lors de l'extraction des informations du restaurant : {e}")
            return {}

    def scraper_page(self):
        data = []
        pseudos = self.driver.find_elements(By.XPATH, "//span[@class='biGQs _P fiohW fOtGX']")
        titres = self.driver.find_elements(By.XPATH, "//div[@class='biGQs _P fiohW qWPrE ncFvv fOtGX']")
        etoiles = self.driver.find_elements(By.XPATH, "//div[@class='OSBmi J k']")
        nb_etoiles = [re.search(r'(\d+),', etoile.get_attribute("textContent")).group(1) for etoile in etoiles]
        dates = [re.search(r"\d{1,2}\s\w+\s\d{4}", elem.text.strip()).group(0) for elem in self.driver.find_elements(By.XPATH, "//div[contains(@class, 'biGQs _P pZUbB ncFvv osNWb')]")]
        experiences = self.driver.find_elements(By.XPATH, "//span[@class='DlAxN']")
        reviews = self.driver.find_elements(By.XPATH, "//div[@data-test-target='review-body']//span[@class='JguWG' and not(ancestor::div[contains(@class, 'csNQI')])]")

        for i in range(len(titres)):
            avis = {
                "pseudo": pseudos[i].text if i < len(pseudos) else "",
                "titre_review": titres[i].text if i < len(titres) else "",
                "nb_etoiles": nb_etoiles[i] if i < len(nb_etoiles) else "",
                "date": dates[i] if i < len(dates) else "",
                "experience": experiences[i].text if i < len(experiences) else "",
                "review": reviews[i].text if i < len(reviews) else ""
            }
            data.append(avis)
        return data

    def scraper_toutes_pages(self, nb_pages):
        all_data = []
        actions = ActionChains(self.driver)

        for page in range(1, nb_pages + 1):
            print(f"Scraping de la page {page}...")
            time.sleep(5)
            try:
                data = self.scraper_page()
                print(f"Données collectées pour la page {page} : {len(data)} avis")
                all_data.extend(data)

                next_button = WebDriverWait(self.driver, 50).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Page suivante']"))
                )

                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(5)
                actions.move_to_element(next_button).click().perform()

                print("Page suivante chargée.")
            except Exception as e:
                print(f"Erreur rencontrée à la page {page} : {e}")
                break

        return all_data

    def test_scraping(self, nbPages_texte):
        avis = []
        infos_restaurant = {
            "nom": "Non disponible",
            "adresse": "Non disponible",
            "classement": "Non disponible",
            "horaires": [],
            "note_globale": "Non disponible",
            "note_cuisine": "Non disponible",
            "note_service": "Non disponible",
            "note_rapportqualiteprix": "Non disponible",
            "note_ambiance": "Non disponible",
            "repas": "Non disponible",
            "infos_pratiques": "Non disponible",
            "regimes": [],
            "fonctionnalites": "Non disponible",
            "fourchette_prix": "Non disponible",
            "types_cuisines": [],
            "latitude" : "Non disponible",
            "longitude" : "Non disponible",
        }
        try:
            infos_restaurant = self.scraper_infos_restaurant()
            nb_commentaires_par_page, nb_total_commentaires, nb_pages = self.extraire_infos(nbPages_texte)

            average_time_per_page = 15
            estimated_total_time = average_time_per_page * nb_pages
            estimated_total_time_minutes = math.ceil(estimated_total_time / 60)
            print(f"Temps estimé pour terminer le scraping : {estimated_total_time_minutes} minutes.\n")

            avis = self.scraper_toutes_pages(nb_pages)
            print(f"Scraping terminé. Total d'avis collectés : {len(avis)}")

        except Exception as e:
            print(f"Erreur générale : {e}")

        restaurant_data = {
            "nom": infos_restaurant["nom"],
            "adresse": infos_restaurant["adresse"],
            "classement": infos_restaurant["classement"],
            "horaires": infos_restaurant["horaires"],
            "note_globale": infos_restaurant["note_globale"],
            "note_cuisine": infos_restaurant["note_cuisine"],
            "note_service": infos_restaurant["note_service"],
            "note_rapportqualiteprix": infos_restaurant["note_rapportqualiteprix"],
            "note_ambiance": infos_restaurant["note_ambiance"],
            "infos_pratiques": infos_restaurant["infos_pratiques"],
            "repas": infos_restaurant["repas"],
            "regimes": infos_restaurant["regimes"],
            "fourchette_prix": infos_restaurant["fourchette_prix"],
            "fonctionnalités": infos_restaurant["fonctionnalites"],
            "type_cuisines": infos_restaurant["types_cuisines"],
            "latitude": infos_restaurant["latitude"],
            "longitude": infos_restaurant["longitude"],
            "avis": avis
        }

        return restaurant_data

    def scrapper(self):
        found = False
        attempts = 0
        max_attempts = 20

        while not found and attempts < max_attempts:
            self.driver = self.create_driver()
            try:
                self.driver.get(self.url)
                time.sleep(3)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                time.sleep(3)
                #save hltm page
                with open("test.html", "w") as file:
                    file.write(self.driver.page_source)

                self.handle_cookies()

                if self.find_restaurant_name():
                    found = True
            except NoSuchElementException:
                print(f"Nom non trouvé, tentative {attempts + 1}/{max_attempts}. Redémarrage...")
                attempts += 1
                self.cleanup()
                time.sleep(10)

        if not found:
            print("Échec : le nom n'a pas été trouvé après plusieurs tentatives.")
            self.cleanup()
        else:
            print("Le nom a été trouvé avec succès. Le navigateur reste ouvert.")
            nbPages_texte = self.driver.find_element("xpath", "//div[@class='Ci']").text
            data = self.test_scraping(nbPages_texte)
            self.cleanup()
            self.data = data
            # return data

    def cleanup(self):
        if self.driver:
            self.driver.quit()
            time.sleep(2)


    def __del__(self):
        self.cleanup()

    def save_data(self, data):
        pass

    
# def main():
#     url = "https://www.tripadvisor.fr/Restaurant_Review-g187265-d5539701-Reviews-L_Institut_Restaurant-Lyon_Rhone_Auvergne_Rhone_Alpes.html"
#     scraper = TripadvisorScraper(url)
#     scraper.scrapper()
#     data = scraper.data
#     print(data)

# if __name__ == "__main__":
#     main()