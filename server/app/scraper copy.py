import time
import math
import re
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException, TimeoutException




class RestaurantScraper:
    def __init__(self, url):
        self.url = url
        self.driver = None 

    # Fonction pour extraire les nombres et calculer les pages
    def extraire_infos(texte):
        """
        Extrait le nombre de commentaires par page, le nombre total de commentaires,
        et calcule le nombre de pages à partir d'un texte donné.
        """
        # Nettoyer le texte pour supprimer les espaces insécables
        texte = texte.replace("\u202f", "")  # Remplace les espaces insécables par rien

        # Extraire les chiffres du texte
        chiffres = [int(s) for s in re.findall(r'\d+', texte)]
        
        if len(chiffres) >= 2:
            nb_commentaires_par_page = chiffres[1]  # Exemple : "15" (2e chiffre)
            nb_total_commentaires = chiffres[-1]   # Exemple : "1300" (dernier chiffre)
            nb_pages = math.ceil(nb_total_commentaires / nb_commentaires_par_page)
            return nb_commentaires_par_page, nb_total_commentaires, nb_pages
        else:
            return None, None, None

    
    def scraper_infos_restaurant(driver):
        """
        Scrape les informations globales sur le restaurant.
        """
        nom = driver.find_element(By.XPATH, "//h1[@class='biGQs _P egaXP rRtyp']").text 
        adresse = driver.find_element(By.XPATH, "//div[contains(text(), 'Emplacement et coordonnées')]/following::span[contains(@class, 'biGQs _P pZUbB hmDzD')][1]").text 
        note_globale = re.search(r"(\d+,\d+)", driver.find_elements(By.XPATH, "//div[@class='biGQs _P vvmrG']")[0].text).group(1)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span//button[@class='ypcsE _S wSSLS']"))).click()
        horaires = [
            f"{lines[0]} : {' - '.join(lines[1:])}"
            for e in driver.find_elements("xpath", "//div[@class='VFyGJ Pi']")
            if len(lines := e.text.splitlines()) >= 2
        ]

        time.sleep(3)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span//button[@class='ypcsE _S wSSLS']"))).click()

        # Localiser les éléments des notes
        notes = driver.find_elements(By.XPATH, "//div[@class='khxWm f e Q3']/div/div")
        # Extraire les notes pour chaque catégorie à partir de l'innerHTML
        note_cuisine = re.search(r'<title[^>]*>([\d.,]+) sur [\d.,]+', notes[1].get_attribute("innerHTML")).group(1)
        note_service = re.search(r'<title[^>]*>([\d.,]+) sur [\d.,]+', notes[3].get_attribute("innerHTML")).group(1)
        note_rapportqualiteprix = re.search(r'<title[^>]*>([\d.,]+) sur [\d.,]+', notes[5].get_attribute("innerHTML")).group(1)
        note_ambiance = re.search(r'<title[^>]*>([\d.,]+) sur [\d.,]+', notes[7].get_attribute("innerHTML")).group(1)
        classement_element = driver.find_element(By.XPATH, "//div[contains(@class, 'biGQs _P pZUbB hmDzD')]//b/span").text.strip() 
        classement = (re.search(r'\d+', classement_element).group())

        #click pour avoir détails
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button[class='UikNM _G B- _S _W _T c G_ wSSLS ACvVd']"))).click()
        time.sleep(2)
        #infos pratiques
        try:
            infos_pratiques = driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'Infos pratiques')]]/following-sibling::div[contains(@class, 'biGQs')]").text.strip()
        except Exception:
            infos_pratiques = "Non renseigné"

        #fourchette de prix
        try:
            fourchette_prix = driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'FOURCHETTE DE PRIX')]]/following-sibling::div[contains(@class, 'biGQs _P pZUbB alXOW oCpZu GzNcM nvOhm UTQMg ZTpaU W hmDzD')]").text.strip().replace("€", "").replace("\xa0", "")
        except Exception:
            fourchette_prix = "Non renseigné"  # Valeur par défaut
        #type cuisines
        try:
            types_cuisines = [item.strip() for item in driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'CUISINES')]]/following-sibling::div[contains(@class, 'biGQs _P pZUbB alXOW oCpZu GzNcM nvOhm UTQMg ZTpaU W hmDzD')]").text.strip().split(",")]
        except Exception:
            types_cuisines = "Non renseigné"
        #regimes
        try:
            regimes = [item.strip() for item in driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'Régimes spéciaux')]]/following-sibling::div[contains(@class, 'biGQs _P pZUbB alXOW oCpZu GzNcM nvOhm UTQMg ZTpaU W hmDzD')]").text.strip().split(",")]
        except Exception:
            regimes = "Non renseigné"
        #repas
        try:
            repas = [item.strip() for item in driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'Repas')]]/following-sibling::div[contains(@class, 'biGQs _P pZUbB alXOW eWlDX GzNcM ATzgx UTQMg TwpTY hmDzD')]").text.strip().split(",")]
        except Exception:
            repas = "Non renseigné"
        #fonctionnalités
        try:
            fonctionnalites = [item.strip() for item in driver.find_element(By.XPATH, "//div[contains(@class, 'Wf') and ./div[contains(text(), 'FONCTIONNALITÉS')]]/following-sibling::div[contains(@class, 'biGQs')]").text.strip().split(",")]
        except Exception:
            fonctionnalites = "Non renseigné"
        
        time.sleep(5)
        driver.find_element(By.XPATH, "//button[@aria-label='Fermer']").click()
        time.sleep(2)

        #quartier = driver.find_elements(By.XPATH,"//div[@class='akmhy e j']//a[@class='BMQDV _F Gv wSSLS SwZTJ FGwzt ukgoS']/span[contains(@class, 'biGQs _P pZUbB hmDzD')]")
        #quartier = quartier[1].text
        
        try:
        # Récupérer l'élément `<a>` contenant le lien Google Maps
            google_maps_link = driver.find_element(By.XPATH,"//div[@class='akmhy e j']//a[@class='BMQDV _F Gv wSSLS SwZTJ FGwzt ukgoS']").get_attribute("href")
            # Extraire les coordonnées géographiques du lien
            if "@" in google_maps_link:
                coordinates = google_maps_link.split("@")[1].split(",")[:2]  # Prendre latitude et longitude
                latitude, longitude = coordinates[0], coordinates[1]
                #print(f"Latitude : {latitude}, Longitude : {longitude}")
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
            "note_cuisine":note_cuisine, 
            "note_service":note_service, 
            "note_rapportqualiteprix":note_rapportqualiteprix, 
            "note_ambiance":note_ambiance,
            "infos_pratiques":infos_pratiques,
            "repas":repas, 
            "regimes": regimes,
            "fonctionnalites":fonctionnalites,
            "fourchette_prix": fourchette_prix, 
            "types_cuisines": types_cuisines, 
            "latitude": latitude, 
            "longitude": longitude
            }

    # Fonction pour scraper les avis d'une page
    def scraper_page(driver):
        """
        Récupère les avis d'une seule page.
        """
        data = []
        # Récupération des éléments sur la page
        pseudos = driver.find_elements(By.XPATH, "//span[@class='biGQs _P fiohW fOtGX']") 
        titres = driver.find_elements(By.XPATH, "//div[@class='biGQs _P fiohW qWPrE ncFvv fOtGX']")
        etoiles = driver.find_elements(By.XPATH, "//div[@class='OSBmi J k']")
        nb_etoiles = [re.search(r'(\d+),', etoile.get_attribute("textContent")).group(1) for etoile in etoiles]
        dates = [re.search(r"\d{1,2}\s\w+\s\d{4}", elem.text.strip()).group(0) for elem in driver.find_elements(By.XPATH, "//div[contains(@class, 'biGQs _P pZUbB ncFvv osNWb')]")]
        experiences = driver.find_elements(By.XPATH, "//span[@class='DlAxN']")
        reviews = driver.find_elements(By.XPATH, "//div[@data-test-target='review-body']//span[@class='JguWG' and not(ancestor::div[contains(@class, 'csNQI')])]")


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

    # Fonction pour scraper les avis de toutes les pages
    def scraper_toutes_pages(driver, nb_pages):
        """
        Scrape les avis de toutes les pages en utilisant la fonction `scraper_page`.
        """
        all_data = []
        actions = ActionChains(driver)
        
        for page in range(1, nb_pages + 1):
            print(f"Scraping de la page {page}...")
            time.sleep(5) 
            try:
                # Recharger les avis dynamiquement pour chaque page
                data = scraper_page(driver)
                print(f"Données collectées pour la page {page} : {len(data)} avis")
                all_data.extend(data)

                # Navigation vers la page suivante
                next_button = WebDriverWait(driver, 50).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Page suivante']"))
                )

                # Scroll et clic
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(5)
                actions.move_to_element(next_button).click().perform()


                print("Page suivante chargée.")
            
            except Exception as e:
                print(f"Erreur rencontrée à la page {page} : {e}")
                break  # Arrêter la boucle, mais conserver les données collectées jusqu'ici

        return all_data

    def test_scraping(driver, nbPages_texte):
        """
        Teste l'ensemble du processus de scraping :
        - Extraction d'informations globales sur le restaurant
        - Scraping des avis sur toutes les pages
        - Regroupement des données
        """
        avis = []  # Init
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
            # Étape 1 : Extraire les infos globales
            infos_restaurant = scraper_infos_restaurant(driver)
    

            # Étape 2 : Extraire les infos pour les pages d'avis
            nb_commentaires_par_page, nb_total_commentaires, nb_pages = extraire_infos(nbPages_texte)
    
            # **Estimation du temps total** :
            average_time_per_page = 15  # Temps moyen par page en secondes
            estimated_total_time = average_time_per_page * nb_pages
    
            # Arrondir en minutes
            estimated_total_time_minutes = math.ceil(estimated_total_time / 60)
            print(f"Temps estimé pour terminer le scraping : {estimated_total_time_minutes} minutes.\n")

            # Étape 3 : Scraper les avis
            avis = scraper_toutes_pages(driver, nb_pages)
            print(f"Scraping terminé. Total d'avis collectés : {len(avis)}")

        except Exception as e:
            print(f"Erreur générale : {e}")

        # Étape 4 : Regrouper les données, même partielles
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
            "avis": avis  # Liste des avis
            
        }

        return restaurant_data



    # Fonction pour configurer le driver
    def create_driver( ):
        #changer par le bon chemin
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

    def scrapper(url):
                
        # Boucle pour redémarrer le navigateur jusqu'à ce que l'élément soit trouvé
        found = False
        attempts = 0
        max_attempts = 20

        while not found and attempts < max_attempts:
            driver = create_driver()  # Créer un nouveau navigateur
            try:
                driver.get(url)
                time.sleep(3)
                
                # Rendre Selenium indétectable
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                time.sleep(3)
                # Accepter les cookies
                try:
                    WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='onetrust-accept-btn-handler']"))
                    ).click()
                except TimeoutException:
                    print("Pas de bannière cookies trouvée.")

                # Chercher le nom
                nom = driver.find_element(By.XPATH, "//h1[@class='biGQs _P egaXP rRtyp']")
                print(f"Nom trouvé : {nom.text}")
                found = True  # Si le nom est trouvé, sortir de la boucle
            except NoSuchElementException:
                print(f"Nom non trouvé, tentative {attempts + 1}/{max_attempts}. Redémarrage...")
                attempts += 1
                driver.quit()  # Fermer le navigateur avant de recommencer
                time.sleep(10)  # Attendre avant de redémarrer un nouveau navigateur
        if not found:
            print("Échec : le nom n'a pas été trouvé après plusieurs tentatives.")
            time.sleep(2)
            driver.quit()  # Fermer le dernier navigateur si le nom n'est pas trouvé
        else:
            print("Le nom a été trouvé avec succès. Le navigateur reste ouvert.")
        # Le driver reste ouvert si le nom a été trouvé


        #code pour executer le scraping
        #On recupère dabord le nb de pages à scraper et on appelle la fonction de scraping puis ferme le driver
        nbPages_texte = driver.find_element("xpath", "//div[@class='Ci']").text
        data = test_scraping(driver, nbPages_texte)
        driver.quit()
        
        return data
    

# URL à visiter
#changer avec l'URL du restaurant à scraper
url = "https://www.tripadvisor.fr/Restaurant_Review-g187265-d5539701-Reviews-L_Institut_Restaurant-Lyon_Rhone_Auvergne_Rhone_Alpes.html"

# Boucle pour redémarrer le navigateur jusqu'à ce que l'élément soit trouvé
found = False
attempts = 0
max_attempts = 20

while not found and attempts < max_attempts:
    driver = create_driver()  # Créer un nouveau navigateur
    try:
        driver.get(url)
        time.sleep(3)
        
        # Rendre Selenium indétectable
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        time.sleep(3)
        # Accepter les cookies
        try:
            WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='onetrust-accept-btn-handler']"))
            ).click()
        except TimeoutException:
            print("Pas de bannière cookies trouvée.")

        # Chercher le nom
        nom = driver.find_element(By.XPATH, "//h1[@class='biGQs _P egaXP rRtyp']")
        print(f"Nom trouvé : {nom.text}")
        found = True  # Si le nom est trouvé, sortir de la boucle
    except NoSuchElementException:
        print(f"Nom non trouvé, tentative {attempts + 1}/{max_attempts}. Redémarrage...")
        attempts += 1
        driver.quit()  # Fermer le navigateur avant de recommencer
        time.sleep(10)  # Attendre avant de redémarrer un nouveau navigateur
if not found:
    print("Échec : le nom n'a pas été trouvé après plusieurs tentatives.")
    time.sleep(2)
    driver.quit()  # Fermer le dernier navigateur si le nom n'est pas trouvé
else:
    print("Le nom a été trouvé avec succès. Le navigateur reste ouvert.")
# Le driver reste ouvert si le nom a été trouvé


#code pour executer le scraping
#On recupère dabord le nb de pages à scraper et on appelle la fonction de scraping puis ferme le driver
nbPages_texte = driver.find_element("xpath", "//div[@class='Ci']").text
data = test_scraping(driver, nbPages_texte)
driver.quit()