import logging
import os

def setup_movie_logger(movie_id):
    # Tạo thư mục 'logs' nếu chưa có
    os.makedirs('logs', exist_ok=True)
    
    # Tạo logger riêng với tên dựa trên movie_id
    logger = logging.getLogger(movie_id)
    logger.setLevel(logging.INFO)

    # Kiểm tra nếu logger đã có handler để tránh bị thêm nhiều lần
    if not logger.handlers:
        # Tạo file handler cho từng movie_id
        file_handler = logging.FileHandler(f'logs/{movie_id}.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def setup_movies_scraper_logger():
    # Tạo thư mục 'logs' nếu chưa có
    os.makedirs('logs', exist_ok=True)

    # Tạo logger cho movies scraper
    logger = logging.getLogger('movies_scraper')
    logger.setLevel(logging.INFO)

    # Kiểm tra nếu logger đã có handler để tránh bị thêm nhiều lần
    if not logger.handlers:
        # Tạo file handler cho movies scraper
        file_handler = logging.FileHandler('logs/movies_scraper.log')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger