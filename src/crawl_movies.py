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
import math

class MoviesScraper(BaseScraper):
    def __init__(self, release_date_from='2024-10-19', release_date_to='2024-10-20'): #2024-10-19,2024-10-20
        super().__init__()
        self.release_date_from = release_date_from
        self.release_date_to = release_date_to
        # self.clicks = math.ceil((num_movies-50) / 50) # Number of clicks depend on movies
        self.movie_data = []
        self.logger = setup_movies_scraper_logger()  # Initialize new logger

    def fetch_movies(self):
        try:
            url = f'https://www.imdb.com/search/title/?title_type=feature&release_date={self.release_date_from},{self.release_date_to}'

            self.driver.get(url)

            initial_html = self.driver.page_source
            initial_soup = BeautifulSoup(initial_html, 'html.parser')
            initial_movies = initial_soup.select('div.sc-59c7dc1-2')  # Save the initial elements

            # Extract data for the initial set of movies
            self.extract_movie_data(initial_movies)

            try:
                # get the element that have the total of movies
                total_movies_elements = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, 
                        '//*[@id="__next"]/main/div[2]/div[3]/section/section/div/section/section/div[2]/div/section/div[2]/div[2]/div[1]/div[1]'))
                )
                total_movies_text = total_movies_elements.text.split()[-1]
                total_movies = int(total_movies_text.replace('.', '')) 
                
                self.logger.info("Total reviews found: %s", total_movies)

                clicks = math.ceil((total_movies - 50) / 50)  
                self.logger.info("MoviesScraper initialized with %s clicks", clicks)

            except Exception as e:
                self.logger.error(f"Error fetching total reviews: {str(e)}")
            clicks = 1
            with tqdm(total=clicks, desc='Loading movies') as pbar:
                for _ in range(clicks):
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


    # def fetch_movies(self):
    #         try:
    #             url = f'https://www.imdb.com/search/title/?title_type=feature&release_date={self.release_date_from},{self.release_date_to}'
    #             self.driver.get(url)

    #             try:
    #                 # get the element that have the total of movies
    #                 total_movies_elements = WebDriverWait(self.driver, 2).until(
    #                     EC.presence_of_element_located((By.XPATH, 
    #                         '//*[@id="__next"]/main/div[2]/div[3]/section/section/div/section/section/div[2]/div/section/div[2]/div[2]/div[1]/div[1]'))
    #                 )
    #                 total_movies_text = total_movies_elements.text.split()[-1]
    #                 total_movies = int(total_movies_text.replace('.', '')) 
                    
    #                 self.logger.info("Total reviews found: %s", total_movies)

    #                 clicks = math.ceil((total_movies - 50) / 50)  
    #                 self.logger.info("MoviesScraper initialized with %s clicks", clicks)

    #             except Exception as e:
    #                 self.logger.error(f"Error fetching total reviews: {str(e)}")

    #             with tqdm(total=clicks, desc='Loading movies') as pbar:
    #                 for _ in range(clicks):
    #                     self.click_see_more_button()
    #                     pbar.update(1)
    #                     time.sleep(1)  # Optional wait time between clicks

    #             final_html = self.driver.page_source
    #             self.logger.info(final_html) 
    #             final_soup = BeautifulSoup(final_html, 'html.parser')
    #             final_movies = final_soup.select('div.sc-59c7dc1-2')
                          

    #             # After all clicks, extract movie data
    #             self.logger.info(final_movies)
    #             self.extract_movie_data(final_movies)

    #             self.logger.info("Completed fetching movies. Total movies: %d", len(self.movie_data))
    #         except Exception as e:
    #             self.logger.error("Error in fetch_movies: %s", str(e))
    #         finally:
    #             self.close_driver()
    #         return self.movie_data


    def click_see_more_button(self):
        try:
            # initial_elements = self.driver.find_elements(By.CLASS_NAME, 'ipc-title')
            # initial_count = len(initial_elements)

            see_more_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'more')]"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", see_more_button)
            self.logger.info("Clicked 'Load More' button successfully.")

            # for _ in range(5):
            #     current_elements = self.driver.find_elements(By.CLASS_NAME, 'ipc-title')
            #     current_count = len(current_elements)

            #     if current_count > initial_count:
            #         break
            #     time.sleep(1)
            # return 

        except Exception as e:
            self.logger.warning(f"No more 'See More' buttons found")
            return None
            #             try:
            #             see_more_button = WebDriverWait(self.driver, 10).until(
            #     EC.element_to_be_clickable((By.XPATH, "//*[@id="__next"]/main/div[2]/div[3]/section/section/div/section/section/div[2]/div/section/div[2]/div[2]/div[2]/div/span/button/span/span"))
            # )
            # self.driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", see_more_button)
            # self.logger.info("Clicked 'Load More' button successfully.")

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
            self.logger.info("Finished extraction of movie data.")