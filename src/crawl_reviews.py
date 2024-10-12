from src.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from tqdm import tqdm  
from bs4 import BeautifulSoup
from datetime import datetime, date
import logging
import os

# # Thiết lập logging
# logging.basicConfig(
#     filename='scraping.log',  # Tên file log
#     filemode='a',  # Append log vào file đã có
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO  # Chỉ ghi log từ cấp INFO trở lên
# )
# logger = logging.getLogger(__name__)

def setup_logger(movie_id):
    # Tạo thư mục logs nếu chưa tồn tại
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Đặt tên file log theo movie_id
    logger = logging.getLogger(movie_id)
    logger.setLevel(logging.INFO)
    
    # Tạo file handler
    file_handler = logging.FileHandler(f'logs/{movie_id}_reviews.log', mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Thêm handler vào logger
    if not logger.handlers:
        logger.addHandler(file_handler)
    
    return logger

class MoviesScraper(BaseScraper):
    def __init__(self, clicks=200, release_date_from='2024-01-01', release_date_to='2024-10-07'):
        super().__init__()
        self.clicks = clicks
        self.movie_data = []
        self.release_date_from = release_date_from
        self.release_date_to = release_date_to
        logger.info("MoviesScraper initialized with %s clicks", self.clicks)

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
                    soup = self.click_see_more_button()
                    pbar.update(1)
                    time.sleep(1)  # Optional wait time between clicks

            final_html = self.driver.page_source
            final_soup = BeautifulSoup(final_html, 'html.parser')
            final_movies = final_soup.select('div.sc-59c7dc1-2')

            # After all clicks, extract movie data
            new_movies = final_movies[len(initial_movies):]
            self.extract_movie_data(new_movies)

            logger.info("Completed fetching movies. Total movies: %d", len(self.movie_data))
        except Exception as e:
            logger.error("Error in fetch_movies: %s", str(e))
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

            return BeautifulSoup(self.driver.page_source, 'html.parser')

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

# ReviewsScraper class to fetch reviews for each movie
class MovieReviewScraper(BaseScraper):
    def __init__(self, movie_data):
        super().__init__()  # Call the base class constructor
        self.movie_data = movie_data  # Load movie data from movie data
        self.movie_reviews = []  # Adjusted to be a list of movie objects
        self.clicks = 0  # Initialize click counter
        self.is_scraping = True  # Flag to manage scraping status
        logger.info("MovieReviewScraper initialized")

    def fetch_reviews(self):
        try:
            for movie in self.movie_data:  # Iterate through the list of movies
                movie_id = movie.get('Movie ID')  # Get Movie ID from the dictionary
                title = movie.get('Title')  # Get Title from the dictionary
                total_reviews = 0
                total_actual_reviews = 0

                if movie_id and title:  # Check if both Movie ID and Title are present
                    for rating_filter in range(1, 11):  # Loop from 1 to 10
                        review_url = f"https://www.imdb.com/title/{movie_id}/reviews?sort=submissionDate&dir=desc&ratingFilter={rating_filter}&rating={rating_filter}"
                        self.driver.get(review_url)

                        # Check if there are any reviews available
                        review_count = self._get_total_reviews()
                        if review_count == 0:
                            logger.info("No reviews found for Movie ID %s with rating %d", movie_id, rating_filter)
                            continue  # Skip to the next rating filter if no reviews

                        # If reviews are available, attempt to load all or more reviews
                        self._load_reviews()  # Load more reviews by clicking the button
                        wait_time = self._calculate_wait_time(10, self.clicks)  # Adjust wait time based on click count
                        time.sleep(wait_time)

                        # Extract reviews from the loaded page
                        html = self.driver.page_source
                        soup = BeautifulSoup(html, 'html.parser')

                        # Extract reviews for the current movie and accumulate total_reviews
                        num_reviews = self._extract_reviews(soup, movie_id, title)
                        total_reviews += review_count
                        total_actual_reviews += num_reviews  # Accumulate reviews count

                logger.info('Movie %s has %d/%d reviews', movie_id, total_actual_reviews, total_reviews)
        except Exception as e:
            logger.error("Error in fetch_reviews: %s", str(e))
        finally:
            self.close_driver()
            self.is_scraping = False
        return self.movie_reviews

    def _get_total_reviews(self):
        """Fetch the total number of reviews from the page."""
        try:
            # Attempt to find the total reviews element by data-testid
            total_reviews_element = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="tturv-total-reviews"]'))
            )
            total_reviews_text = total_reviews_element.text.split()[0]  # Get the number part
            logger.info("Total reviews found: %s", total_reviews_text)
            return int(total_reviews_text)
        except Exception as e:
            # If the first attempt fails, check the alternative method
            try:
                total_reviews_element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="header"]//span'))
                )
                total_reviews_text = total_reviews_element.text.split()[0]  # Get the number part
                logger.info("Total reviews found: %s", total_reviews_text)
                return int(total_reviews_text)
            except Exception as e:
                logger.error("Error fetching total reviews: %s", e)
                return 0  # Default to 0 if neither element is found

    # def _load_reviews(self):
    #     try:
    #         # Find and click the 'All' button
    #         all_reviews_button = WebDriverWait(self.driver, 10).until(
    #             EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/main/div/section/div/section/div/div[1]/section[1]/div[3]/div/span[2]/button/span/span'))
    #         )
    #         self.driver.execute_script(
    #             "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", 
    #             all_reviews_button
    #         )
    #         time.sleep(4)  # Wait for the page to load after clicking
    #         logger.info("Clicked 'All' reviews button and waiting for the page to load.")

    #         # Scroll slowly to ensure all content loads
    #         last_height = self.driver.execute_script("return document.body.scrollHeight")
    #         logger.info("Starting to scroll to load all reviews.")

    #         while True:
    #             self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    #             time.sleep(2)  # Wait for content to load after each scroll

    #             # Check the new height of the page
    #             new_height = self.driver.execute_script("return document.body.scrollHeight")
    #             if new_height == last_height:  # If there is no more content to load, stop
    #                 logger.info("Reached the bottom of the page, all reviews loaded.")
    #                 break
    #             last_height = new_height

    #     except Exception as e:
    #         logger.error("Error loading 'All' reviews")

    #         # If the 'All' button is not found, try to find the 'Load More' button
    #         try:
    #             load_more_button = WebDriverWait(self.driver, 5).until(
    #                 # EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Load More')]"))
    #                 EC.element_to_be_clickable((By.XPATH, '//*[@id="load-more-trigger"]'))
    #             )
    #             self.driver.execute_script("arguments[0].click();", load_more_button)
    #             time.sleep(4)  # Wait after clicking
    #             logger.info("Clicked 'Load More' button to load more reviews.")
    #         except Exception as e:
    #             try:
    #                 more_button = WebDriverWait(self.driver, 5).until(
    #                     EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/main/div/section/div/section/div/div[1]/section[1]/div[3]/div/span[1]/button/span/span'))
    #                 )
    #                 self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", more_button)
    #                 time.sleep(4)  # Chờ sau khi click
    #                 logger.info("Clicked 'More' button to load more reviews.")
    #             except Exception as e:
    #                 logger.info("No more button found to click.")

    def _load_reviews(self):
        def click_button(xpath, name, wait=5):
            """Helper function to find and click a button if available."""
            try:
                button = WebDriverWait(self.driver, wait).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", 
                    button
                )
                time.sleep(4)  # Wait for content to load after clicking
                logger.info(f"Clicked '{name}' button successfully.")
                return True
            except Exception:
                logger.info(f"No '{name}' button found.")
                return False

        # 1. Try clicking the 'All' button first
        if click_button('//*[@id="__next"]/main/div/section/div/section/div/div[1]/section[1]/div[3]/div/span[2]/button/span/span', 'All'):
            logger.info("Clicked 'More' button successfully.")
            self._scroll_to_load_all()  # Scroll if 'All' button is clicked
            return  # Stop after 'All' is clicked

        # 2. Continuously click 'Load More' button until it no longer appears
        while True:
            if not click_button('//*[@id="load-more-trigger"]', 'Load More'):
                logger.info("No more 'Load More' buttons found, moving to 'More' button check.")
                break  # Exit the loop when 'Load More' is no longer available

        # 3. Try clicking the 'More' button if it exists
        if click_button('//*[@id="__next"]/main/div/section/div/section/div/div[1]/section[1]/div[3]/div/span[1]/button/span/span', 'More'):
            logger.info("Clicked 'More' button successfully.")
        else:
            logger.info("No 'More' button found, all reviews loaded.")

    def _scroll_to_load_all(self):
        """Scroll the page slowly to ensure all reviews are loaded."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        logger.info("Starting to scroll to load all reviews.")

        while True:
            # Scroll to the bottom of the page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for new content to load after each scroll

            # Check if the new page height is the same as the previous one
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # Stop if no more content is being loaded
                logger.info("Reached the bottom of the page, all reviews loaded.")
                break
            last_height = new_height

    def _calculate_wait_time(self, base_wait_time, clicks):
        """
        Calculate an adaptive wait time based on the number of clicks.
        As the number of clicks increases, the wait time grows exponentially to accommodate website lag.
        """
        growth_factor = 1.2  # Exponential growth factor
        additional_wait_time = base_wait_time * (growth_factor ** (clicks // 10))  # Increase wait time every 10 clicks
        
        return base_wait_time + additional_wait_time


    def _extract_reviews(self, soup, movie_id, title):
        # Attempt to extract reviews using the primary selector
        reviews = soup.select('article.user-review-item')

        # Check if movie info already exists in the list
        movie_info = next((info for info in self.movie_reviews if info['Movie ID'] == movie_id), None)

        if movie_info is None:
            # Initialize a new movie_info if it doesn't exist
            movie_info = {
                'Movie ID': movie_id,
                'Reviews': []
            }
            self.movie_reviews.append(movie_info)  # Append to the main list
            logger.info(f"Initialized new movie info for Movie ID: {movie_id}, Title: {title}.")

        # If no reviews found, try to load more reviews
        if not reviews:  # Attempt to load more reviews
            reviews = soup.select('div.lister-item.mode-detail.imdb-user-review')
            if not reviews:  # If still no reviews available
                logger.warning(f"No reviews found for {title}.")
                return 0  # Return 0 if no reviews found

        # Parse reviews and add them to the movie_info['Reviews'] list
        for review in reviews:
            # Determine the button type (all vs. load more) based on the presence of specific elements
            button_type = "load_more" if review.select_one('span.rating-other-user-rating span') else "all"
            parsed_review = self._parse_review(review, button_type)

            # Append the parsed review to the 'Reviews' list
            movie_info['Reviews'].append(parsed_review)
            logger.info(f"Added review for Movie ID: {movie_id}, Title: {title}, Button Type: {button_type}.")

        logger.info(f"Processed {len(reviews)} reviews for Movie ID: {movie_id}, Title: {title}.")
        return len(reviews)  # Return the number of reviews processed


    def convert_to_int(self, human_readable):
        """Convert human-readable numbers to integers."""
        if 'K' in human_readable:
            return int(float(human_readable.replace('K', '').strip()) * 1000)
        elif 'M' in human_readable:
            return int(float(human_readable.replace('M', '').strip()) * 1000000)
        else:
            return int(human_readable.strip())

    def _parse_review(self, review, button_type):
        """
        Extract information from the review based on its type (load_more or all)
        """
        # Initialize helpful votes to 0
        found_helpful = 0
        not_helpful = 0

        # Parse review based on the button type
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

        # Extract helpful votes
        if button_type == "load_more":
            helpful_text = review.select_one('div.actions.text-muted').get_text(strip=True) if review.select_one('div.actions.text-muted') else ''
            match = re.search(r'(\d+) out of (\d+) found this helpful', helpful_text)
            if match:
                found_helpful = int(match.group(1))
                not_helpful = int(match.group(2)) - found_helpful
                logger.info(f"Found {found_helpful} helpful votes and {not_helpful} not helpful votes for the review.")
        else:
            found_helpful = self.convert_to_int(review.select_one('span.ipc-voting__label__count--up').get_text(strip=True)) if review.select_one('span.ipc-voting__label__count--up') else 0
            not_helpful = self.convert_to_int(review.select_one('span.ipc-voting__label__count--down').get_text(strip=True)) if review.select_one('span.ipc-voting__label__count--down') else 0
            logger.info(f"Found {found_helpful} helpful votes and {not_helpful} not helpful votes for the review.")

        # Log the parsed review details
        logger.info(f"Parsed review for Author: {author_tag}, Rating: {review_rating}, Date: {review_date}")

        # Return the review information in the expected format
        return {
            'Review Summary': review_summary,
            'Review': review_text,
            'Rating': review_rating,
            'Author': author_tag,
            'Date': review_date,
            'Helpful': found_helpful,
            'Not Helpful': not_helpful
        }
