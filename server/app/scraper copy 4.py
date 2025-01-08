import time
import math
import re
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import os
import platform
import winreg
from pathlib import Path
# import logging
import subprocess

# logger = logging.getLogger(__name__)

class TripadvisorScraper:
    def __init__(self, url):
        self.url = url
        self.nom_restaurant = None
        self.nb_total_commentaires = None
        self.nb_pages = None
        self.nb_commentaires_par_page = None
        self.data = None
        self.driver = None

    def get_chrome_version(self):
        try:
            if platform.system() == 'Windows':
                chrome_path = self.get_chrome_path()
                output = subprocess.check_output(f'wmic datafile where name="{chrome_path}" get Version /value', shell=True)
                version = re.search(r'Version=(\d+)', output.decode('utf-8'))
                return int(version.group(1)) if version else 108
            else:
                output = subprocess.check_output(['google-chrome', '--version'])
                version = re.search(r'Chrome\s+(\d+)', output.decode('utf-8'))
                return int(version.group(1)) if version else 108
        except Exception:
            return 108

    def get_chrome_path(self):
        try:
            if platform.system() == 'Windows':
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
                chrome_path = winreg.QueryValue(key, None)
                if os.path.exists(chrome_path):
                    return chrome_path

                paths = [
                    Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')),
                    Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'))
                ]
                for base_path in paths:
                    chrome_path = base_path / 'Google' / 'Chrome' / 'Application' / 'chrome.exe'
                    if chrome_path.exists():
                        return str(chrome_path)
            else:
                return "/usr/bin/google-chrome-stable"
        except Exception:
            return None

    def create_driver(self):
        options = uc.ChromeOptions()
        chrome_version = self.get_chrome_version()

        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'--chrome-version={chrome_version}')

        chrome_path = self.get_chrome_path()
        if chrome_path:
            options.binary_location = chrome_path

        try:
            driver = uc.Chrome(version_main=chrome_version, options=options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logging.error(f"Failed to create driver: {str(e)}")
            raise

    def handle_cookies(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='onetrust-accept-btn-handler']"))
            ).click()
        except TimeoutException:
            logging.info("No cookie banner found")

    def find_restaurant_name(self):
        try:
            name_element = self.driver.find_element(By.XPATH, "//h1[@class='biGQs _P egaXP rRtyp']")
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
            return nb_commentaires_par_page, nb_total_commentaires, nb_pages
        else:
            return None, None, None

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

    
def main():
    url = "https://www.tripadvisor.fr/Restaurant_Review-g187265-d5539701-Reviews-L_Institut_Restaurant-Lyon_Rhone_Auvergne_Rhone_Alpes.html"
    scraper = TripadvisorScraper(url)
    scraper.scrapper()
    data = scraper.data
    print(data)

if __name__ == "__main__":
    main()