from prefect import task, flow
from movie_crawling.crawl_reviews import MovieReviewScraper
from movie_crawling.fetch_data import fetch_and_save_movie_data
from movie_crawling.tmdb_api import TMDBApi
import pymongo
import os
from datetime import datetime, timedelta

# Task to fetch and load movies in the last 24 hours
@task(retries=2)
def extract_and_load_recent_movies(batch_size=10):
    release_date_from = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    release_date_to = datetime.now().strftime('%Y-%m-%d')
    fetch_and_save_movie_data(release_date_from, release_date_to, batch_size)

# Task to check for top popular movies
@task
def check_top_popular_movies(db):
    collection_name = 'top_popular_movies'
    if collection_name not in db.list_collection_names():
        return None  # Collection does not exist
    return list(db[collection_name].find().limit(10))

# Task to fetch and update reviews for popular movies
@task
def update_movie_reviews(db, popular_movies):
    tmdb_api_key = os.getenv('TMDB_API_KEY')
    tmdb_api = TMDBApi(api_key=tmdb_api_key)

    for movie in popular_movies:
        imdb_id = movie.get('imdb_id')
        last_date_review = movie.get('last_date_review')
        total_reviews = movie.get('total_reviews')

        # Fetch new total reviews from the review page
        new_total_reviews = MovieReviewScraper(movie_id=imdb_id).fetch_reviews()['Total Reviews']
        
        if new_total_reviews > total_reviews:
            # Load new reviews
            new_reviews = MovieReviewScraper(movie_id=imdb_id).fetch_reviews()
            new_reviews_list = [
                review for review in new_reviews['Reviews']
                if review['Date'] > last_date_review
            ]

            # Save new reviews to MongoDB
            if new_reviews_list:
                db['movie_reviews'].insert_many(new_reviews_list)
                print(f"Added {len(new_reviews_list)} new reviews for {imdb_id}.")

            # Update total reviews and last review date in top_popular_movies
            movie['total_reviews'] = new_total_reviews
            movie['last_date_review'] = new_reviews_list[0]['Date'] if new_reviews_list else last_date_review
            db['top_popular_movies'].update_one(
                {'imdb_id': imdb_id},
                {'$set': {'total_reviews': movie['total_reviews'], 'last_date_review': movie['last_date_review']}}
            )

@flow(name="Movie-ETL-History", log_prints=True)
def movie_etl_flow():
    # Database configuration
    mongo_uri = os.getenv('MONGO_URI')
    client = pymongo.MongoClient(mongo_uri)
    db_name = os.getenv('MONGODB_DATABASE', 'default_db_name').replace(' ', '_')
    db = client[db_name]

    # Step 1: Fetch recent movies
    extract_and_load_recent_movies()

    # Step 2: Check top popular movies
    popular_movies = check_top_popular_movies(db)
    
    if popular_movies:
        # Step 3: Update reviews for popular movies
        update_movie_reviews(db, popular_movies)

# Execute the flow
if __name__ == "__main__":
    movie_etl_flow()