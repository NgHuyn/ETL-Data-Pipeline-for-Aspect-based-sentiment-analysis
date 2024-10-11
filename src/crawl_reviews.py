from src.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from tqdm import tqdm  
from bs4 import BeautifulSoup
import json 

class MoviesScraper(BaseScraper):
    def __init__(self, clicks=200, release_date_from='2024-01-01', release_date_to='2024-10-07'):
        super().__init__()
        self.clicks = clicks
        self.movie_data = []
        self.release_date_from = release_date_from
        self.release_date_to = release_date_to

    def fetch_movies(self):
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

    def fetch_reviews(self):
        try:
            for movie in self.movie_data:  # Iterate through the list of movies
                movie_id = movie.get('Movie ID')  # Get Movie ID from the dictionary
                title = movie.get('Title')  # Get Title from the dictionary
                total_reviews = 0

                if movie_id and title:  # Check if both Movie ID and Title are present
                    for rating_filter in range(1, 11):  # Loop from 1 to 10
                        review_url = f"https://www.imdb.com/title/{movie_id}/reviews?sort=submissionDate&dir=desc&&ratingFilter={rating_filter}&rating={rating_filter}"
                        self.driver.get(review_url)

                        self._load_reviews()  # Load more reviews by clicking the button

                        wait_time = self._calculate_wait_time(10, self.clicks)  # Adjust wait time based on click count
                        time.sleep(wait_time)

                        html = self.driver.page_source
                        soup = BeautifulSoup(html, 'html.parser')

                        # Extract reviews for the current movie and accumulate total_reviews
                        # num_reviews = self._extract_reviews(soup, movie_id, title)
                        num_reviews = self._extract_reviews(soup, movie_id, title)
                        total_reviews += num_reviews  # Accumulate reviews count

                else:
                    print(f"Movie data missing for {movie}. Skipping this movie.")

                print(f'Movie {movie_id} has {total_reviews} reviews')
        finally:
            self.close_driver()
            self.is_scraping = False
        return self.movie_reviews

    def _load_reviews(self):
        # Try to find and click the 'All' reviews button
        try:
            all_reviews_button = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='__next']/main/div/section/div/section/div/div[1]/section[1]/div[3]/div/span[2]/button"))
            )
            # self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", all_reviews_button)
            # time.sleep(2)  # Wait for the page to load if needed
            all_reviews_button.click()
        except Exception as e:
            # Could not find 'All' button, will try to find 'Load More' button.
            self._load_more_reviews()


    def _load_more_reviews(self):
        # Add progress bar for loading more reviews
        with tqdm(desc='Loading More Reviews', leave=False) as pbar:
            while True:
                try:
                    load_more_button = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="load-more-trigger"]'))
                    )
                    # self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
                    load_more_button.click()

                    self.clicks += 1  # Increment the click count
                    pbar.update(1)  # Update progress bar

                    wait_time = self._calculate_wait_time(1, self.clicks)  # Adjust wait time based on click count
                    time.sleep(wait_time)

                except Exception as e:  # No more 'Load More' buttons to click.
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

        # Check if movie info already exists in the list
        movie_info = next((info for info in self.movie_reviews if info['Movie ID'] == movie_id), None)

        if movie_info is None:
            # Initialize a new movie_info if it doesn't exist
            movie_info = {
                'Movie ID': movie_id,
                'Reviews': []
            }
            self.movie_reviews.append(movie_info)  # Append to the main list

        # If no reviews found, try to load more reviews
        if not reviews:  # Load more
            reviews = soup.select('div.lister-item.mode-detail.imdb-user-review')
            if not reviews:  # If still no reviews available
                print(f"No reviews found for {title}.")
                return 0  # Return 0 if no reviews found

        # Parse reviews and add them to the movie_info['Reviews'] list
        for review in reviews:
            # Determine the button type (all vs. load more) based on the presence of specific elements
            button_type = "load_more" if review.select_one('span.rating-other-user-rating span') else "all"
            parsed_review = self._parse_review(review, button_type)

            # Append the parsed review to the 'Reviews' list
            movie_info['Reviews'].append(parsed_review)

        return len(reviews)  # Return the number of reviews processed

    def convert_to_int(human_readable):
        """Convert human-readable numbers to integers."""
        if 'K' in human_readable:
            return int(float(human_readable.replace('K', '').strip()) * 1000)
        elif 'M' in human_readable:
            return int(float(human_readable.replace('M', '').strip()) * 1000000)
        else:
            return int(human_readable.strip())

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

        # Extract helpful votes
        if button_type == "load_more":
            helpful_text = review.select_one('div.actions.text-muted').get_text(strip=True) if review.select_one('div.actions.text-muted') else ''
            match = re.search(r'(\d+) out of (\d+) found this helpful', helpful_text)
            if match:
                found_helpful = int(match.group(1))
                not_helpful = int(match.group(2)) - found_helpful
        else:
            found_helpful = convert_to_int(review.select_one('span.ipc-voting__label__count--up').get_text(strip=True)) if review.select_one('span.ipc-voting__label__count--up') else 0
            not_helpful = convert_to_int(review.select_one('span.ipc-voting__label__count--down').get_text(strip=True)) if review.select_one('span.ipc-voting__label__count--down') else 0

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



