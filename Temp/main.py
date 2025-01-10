from undetected_chromedriver import Chrome, ChromeOptions

# Configuration des options pour Chrome
options = ChromeOptions()
options.add_argument('--headless')  # Exécuter sans interface graphique
options.add_argument('--no-sandbox')  # Nécessaire pour Docker
options.add_argument('--disable-dev-shm-usage')  # Évite les problèmes de /dev/shm
options.add_argument('--disable-gpu')  # Optionnel pour les environnements sans GPU
options.add_argument('--disable-extensions')
options.add_argument('--remote-debugging-port=9222')  # Pour le debugging dans Docker

# Initialisation de Selenium avec undetected_chromedriver
try:
    driver = Chrome(options=options)
    driver.get("https://www.google.com")
    print(f"Title of the page is: {driver.title}")
finally:
    driver.quit()
