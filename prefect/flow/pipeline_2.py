from prefect import task, flow
from movie_crawling.crawl_reviews import MovieReviewScraper
from movie_crawling.crawl_movies import MoviesScraper
from movie_crawling.fetch_data import fetch_and_save_movie_data
from movie_crawling.tmdb_api import TMDBApi
import pymongo
import os
from datetime import datetime, timedelta
import logging


logging.basicConfig(level=logging.INFO)

# Task to fetch and load movies in a week
@task(retries=2)
def extract_and_load_recent_movies(batch_size=10):
    release_date_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    release_date_to = datetime.now().strftime('%Y-%m-%d')
    fetch_and_save_movie_data(release_date_from, release_date_to, batch_size)

# Task to check for top popular movies collection
@task
def check_top_popular_movies(db):
    collection_name = 'top_popular_movies'
    if collection_name not in db.list_collection_names():
        return None  # Collection does not exist
    return list(db[collection_name].find().limit(10))

# Task to fetch and update reviews for popular movies
# @task
# def update_movie_reviews(db):
    # tmdb_api_key = os.getenv('TMDB_API_KEY')
    # tmdb_api = TMDBApi(api_key=tmdb_api_key)

    # popular_movies = check_top_popular_movies(db)
    # # case 1: if the collection exists
    # if popular_movies:
    #     # Lưu danh sách imdb_id hiện có trong cơ sở dữ liệu
    #     existing_movies = db['top_popular_movies'].find({}, {'imdb_id': 1})
    #     existing_imdb_ids = {movie['imdb_id'] for movie in existing_movies}

    #     for movie in popular_movies:
    #         # get the info from the collection "top_popular_movies"
    #         imdb_id = movie.get('imdb_id')
    #         last_date_review = movie.get('last_date_review')
    #         initial_reviews = movie.get('total_reviews')

    #         # Fetch new total reviews from the review page
    #         fetch_reviews = MovieReviewScraper(movie_id=imdb_id, total_reviews=initial_reviews, last_date_review=last_date_review)
    #         new_reviews = fetch_reviews.fetch_reviews()
    #         # update the reviews for the db movie_reviews
    #         if new_reviews is not None and len(new_reviews['Reviews']) > 0:
    #             db['movie_reviews'].update_one(
    #                 {'Movie ID': imdb_id},
    #                 {
    #                     '$addToSet': {'Reviews': {'$each': new_reviews['Reviews']}},
    #                 },
    #                     upsert=True
    #                 )
    #             logging.info(f"Added {new_reviews['Reviews']} new reviews for {imdb_id}.")

    #         movie['total_reviews'] = new_reviews.total_reviews
    #         movie['last_date_review'] = new_reviews.last_date_review

    #         # update db top_popular_movies
    #         db['top_popular_movies'].update_one(
    #                 {'imdb_id': imdb_id},
    #                 {'$set': {'total_reviews': movie['total_reviews'], 'last_date_review': movie['last_date_review']},
    #                 '$addToSet': {'reviews': {'$each': new_reviews['Reviews']}}}
    #             )
            
    #         # Xóa các phim không còn trong danh sách popular_movies
    #         popular_imdb_ids = {movie['imdb_id'] for movie in popular_movies}
    #         for existing_id in existing_imdb_ids:
    #             if existing_id not in popular_imdb_ids:
    #                 db['top_popular_movies'].delete_one({'imdb_id': existing_id})
    #                 logging.info(f"Removed movie with imdb_id: {existing_id} from top_popular_movies.")
    # # case 2: the collection doesn't exist
    # else:
    #     # pick top 10 popular movies
    #     release_date_to = datetime.now().strftime('%Y-%m-%d')
    #     popular_movies = MoviesScraper(release_date_from='2024-01-01', release_date_to=release_date_to).fetch_movies(limit=10)

    #     # fetch all reviews for each movie
    #     for movie in popular_movies:
    #         imdb_id = movie['Movie ID']
    #         fetch_reviews = MovieReviewScraper(movie_id=imdb_id)
    #         new_reviews = fetch_reviews.fetch_reviews()

    #         # insert to db top_popular_movies
    #         db['top_popular_movies'].insert_one({
    #             'imdb_id': imdb_id,  # Giá trị ví dụ
    #             'total_reviews': new_reviews.total_reviews,
    #             'last_date_review': new_reviews.last_date_review,
    #             'reviews': new_reviews['Reviews']
    #         })

    #         # Kiểm tra xem có bản ghi trong movie_reviews không
    #         existing_review = db['movie_reviews'].find_one({'Movie ID': imdb_id})

    #         if existing_review:
    #             # Nếu bản ghi đã tồn tại, cập nhật reviews
    #             db['movie_reviews'].update_one(
    #                 {'Movie ID': imdb_id},
    #                 {
    #                     '$addToSet': {'Reviews': {'$each': new_reviews['Reviews']}},
    #                     '$set': {
    #                         'total_reviews': new_reviews.total_reviews,
    #                         'last_date_review': new_reviews.last_date_review
    #                     }
    #                 },
    #                 upsert=True  # Chỉ cần thêm nếu không tồn tại
    #             )
    #             logging.info(f"Updated reviews for {imdb_id}.")
    #         else:
    #             # Nếu bản ghi không tồn tại, tạo mới
    #             db['movie_reviews'].insert_one({
    #                 'Movie ID': imdb_id,
    #                 'Reviews': new_reviews['Reviews'],
    #                 'total_reviews': new_reviews.total_reviews,
    #                 'last_date_review': new_reviews.last_date_review
    #             })
    #             logging.info(f"Inserted new movie review for {imdb_id}.")





        # # Fetch new total reviews from the review page
        # new_total_reviews = MovieReviewScraper(movie_id=imdb_id).fetch_reviews()['Total Reviews']
        
        # if new_total_reviews > total_reviews:
        #     # Load new reviews
        #     new_reviews = MovieReviewScraper(movie_id=imdb_id).fetch_reviews()
        #     new_reviews_list = [
        #         review for review in new_reviews['Reviews']
        #         if review['Date'] > last_date_review
        #     ]

        #     # Save new reviews to MongoDB
        #     if new_reviews_list:
        #         db['movie_reviews'].insert_many(new_reviews_list)
        #         print(f"Added {len(new_reviews_list)} new reviews for {imdb_id}.")

        #     # Update total reviews and last review date in top_popular_movies
        #     movie['total_reviews'] = new_total_reviews
        #     movie['last_date_review'] = new_reviews_list[0]['Date'] if new_reviews_list else last_date_review
        #     db['top_popular_movies'].update_one(
        #         {'imdb_id': imdb_id},
        #         {'$set': {'total_reviews': movie['total_reviews'], 'last_date_review': movie['last_date_review']}}
        #     )
@task
def update_movie_reviews(db):
    tmdb_api_key = os.getenv('TMDB_API_KEY')
    tmdb_api = TMDBApi(api_key=tmdb_api_key)

    popular_movies = check_top_popular_movies(db)
    
    # Case 1: if the collection exists
    if popular_movies:
        logging.info("Updating reviews for existing popular movies.")
        
        existing_movies = db['top_popular_movies'].find({}, {'imdb_id': 1})
        existing_imdb_ids = {movie['imdb_id'] for movie in existing_movies}
        
        for movie in popular_movies:
            imdb_id = movie.get('imdb_id')
            last_date_review = movie.get('last_date_review')
            initial_reviews = movie.get('total_reviews')

            logging.info(f"Fetching new reviews for movie ID: {imdb_id}")
            fetch_reviews = MovieReviewScraper(movie_id=imdb_id, total_reviews=initial_reviews, last_date_review=last_date_review)
            new_reviews = fetch_reviews.fetch_reviews()

            # Update the reviews for the db movie_reviews
            if new_reviews is not None and len(new_reviews['Reviews']) > 0:
                db['movie_reviews'].update_one(
                    {'Movie ID': imdb_id},
                    {
                        '$addToSet': {'Reviews': {'$each': new_reviews['Reviews']}},
                    },
                    upsert=True
                )
                logging.info(f"Added {len(new_reviews['Reviews'])} new reviews for {imdb_id}.")

            movie['total_reviews'] = fetch_reviews.total_reviews
            movie['last_date_review'] = fetch_reviews.last_date_review

            # Update db top_popular_movies
            db['top_popular_movies'].update_one(
                {'imdb_id': imdb_id},
                {
                    '$set': {
                        'total_reviews': movie['total_reviews'],
                        'last_date_review': movie['last_date_review']
                    },
                    '$addToSet': {'reviews': {'$each': new_reviews['Reviews']}}
                }
            )
            logging.info(f"Updated top_popular_movies for {imdb_id}.")

        # Remove movies not in the new popular_movies list
        popular_imdb_ids = {movie['imdb_id'] for movie in popular_movies}
        for existing_id in existing_imdb_ids:
            if existing_id not in popular_imdb_ids:
                db['top_popular_movies'].delete_one({'imdb_id': existing_id})
                logging.info(f"Removed movie with imdb_id: {existing_id} from top_popular_movies.")

    # Case 2: the collection doesn't exist
    else:
        logging.info("No existing popular movies found. Fetching new top 10 popular movies.")
        
        release_date_to = datetime.now().strftime('%Y-%m-%d')
        popular_movies = MoviesScraper(release_date_from='2024-01-01', release_date_to=release_date_to).fetch_movies(limit=10)

        for movie in popular_movies:
            imdb_id = movie['Movie ID']
            logging.info(f"Fetching reviews for new movie ID: {imdb_id}")
            fetch_reviews = MovieReviewScraper(movie_id=imdb_id)
            new_reviews = fetch_reviews.fetch_reviews()
            total_reviews = fetch_reviews.total_reviews
            last_date_review = fetch_reviews.last_date_review

            # Insert to db top_popular_movies
            db['top_popular_movies'].insert_one({
                'imdb_id': imdb_id,
                'total_reviews': total_reviews,
                'last_date_review': last_date_review,
                'reviews': new_reviews['Reviews']
            })
            logging.info(f"Inserted new popular movie with ID: {imdb_id}.")

            # Check if there is a record in movie_reviews
            existing_review = db['movie_reviews'].find_one({'Movie ID': imdb_id})

            if existing_review:
                logging.info(f"Updating existing reviews for movie ID: {imdb_id}.")
                # If the record exists, update reviews
                db['movie_reviews'].update_one(
                    {'Movie ID': imdb_id},
                    {
                        '$addToSet': {'Reviews': {'$each': new_reviews['Reviews']}},
                    },
                    upsert=True
                )
                logging.info(f"Updated reviews for {imdb_id}.")
            else:
                logging.info(f"Inserting new reviews for movie ID: {imdb_id}.")
                # If the record does not exist, create a new one
                db['movie_reviews'].insert_one({
                    'Movie ID': imdb_id,
                    'Reviews': new_reviews['Reviews'],
                })
                logging.info(f"Inserted new movie review for {imdb_id}.")

@flow(name="Movie-ETL-History", log_prints=True)
def movie_etl_flow():
    # Database configuration
    mongo_uri = os.getenv('MONGO_URI')
    client = pymongo.MongoClient(mongo_uri)
    db_name = os.getenv('MONGODB_DATABASE', 'default_db_name').replace(' ', '_')
    db = client[db_name]

    # Step 1: Fetch recent movies
    # extract_and_load_recent_movies()

    # step 2: update new review of top popular movies
    update_movie_reviews(db)

# Execute the flow
if __name__ == "__main__":
    movie_etl_flow()