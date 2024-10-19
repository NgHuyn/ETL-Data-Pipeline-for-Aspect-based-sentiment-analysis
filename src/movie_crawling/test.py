from crawl_movies import MoviesScraper
from crawl_reviews import MovieReviewScraper
from tmdb_api import TMDBApi  
from dotenv import load_dotenv
import os
import pymongo
import logging

logging.basicConfig(level=logging.INFO)

def configure():
    """Load environment variables."""
    load_dotenv()

def save_to_mongo(data, collection_name, db):
    """Save data to MongoDB collection."""
    if not data:
        logging.warning(f"No data to save for {collection_name}.")
        return
    collection = db[collection_name]
    try:
        if isinstance(data, list):
            collection.insert_many(data, ordered=False)
        else:
            collection.insert_one(data)
        logging.info(f"Inserted data into {collection_name}.")
    except Exception as e:
        logging.error(f"Error saving to {collection_name}: {e}")

def fetch_and_save_movie_data():
    """Main function to fetch and save movie data."""
    configure()
    
    # Get API key and Mongo URI
    tmdb_api_key = os.getenv('TMDB_API_KEY')
    mongo_uri = os.getenv('MONGO_URI')

    # Initialize MongoDB client and scrapers
    client = pymongo.MongoClient(mongo_uri)
    db = client["movie_database"]
    tmdb_api = TMDBApi(api_key=tmdb_api_key)
    scraper = MoviesScraper(release_date_from='2024-01-04', release_date_to='2024-01-04')

    save_to_mongo(tmdb_api.get_movie_genres(), 'movie_genres', db)

    for movie in scraper.fetch_movies():
        imdb_id = movie.get('Movie ID')
        if not imdb_id:
            logging.warning("Movie ID not found.")
            continue

        tmdb_id = tmdb_api.find_tmdb_id_by_imdb_id(imdb_id)
        if not tmdb_id:
            logging.warning(f"TMDB ID not found for IMDB ID {imdb_id}. Skipping.")
            continue

        # Fetch and save movie details, reviews, cast and crew
        save_to_mongo(tmdb_api.get_movie_details(tmdb_id), 'movie_details', db)
        save_to_mongo(MovieReviewScraper(movie_id=imdb_id, movie_title=movie.get('Title')).fetch_reviews(), 'movie_reviews', db)

        # Fetch and save cast (actors) and crew (directors)
        cast_and_crew = tmdb_api.get_cast_and_crew(tmdb_id)
        if cast_and_crew:
            for actor in cast_and_crew.get('cast', []):
                actor['movie_tmdb_id'] = tmdb_id
                save_to_mongo(actor, 'movie_actor_credits', db)
                save_to_mongo(tmdb_api.get_person_details(actor['id']), 'actor_details', db)

            for crew_member in cast_and_crew.get('crew', []):
                if crew_member.get('job') == 'Director':
                    crew_member['movie_tmdb_id'] = tmdb_id
                    save_to_mongo(crew_member, 'movie_director_credits', db)
                    save_to_mongo(tmdb_api.get_person_details(crew_member['id']), 'director_details', db)

fetch_and_save_movie_data()
