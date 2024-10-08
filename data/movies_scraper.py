from data.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from tqdm import tqdm  
from bs4 import BeautifulSoup
import json 

# MoviesScraper class to fetch movies
class MoviesScraper(BaseScraper):
    def __init__(self, clicks=2):
        super().__init__()  # Call the base class constructor
        self.clicks = clicks  # Number of times to click the "50 more" button
        self.movie_data = []

    def fetch_movies(self):
        url = 'https://www.imdb.com/search/title/?title_type=feature'
        self.driver.get(url)

        # Click on "50 more" button for the specified number of clicks
        with tqdm(total=self.clicks, desc='Loading movies') as pbar:
            for _ in range(self.clicks):
                soup = self.click_see_more_button()  # Re-fetch HTML after each click if successful
                # movies = soup.select('div.sc-59c7dc1-2')  # Adjust the selector based on your data structure
                # print(f"Movies loaded after click {_+1}: {len(movies)}")  # Check the number of loaded movies after each click
                pbar.update(1)  # Update the progress bar for each click

        # Calculate and apply the wait time based on the number of clicks
        wait_time = self._calculate_wait_time(self.clicks)
        time.sleep(wait_time)  # Adjust wait time based on clicks

        # After all clicks, extract the final set of movie data
        html = self.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        movies = soup.select('div.sc-59c7dc1-2')
        self.extract_movie_data(movies)  # Extract all data after final click

        self.close_driver()  # Close the driver after fetching movies

        return self.movie_data

    def click_see_more_button(self):
        try:
            # Get the current number of 'ipc-title' elements before clicking
            initial_elements = self.driver.find_elements(By.CLASS_NAME, 'ipc-title')
            initial_count = len(initial_elements)

            see_more_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '50 more')]"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", see_more_button)

            # Retry up to 5 times to confirm that new content has been loaded
            for _ in range(5):
                current_elements = self.driver.find_elements(By.CLASS_NAME, 'ipc-title')
                current_count = len(current_elements)

                if current_count > initial_count:
                    break  # New content detected
                time.sleep(1)  # Brief wait before rechecking

            return BeautifulSoup(self.driver.page_source, 'html.parser')

        except Exception as e:
            print(f"Error occurred: {e}")
            return None


    def extract_movie_data(self, movies):
        for movie in movies:
            title_tag = movie.select_one('h3.ipc-title__text') if movie.select_one('h3.ipc-title__text') else None
            link_tag = movie.select_one('a.ipc-title-link-wrapper') if movie.select_one('a.ipc-title-link-wrapper') else None  # if don't have link -> can't find the review or movie id -> skip that movie

            title = title_tag.text.strip() if title_tag else 'N/A'
            link = link_tag['href']

            if link_tag:
                link = link_tag['href']

                # Extract movie ID
                movie_id = link.split('/title/')[1].split('/')[0]
            else:
                movie_id = 'N/A'

            # Clean the title
            title = re.sub(r'^\d+\.\s*', '', title)

            # Adding the data
            self.movie_data.append({
                'Movie ID': movie_id,
                'Title': title,
            })
    
    def _calculate_wait_time(self, clicks):
        """
        Calculate an adaptive wait time based on the number of clicks.
        As the number of clicks increases, the wait time grows exponentially to accommodate website lag.
        """
        base_wait_time = 5  # Base wait time in seconds
        growth_factor = 1.2  # Exponential growth factor
        additional_wait_time = base_wait_time * (growth_factor ** (clicks // 10))  # Increase wait time every 10 clicks
        
        return base_wait_time + additional_wait_time
    
    def save_to_json(self, file_name='movies_data.json'):
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(self.movie_data, file, ensure_ascii=False, indent=4)