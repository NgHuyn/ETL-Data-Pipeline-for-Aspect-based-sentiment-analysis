import os
import json
from data.movies_scraper import MoviesScraper
from data.reviews_scraper import MovieReviewScraper

if __name__ == "__main__":
    # get the movie_id first
    scraper = MoviesScraper(clicks=10, batch_size=4)
    movie_data = scraper.fetch_movies()

    # get the reviews from each movie
    scraper = MovieReviewScraper(movie_data=movie_data[0:3]) # adjust the elements from the movie data 

    scraper.fetch_reviews()
    scraper.save_to_json()
    print("Movies fetched and saved to movies_reviews.json")
    

