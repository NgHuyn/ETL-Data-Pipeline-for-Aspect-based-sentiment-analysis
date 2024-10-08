from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Base class for handling common WebDriver functionalities
class BaseScraper:
    def __init__(self):
        self.driver = self.init_driver()

    def init_driver(self):
        service = Service()
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def close_driver(self):
        self.driver.quit()




    

