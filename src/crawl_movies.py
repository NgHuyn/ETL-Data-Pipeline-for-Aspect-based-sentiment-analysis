from src.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from tqdm import tqdm  
from bs4 import BeautifulSoup
from datetime import datetime, date
from .utils import setup_movies_scraper_logger

class MoviesScraper(BaseScraper):
    def __init__(self, clicks=200, release_date_from='2024-01-01', release_date_to='2024-10-07'):
        super().__init__()
        self.clicks = clicks
        self.movie_data = []
        self.release_date_from = release_date_from
        self.release_date_to = release_date_to
        self.logger = setup_movies_scraper_logger()  # Khởi tạo logger
        self.logger.info("MoviesScraper initialized with %s clicks", self.clicks)

    def fetch_movies(self):
        try:
            url = f'https://www.imdb.com/search/title/?title_type=feature&release_date={self.release_date_from},{self.release_date_to}'
            self.driver.get(url)

            initial_html = self.driver.page_source
            initial_soup = BeautifulSoup(initial_html, 'html.parser')
            initial_movies = initial_soup.select('div.sc-59c7dc1-2')  # Save the initial elements

            # Extract data for the initial set of movies
            self.extract_movie_data(initial_movies)

            with tqdm(total=self.clicks, desc='Loading movies') as pbar:
                for _ in range(self.clicks):
                    self.click_see_more_button()
                    pbar.update(1)
                    time.sleep(1)  # Optional wait time between clicks

            final_html = self.driver.page_source
            final_soup = BeautifulSoup(final_html, 'html.parser')
            final_movies = final_soup.select('div.sc-59c7dc1-2')

            # After all clicks, extract movie data
            new_movies = final_movies[len(initial_movies):]
            self.extract_movie_data(new_movies)

            self.logger.info("Completed fetching movies. Total movies: %d", len(self.movie_data))
        except Exception as e:
            self.logger.error("Error in fetch_movies: %s", str(e))
        finally:
            self.close_driver()
        return self.movie_data

    def click_see_more_button(self):
        try:
            initial_elements = self.driver.find_elements(By.CLASS_NAME, 'ipc-title')
            initial_count = len(initial_elements)

            see_more_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '50 more')]"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", see_more_button)

            for _ in range(5):
                current_elements = self.driver.find_elements(By.CLASS_NAME, 'ipc-title')
                current_count = len(current_elements)

                if current_count > initial_count:
                    break
                time.sleep(1)

            return 

        except Exception as e:
            print(f"Error occurred: {e}")
            return None

    def extract_movie_data(self, movies):
        existing_movie_ids = {movie['Movie ID'] for movie in self.movie_data}  # Set of existing movie IDs

        for movie in movies:
            title_tag = movie.select_one('h3.ipc-title__text')
            link_tag = movie.select_one('a.ipc-title-link-wrapper')

            title = title_tag.text.strip() if title_tag else 'N/A'
            link = link_tag['href'] if link_tag else None

            if link_tag:
                movie_id = link.split('/title/')[1].split('/')[0]
            else:
                movie_id = 'N/A'

            title = re.sub(r'^\d+\.\s*', '', title)

            if movie_id not in existing_movie_ids:  # Only add if movie_id is not already in the list
                self.movie_data.append({
                    'Movie ID': movie_id,
                    'Title': title,
                })

    def _calculate_wait_time(self, clicks):
        base_wait_time = 5
        growth_factor = 1.2
        additional_wait_time = base_wait_time * (growth_factor ** (clicks // 10))
        return base_wait_time + additional_wait_time