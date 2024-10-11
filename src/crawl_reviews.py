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
    def __init__(self, clicks=200, batch_size=20, save_file='movies_data.json'):
        super().__init__()
        self.clicks = clicks
        self.batch_size = batch_size
        self.save_file = save_file
        self.movie_data = []

    def fetch_movies(self):
        url = 'https://www.imdb.com/search/title/?title_type=feature&release_date=2024-01-01,2024-10-31'
        self.driver.get(url)

        total_batches = self.clicks // self.batch_size  # Calculate total batches
        remaining_clicks = self.clicks % self.batch_size  # Remaining clicks after batches

        for batch in range(total_batches):
            try:
                print(f"Processing batch {batch + 1}/{total_batches}...")
                self._process_batch(self.batch_size)
            except Exception as e:
                print(f"Error occurred in batch {batch + 1}: {e}")
                break # stop the process after an error

        # Process any remaining clicks
        if remaining_clicks > 0:
            try:
                print(f"Processing remaining {remaining_clicks} clicks...")
                self._process_batch(remaining_clicks)
            except Exception as e:
                print(f"Error occurred: {e}")

        self.close_driver()
        return self.movie_data

    def _process_batch(self, num_clicks):
        """Process a batch with num_clicks of 'see more' clicks."""
        initial_html = self.driver.page_source
        initial_soup = BeautifulSoup(initial_html, 'html.parser')
        initial_movies = initial_soup.select('div.sc-59c7dc1-2')  # Saving first element

        # Extract data for the initial set of movies (phim ban đầu)
        self.extract_movie_data(initial_movies)

        with tqdm(total=num_clicks, desc='Loading movies') as pbar:
            for _ in range(num_clicks):
                soup = self.click_see_more_button()
                pbar.update(1)

        wait_time = self._calculate_wait_time(num_clicks)
        time.sleep(wait_time)

        # After pressing the 'see more' button
        final_html = self.driver.page_source
        final_soup = BeautifulSoup(final_html, 'html.parser')
        final_movies = final_soup.select('div.sc-59c7dc1-2')

        # After each batch, extract movie data (just extract new data)
        new_movies = final_movies[len(initial_movies):]
        self.extract_movie_data(new_movies)

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

    def save_partial_data(self, batch_num):
        """Save temporary data after each batch."""
        temp_file_name = f"movies_data_batch_{batch_num}.json"
        with open(temp_file_name, 'w', encoding='utf-8') as file:
            json.dump(self.movie_data, file, ensure_ascii=False, indent=4)
        print(f"Data for batch {batch_num} saved to {temp_file_name}")

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

    def fetch_reviews(self):
        for movie in self.movie_data:  # Iterate through the list of movies
            movie_id = movie.get('Movie ID')  # get movie id from dict
            title = movie.get('Title')  #

            if movie_id and title:  # check if they are available
                for rating_filter in range(1, 11):  # having 10 rating stars 
                    review_url = f"https://www.imdb.com/title/{movie_id}/reviews?sort=submissionDate&dir=desc&ratingFilter={rating_filter}"
                    # print(f"Fetching reviews for {title} ({movie_id}) at {review_url} with rating filter {rating_filter}")
                    self.driver.get(review_url)

                    self._load_reviews()  # Load more reviews by clicking the button

                    wait_time = self._calculate_wait_time(10, self.clicks)  # adjust the time for sleeping
                    time.sleep(wait_time)

                    html = self.driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')

                    # extract the reviews for the current movie
                    self._extract_reviews(soup, movie_id, title)
            else:
                print(f"Movie data missing for {movie}. Skipping this movie.")

        self.close_driver()
        return self.movie_reviews


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
        with tqdm(desc='Loading More Reviews', leave=False) as pbar:
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
        with open('movies_reviews.json', 'w', encoding='utf-8') as f:
            json.dump(self.movie_reviews, f, ensure_ascii=False, indent=4)
        print("Reviews saved to movies_reviews.json")

