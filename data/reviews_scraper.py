from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from data.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import time
import json
from tqdm import tqdm  

# ReviewsScraper class to fetch reviews for each movie
class MovieReviewScraper(BaseScraper):
    def __init__(self, json_file_path):
        super().__init__()  # Call the base class constructor
        self.json_file_path = json_file_path  # Path to the JSON file
        self.movie_data = self._load_movies_from_json()  # Load movie data from JSON
        self.movie_reviews = []  # Adjusted to be a list of movie objects
        self.clicks = 0  # Initialize click counter

    def _load_movies_from_json(self):
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)  # Load JSON data

    def fetch_reviews(self):
        for movie in self.movie_data:  # Iterate through the list of movies
            movie_id = movie['Movie ID']
            title = movie['Title']
            review_url = f"https://www.imdb.com/title/{movie_id}/reviews"
            self.driver.get(review_url)

            self._load_reviews()

            wait_time = self._calculate_wait_time(10, self.clicks)  # Adjust wait time based on click count
            time.sleep(wait_time)

            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            self._extract_reviews(soup, movie_id, title)

        self.close_driver()
        self.movie_reviews

    def _load_reviews(self):
        # Try to find and click the 'All' reviews button
        try:
            all_reviews_button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='__next']/main/div/section/div/section/div/div[1]/section[1]/div[3]/div/span[2]/button"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", all_reviews_button)
            time.sleep(2)  # Wait for the page to load if needed
            all_reviews_button.click()
        except Exception as e:
            print("Could not find 'All' button, will try to find 'Load More' button.")
            self._load_more_reviews()

    def _load_more_reviews(self):
        # Add progress bar for loading more reviews
        with tqdm(total=10, desc='Loading More Reviews', leave=False) as pbar:
            while True:
                try:
                    load_more_button = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="load-more-trigger"]'))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
                    load_more_button.click()

                    self.clicks += 1  # Increment the click count
                    pbar.update(1)  # Update progress bar

                    wait_time = self._calculate_wait_time(1, self.clicks)  # Adjust wait time based on click count
                    time.sleep(wait_time)

                except Exception as e:
                    print("No more 'Load More' buttons to click.")
                    break

    def _calculate_wait_time(self, base_wait_time, clicks):
        """
        Calculate an adaptive wait time based on the number of clicks.
        As the number of clicks increases, the wait time grows exponentially to accommodate website lag.
        """
        growth_factor = 1.2  # Exponential growth factor
        additional_wait_time = base_wait_time * (growth_factor ** (clicks // 10))  # Increase wait time every 10 clicks
        
        return base_wait_time + additional_wait_time


    def _extract_reviews(self, soup, movie_id, title):
        reviews = soup.select('article.user-review-item')  # Attempt to extract reviews using one selector
        movie_info = {
            'Movie ID': movie_id,
            'Reviews': []
        }
        # If no reviews found, try to load more reviews
        if not reviews:  
            reviews = soup.select('div.lister-item.mode-detail.imdb-user-review')
            if not reviews: # If still no reviews available
                print(f"No reviews found for {title}.")
                return

            for review in reviews:
                parsed_review = self._parse_review(review, "load_more")
                movie_info['Reviews'].append(parsed_review)
        else: # If "all" button found
            for review in reviews:
                parsed_review = self._parse_review(review, "all")
                movie_info['Reviews'].append(parsed_review)

        self.movie_reviews.append(movie_info)

        # Count the number of reviews and display it
        num_reviews = len(movie_info['Reviews'])
        print(f"Total number of reviews for '{title}': {num_reviews}")

    def _parse_review(self, review, button_type):
        """
        Extract information from the review and return as a dictionary.
        """
        # Extract information from the review based on its type (load_more or all)
        if button_type == "load_more":
            review_rating = review.select_one('span.rating-other-user-rating span').get_text(strip=True) if review.select_one('span.rating-other-user-rating span') else 'No rating'
            review_summary = review.select_one('a.title').get_text(strip=True) if review.select_one('a.title') else 'No summary'
            review_text = review.select_one('div.text.show-more__control').get_text(strip=True) if review.select_one('div.text.show-more__control') else 'No content'
            author_tag = review.select_one('span.display-name-link a').get_text(strip=True) if review.select_one('span.display-name-link a') else 'Unknown Author'
            review_date = review.select_one('span.review-date').get_text(strip=True) if review.select_one('span.review-date') else 'No date'
        else:
            review_rating = review.select_one('span.ipc-rating-star--rating').get_text(strip=True) if review.select_one('span.ipc-rating-star--rating') else 'No rating'
            review_summary = review.select_one('span[data-testid="review-summary"]').get_text(strip=True) if review.select_one('span[data-testid="review-summary"]') else 'No summary'
            review_text = review.select_one('div.ipc-html-content-inner-div').get_text(strip=True) if review.select_one('div.ipc-html-content-inner-div') else 'No content'
            author_tag = review.select_one('a[data-testid="author-link"]').get_text(strip=True) if review.select_one('a[data-testid="author-link"]') else 'Unknown Author'
            review_date = review.select_one('li.review-date').get_text(strip=True) if review.select_one('li.review-date') else 'No date'

        # Return the review information in the expected format
        return {
            'Review Summary': review_summary,
            'Review': review_text,
            'Rating': review_rating,
            'Author': author_tag,
            'Date': review_date
        }
    def save_to_json(self):
        with open('movie_reviews.json', 'w', encoding='utf-8') as f:
            json.dump(self.movie_reviews, f, ensure_ascii=False, indent=4)
        print("Reviews saved to movie_reviews.json")