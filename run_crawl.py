import os
import json
from src.movies_scraper import MoviesScraper
from src.reviews_scraper import MovieReviewScraper

if __name__ == "__main__":
    # get the movie_id first
    scraper = MoviesScraper(clicks=10, release_date_from='2024-01-01', release_date_to='2024-10-07')
    movie_data = scraper.fetch_movies()

    # get the reviews from each movie
    scraper = MovieReviewScraper(movie_data=movie_data[:1])
    scraper.fetch_reviews()
    

