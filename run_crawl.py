from src.crawl_reviews import MoviesScraper
from src.crawl_reviews import MovieReviewScraper

if __name__ == "__main__":
    # get the movie_id first
    scraper = MoviesScraper(clicks=1, release_date_from='2024-01-01', release_date_to='2024-10-07')
    movie_data = scraper.fetch_movies()
    print(movie_data[:2])

    # get the reviews from each movie
    scraper = MovieReviewScraper(movie_data=movie_data[:2])
    scraper.fetch_reviews()
    

