import time
import math
import re
import random
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc


class TripadvisorScraper:
    def __init__(self, url, driver_path):
        self.url = url
        self.driver_path = driver_path
        self.driver = None
        self.data = []
    
    def setup_driver(self):
        """Initialise le driver Selenium avec des paramètres réalistes pour contourner les détections."""
        options = uc.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("start-maximized")
        
        # Randomiser l'user-agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        ]
        user_agent = random.choice(user_agents)
        options.add_argument(f'--user-agent={user_agent}')
        
        # Initialiser le driver
        service = Service(self.driver_path)
        self.driver = uc.Chrome(options=options, service=service)
        self.driver.get(self.url)
        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        
        # Accepter les cookies
        try:
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id='onetrust-reject-all-handler']"))
            ).click()
        except Exception as e:
            print(f"Erreur lors de l'acceptation des cookies : {e}")
    
    @staticmethod
    def extract_page_info(text):
        """Extrait le nombre de commentaires et de pages à partir d'un texte donné."""
        text = text.replace("\u202f", "")  # Supprimer les espaces insécables
        numbers = [int(s) for s in re.findall(r'\d+', text)]
        if len(numbers) >= 2:
            comments_per_page = numbers[1]
            total_comments = numbers[-1]
            pages = math.ceil(total_comments / comments_per_page)
            return comments_per_page, total_comments, pages
        return None, None, None
    
    def scrape_restaurant_info(self):
        """Scrape les informations principales d'un restaurant."""
        try:
            name = self.driver.find_element(By.XPATH, "//h1[@class='biGQs _P egaXP rRtyp']").text
            address = self.driver.find_element(
                By.XPATH,
                "//div[contains(text(), 'Emplacement et coordonnées')]/following::span[contains(@class, 'biGQs _P pZUbB hmDzD')][1]"
            ).text
            rank_text = self.driver.find_element(By.XPATH, "//div[contains(@class, 'biGQs _P pZUbB hmDzD')]//b/span").text
            rank = re.search(r'\d+', rank_text).group()
            price_range = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'biGQs _P pZUbB alXOW oCpZu GzNcM nvOhm UTQMg ZTpaU W hmDzD') and contains(text(), '€')]"
            ).text.strip().replace("€", "").replace("\xa0", "")
            cuisine_types = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'biGQs _P pZUbB alXOW oCpZu GzNcM nvOhm UTQMg ZTpaU W hmDzD') and not(contains(text(), '€'))]"
            ).text.split(",")
            return {
                "name": name,
                "address": address,
                "rank": rank,
                "price_range": price_range,
                "cuisine_types": [c.strip() for c in cuisine_types]
            }
        except Exception as e:
            print(f"Erreur lors de l'extraction des informations du restaurant : {e}")
            return {}
    
    def scrape_reviews_on_page(self):
        """Scrape les avis sur une seule page."""
        data = []
        try:
            pseudos = self.driver.find_elements(By.XPATH, "//span[@class='biGQs _P fiohW fOtGX']")
            titles = self.driver.find_elements(By.XPATH, "//div[@class='biGQs _P fiohW qWPrE ncFvv fOtGX']")
            stars = self.driver.find_elements(By.XPATH, "//div[@class='OSBmi J k']")
            stars_count = [re.search(r'(\d+),', star.get_attribute("textContent")).group(1) for star in stars]
            dates = [
                self.driver.execute_script("return arguments[0].childNodes[0].textContent;", elem).strip()
                for elem in self.driver.find_elements(By.XPATH, "//div[@class='aVuQn']")
            ]
            reviews = self.driver.find_elements(By.XPATH, "//div[@data-test-target='review-body']//span[@class='JguWG']")
            for i in range(len(titles)):
                data.append({
                    "pseudo": pseudos[i].text if i < len(pseudos) else "",
                    "title": titles[i].text if i < len(titles) else "",
                    "stars": stars_count[i] if i < len(stars_count) else "",
                    "date": dates[i] if i < len(dates) else "",
                    "review": reviews[i].text if i < len(reviews) else ""
                })
        except Exception as e:
            print(f"Erreur lors du scraping des avis sur une page : {e}")
        return data
    
    def scrape_all_reviews(self, pages):
        """Scrape les avis sur toutes les pages disponibles."""
        all_data = []
        actions = ActionChains(self.driver)
        for page in range(1, pages + 1):
            print(f"Scraping page {page}/{pages}...")
            time.sleep(5)
            all_data.extend(self.scrape_reviews_on_page())
            try:
                next_button = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@aria-label='Page suivante']"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                actions.move_to_element(next_button).click().perform()
            except Exception as e:
                print(f"Erreur lors du changement de page : {e}")
                break
        return all_data
    
    def scrape(self):
        """Exécute l'ensemble du processus de scraping."""
        self.setup_driver()
        try:
            restaurant_info = self.scrape_restaurant_info()
            page_info_text = self.driver.find_element(By.XPATH, "//div[@class='Ci']").text
            _, _, total_pages = self.extract_page_info(page_info_text)
            reviews = self.scrape_all_reviews(total_pages)
            restaurant_info["reviews"] = reviews
            
            with open("restaurant_data.json", "w", encoding="utf-8") as f:
                json.dump(restaurant_info, f, ensure_ascii=False, indent=4)
            print("Scraping terminé, données sauvegardées dans restaurant_data.json.")
        except Exception as e:
            print(f"Erreur générale lors du scraping : {e}")
        finally:
            self.driver.quit()


# # Exemple d'utilisation
# url = 'https://www.tripadvisor.fr/Restaurant_Review-g187265-d3727154-Reviews-Les_Terrasses_de_Lyon-Lyon_Rhone_Auvergne_Rhone_Alpes.html'
# driver_path = 'path/to/chromedriver.exe'
# scraper = TripadvisorScraper(url, driver_path)
# scraper.scrape()
