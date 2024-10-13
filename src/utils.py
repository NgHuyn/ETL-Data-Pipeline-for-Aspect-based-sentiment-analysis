import logging
import os

def setup_reviews_logger(movie_id):
    # Initialize logs/reviews_log folder
    os.makedirs('logs/reviews_log', exist_ok=True)
    
    # Initialize logger base in movie_id
    logger = logging.getLogger(movie_id)
    logger.setLevel(logging.INFO)

    # check if logger is already have handler to avoid adding many times
    if not logger.handlers:
        # create file handler for each movie_id
        file_handler = logging.FileHandler(f'logs/reviews_log/{movie_id}.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def setup_movies_scraper_logger():
    # Initialize logs/movies_log folder
    os.makedirs('logs/movies_log', exist_ok=True)

    # Initialize logger for movies scraper
    logger = logging.getLogger('movies_scraper')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler('logs/movies_log/movies_scraper.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger