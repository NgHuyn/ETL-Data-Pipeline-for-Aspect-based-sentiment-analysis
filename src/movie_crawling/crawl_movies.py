from .base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from tqdm import tqdm  
from bs4 import BeautifulSoup
from .utils import setup_movies_scraper_logger
import math

class MoviesScraper(BaseScraper):
    def __init__(self, release_date_from='2024-01-01', release_date_to='2024-10-01'):
        super().__init__()
        self.release_date_from = release_date_from
        self.release_date_to = release_date_to
        self.movie_data = []
        self.logger = setup_movies_scraper_logger()  # Initialize new logger

    def fetch_movies(self, limit=10):
            try:
                url = f'https://www.imdb.com/search/title/?title_type=feature&release_date={self.release_date_from},{self.release_date_to}'
                self.driver.get(url)

                try:
                    # get the element that have the total of movies
                    total_movies_elements = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.XPATH, 
                            '//*[@id="__next"]/main/div[2]/div[3]/section/section/div/section/section/div[2]/div/section/div[2]/div[2]/div[1]/div[1]'))
                    )
                    total_movies_text = total_movies_elements.text.split()[-1]
                    total_movies_found = int(total_movies_text.replace(',', '')) 
                    self.logger.info("Total reviews found: %s", total_movies_found)

                    if limit is None:
                        limit = total_movies_found
                    clicks = math.ceil((limit - 50) / 50)  
                    self.logger.info("MoviesScraper initialized with %s clicks", clicks)

                except Exception as e:
                    self.logger.error(f"Error fetching total movies: {str(e)}")

                # clicking for loading more movies
                with tqdm(total=clicks, desc='Loading movies') as pbar:
                    for _ in range(clicks):
                        self.click_see_more_button()
                        pbar.update(1)
                        time.sleep(1)  # Optional wait time between clicks

                 # After all clicks, extract movie data
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                self.extract_movie_data(soup, limit)

                self.logger.info("Completed fetching movies. Total movies: %d", len(self.movie_data))
            except Exception as e:
                self.logger.error("Error in fetch_movies: %s", str(e))
            finally:
                self.close_driver()
            return self.movie_data


    def click_see_more_button(self):
        try:
            see_more_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/main/div[2]/div[3]/section/section/div/section/section/div[2]/div/section/div[2]/div[2]/div[2]/div/span/button'))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", see_more_button)
            self.logger.info("Clicked 'Load More' button successfully.")
            
        except Exception as e:
            self.logger.warning(f"No more 'See More' buttons found")
            return None

    def extract_movie_data(self, soup, limit):
        movies = soup.select('li.ipc-metadata-list-summary-item')
        
        if limit is not None:
            movies = movies[:limit]

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

            self.movie_data.append({
                'Movie ID': movie_id,
                'Title': title,
            })
        self.logger.info("Finished extraction of movie data.")