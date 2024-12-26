import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent, FakeUserAgentError
import pandas as pd
import time
from random import randint
import logging
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TripAdvisorScraper:
    def __init__(self, base_url): 
        """
        Initialise le scraper.
        :param base_url: URL de base pour le scraping
        """
        self.base_url = base_url
        self.setup_user_agent()
        self.session = requests.Session()
        self.min_delay = 2
        self.max_delay = 5

    def setup_user_agent(self):
        """Initialise le User-Agent avec gestion des erreurs."""
        try:
            self.ua = UserAgent()
        except FakeUserAgentError:
            logger.warning("Impossible d'utiliser FakeUserAgent. Utilisation d'un User-Agent par défaut.")
            self.ua = None

    def get_headers(self):
        """Crée des en-têtes HTTP pour simuler un navigateur."""
        default_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        return {
            "User-Agent": self.ua.random if self.ua else default_ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        }

    def build_url(self, offset):
        """Construit l'URL pour une page donnée."""
        return f"{self.base_url}&o=a{offset}"

    def make_request(self, url, retries=3):
        """Effectue une requête GET avec gestion des erreurs et mise à jour du User-Agent."""
        for attempt in range(retries):
            try:
                headers = self.get_headers()
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.warning(f"Requête échouée (tentative {attempt + 1}) : {str(e)}")
                if attempt == retries - 1:
                    raise
                time.sleep(randint(3, 7))

    def parse_restaurant(self, element):
        """Extrait les informations d'un restaurant."""
        try:
            name_elem = element.find('a', class_='Lwqic Cj b')
            return {
                'Nom': name_elem.text.strip() if name_elem else "N/A",
                'URL': urljoin(self.base_url, name_elem['href']) if name_elem and name_elem.has_attr('href') else "N/A"
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'un restaurant : {str(e)}")
            return None

    def scrape_page(self, offset):
        """Récupère les informations des restaurants sur une page spécifique."""
        url = self.build_url(offset)
        logger.info(f"Scraping des résultats à l'offset {offset} : {url}")

        try:
            content = self.make_request(url)
            soup = BeautifulSoup(content, 'html.parser')

            # Extraction des restaurants
            restaurant_divs = soup.find_all('div', class_='RfBGI')
            restaurants = []

            for div in restaurant_divs:
                data = self.parse_restaurant(div)
                if data:
                    restaurants.append(data)
                time.sleep(randint(1, 2))

            return restaurants
        except Exception as e:
            logger.error(f"Erreur lors du scraping de l'offset {offset} : {str(e)}")
            return []

    def scrape_all_pages(self, max_pages=50):
        """Récupère les informations des restaurants sur plusieurs pages."""
        all_restaurants = []
        empty_pages = 0

        for page_number in range(max_pages):
            offset = page_number * 30
            restaurants = self.scrape_page(offset)
            if restaurants:
                all_restaurants.extend(restaurants)
                empty_pages = 0
                logger.info(f"Offset {offset} : {len(restaurants)} restaurants trouvés.")
            else:
                empty_pages += 1
                if empty_pages >= 2:
                    logger.info("Arrêt du scraping après 2 pages vides consécutives.")
                    break
            time.sleep(randint(self.min_delay, self.max_delay))  # Pause entre les pages
            
        return pd.DataFrame(all_restaurants)

def main():
    base_url = "https://www.tripadvisor.fr/RestaurantSearch?geo=187265&sortOrder=popularity"
    scraper = TripAdvisorScraper(base_url)

    try:
        df = scraper.scrape_all_pages(max_pages=50)  # Scrape jusqu'à 50 pages
        if not df.empty:
            df.to_csv('restaurants_lyon.csv', index=False, encoding='utf-8-sig')
            logger.info(f"Scraping terminé avec succès : {len(df)} restaurants trouvés.")
        else:
            logger.error("Aucun restaurant trouvé.")
    except Exception as e:
        logger.error(f"Échec du scraping : {str(e)}")

if __name__ == "__main__":
    main()