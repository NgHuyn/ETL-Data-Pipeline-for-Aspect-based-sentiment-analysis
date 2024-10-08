import os
import json
from data.movies_scraper import MoviesScraper
from data.reviews_scraper import MovieReviewScraper

if __name__ == "__main__":
    # scraper = MoviesScraper(clicks=3)

    # scraper.fetch_movies()
    # scraper.save_to_json()
    # print("Movies fetched and saved to movies.json")

    #test reviews scraper
    data = [
        {
            "Movie ID": "tt17526714",
            "Title": "The Substance"
        }
    ]

    # Save the data to a JSON file
    with open('test_movie.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)

    path = os.path.join(os.path.dirname(__file__), 'data\\test_movie.json')
    scraper = MovieReviewScraper(path)
    
    scraper.fetch_reviews()
    scraper.save_to_json()
    print("Movies fetched and saved to movies_reviews.json")
    

