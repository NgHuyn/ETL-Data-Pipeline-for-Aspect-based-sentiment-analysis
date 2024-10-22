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

def batch_list(data, batch_size):
    """Chia dữ liệu thành các batch."""
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

def fetch_and_save_movie_data(release_date_from, release_date_to, batch_size=10):
    """Fetch and save movie data in batches."""
    configure()
    
    # Get API key and Mongo URI
    tmdb_api_key = os.getenv('TMDB_API_KEY')
    mongo_uri = os.getenv('MONGO_URI')

    # Initialize MongoDB client and scrapers
    client = pymongo.MongoClient(mongo_uri)
    db_name = os.getenv('MONGODB_DATABASE', 'default_db_name').replace(' ', '_')  
    if len(db_name) > 38:
        raise ValueError("Database name exceeds maximum length of 38 characters.")
    db = client[db_name]
    tmdb_api = TMDBApi(api_key=tmdb_api_key)

    scraper = MoviesScraper(release_date_from=release_date_from, release_date_to=release_date_to)

    # Check if movie_genres collection already exists
    if 'movie_genres' not in db.list_collection_names():
        save_to_mongo(tmdb_api.get_movie_genres(), 'movie_genres', db)
    else:
        logging.info("Collection 'movie_genres' already exists. Skipping genre retrieval.")

    # Fetch the full list of movies
    movies = scraper.fetch_movies()
    
    # Chia nhỏ danh sách phim thành các batch và xử lý từng batch một
    for movie_batch in batch_list(movies, batch_size):
        logging.info(f"Processing batch of {len(movie_batch)} movies.")
        
        for movie in movie_batch:
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
            save_to_mongo(MovieReviewScraper(movie_id=imdb_id).fetch_reviews(), 'movie_reviews', db)

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
        
        logging.info(f"Finished processing batch of {len(movie_batch)} movies.")

# fetch_and_save_movie_data(release_date_from='2024-02-02', release_date_to='2024-02-02')




