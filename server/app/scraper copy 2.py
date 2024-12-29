import os
import platform
import winreg
from pathlib import Path

def get_chrome_path():
    """Get Chrome path from Windows registry or common locations"""
    try:
        if platform.system() == 'Windows':
            # Try registry first
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
            chrome_path = winreg.QueryValue(key, None)
            if os.path.exists(chrome_path):
                return chrome_path

            # Common installation paths
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
    except:
        return None

def create_driver(self):
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    chrome_path = get_chrome_path()
    if chrome_path:
        options.binary_location = chrome_path
    
    try:
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logger.error(f"Failed to create driver: {str(e)}")
        raise


# test

print(get_chrome_path()) # expected: path to Chrome executable
