import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent, FakeUserAgentError
import pandas as pd
import time
from random import randint
import logging
from urllib.parse import urljoin

# Configuration du logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TripAdvisorScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.setup_user_agent()
        self.session = requests.Session()
        self.min_delay = 3  # Délai minimum entre les requêtes
        self.max_delay = 7  # Délai maximum entre les requêtes

    def setup_user_agent(self):
        """Initialise le User-Agent avec une gestion des erreurs."""
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

    def make_request(self, url, retries=3):
        """Effectue une requête HTTP avec gestion des erreurs."""
        for attempt in range(retries):
            try:
                response = self.session.get(url, headers=self.get_headers(), timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.warning(f"Tentative {attempt + 1} échouée pour {url} : {str(e)}")
                if attempt == retries - 1:
                    raise
                time.sleep(randint(5, 10))  # Attente avant une nouvelle tentative

    def parse_restaurant(self, element):
        """Extrait les informations d'un restaurant."""
        try:
            print(element.find_all('div', {"data-test-target": "restaurants-list"}))

            # name_elem = element.find('div', class_='RfBGI')
            name_elem = element.find('a', {"data-test-target": "restaurants-list"})
            print('111111',name_elem)
            # rating_elem = element.find('svg', {'aria-label': True})
            # reviews_elem = element.find('span', {'data-test': 'reviews-count'})
            # price_elem = element.find('span', {'data-test': 'price-range'})

            return {
                'Nom': name_elem.text.strip() if name_elem else "N/A",
                # 'Note': rating_elem['aria-label'].split()[0] if rating_elem else "N/A",
                # 'Nombre d\'Avis': reviews_elem.text.strip().split()[0] if reviews_elem else "0",
                # 'Prix': price_elem.text.strip() if price_elem else "N/A",
                # 'URL': urljoin(self.base_url, name_elem['href']) if name_elem and name_elem.has_attr('href') else "N/A"
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'un restaurant : {str(e)}")
            return None

    def scrape_page(self, page_number):
        """Scrape les restaurants d'une page donnée."""
        url = f"{self.base_url}&o=a{page_number * 30}"
        logger.info(f"Scraping de la page {page_number + 1} : {url}")

        try:
            content = self.make_request(url)
            soup = BeautifulSoup(content, 'html.parser')
            
            with open(f"page_{page_number + 1}.html", 'w', encoding='utf-8') as f:
                f.write(str(soup))

            restaurant_divs = soup.find_all('div', {"data-test": "restaurant-item"})
            if not restaurant_divs:
                logger.warning(f"Aucun restaurant trouvé sur la page {page_number + 1}")
                return []

            restaurants = []
            for div in restaurant_divs:
                data = self.parse_restaurant(div)
                if data:
                    restaurants.append(data)
                time.sleep(randint(1, 2))  # Délai entre les analyses

            return restaurants

        except Exception as e:
            logger.error(f"Erreur lors du scraping de la page {page_number + 1} : {str(e)}")
            return []

    def scrape_restaurants(self, num_pages=1):
        """Scrape plusieurs pages de restaurants."""
        all_restaurants = []

        for page in range(num_pages):
            restaurants = self.scrape_page(page)
            if restaurants:
                all_restaurants.extend(restaurants)
                logger.info(f"Page {page + 1} : {len(restaurants)} restaurants trouvés.")
            else:
                logger.warning(f"Aucune donnée pour la page {page + 1}. Arrêt potentiel.")
                break
            time.sleep(randint(self.min_delay, self.max_delay))  # Délai entre les pages

        return pd.DataFrame(all_restaurants)

def main():
    # URL de base pour les restaurants de Lyon sur TripAdvisor
    base_url = "https://www.tripadvisor.fr/RestaurantSearch?geo=187265&sortOrder=popularity"
    scraper = TripAdvisorScraper(base_url)

    try:
        # Nombre de pages à scraper
        num_pages = 5
        df = scraper.scrape_restaurants(num_pages=num_pages)
        if not df.empty:
            df.to_csv('restaurants_lyon.csv', index=False, encoding='utf-8-sig')
            logger.info(f"Scraping terminé avec succès : {len(df)} restaurants enregistrés dans 'restaurants_lyon.csv'")
        else:
            logger.error("Aucun restaurant trouvé.")
    except Exception as e:
        logger.error(f"Échec du scraping : {str(e)}")

if __name__ == "__main__":
    main()
