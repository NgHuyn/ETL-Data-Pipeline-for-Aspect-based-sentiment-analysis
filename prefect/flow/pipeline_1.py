from prefect import task, flow
from movie_crawling.fetch_data import fetch_and_save_movie_data

# Task to fetch and load movies in batches
@task(retries=2)
def extract_and_load_movies(release_date_from, release_date_to, batch_size=10):
    fetch_and_save_movie_data(release_date_from, release_date_to, batch_size)

@flow(name="Movie-ETL-History", log_prints=True)
def movie_etl_flow():
    release_date_from = '2024-01-01'
    release_date_to = '2024-01-01'
    extract_and_load_movies(release_date_from, release_date_to, batch_size=10)

# Execute the flow
if __name__ == "__main__":
    movie_etl_flow()
