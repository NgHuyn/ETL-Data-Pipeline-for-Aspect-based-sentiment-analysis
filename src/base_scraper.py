from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Base class for handling common WebDriver functionalities
class BaseScraper:
    def __init__(self):
        self.driver = self.init_driver()

    def init_driver(self):
        service = Service()  # Initialize the service
        options = webdriver.ChromeOptions()
        
        # Set Chrome options to reduce memory usage
        options.headless = True  # Enable headless mode
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--no-sandbox")  # Use this if you encounter issues

        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def close_driver(self):
        self.driver.quit()

