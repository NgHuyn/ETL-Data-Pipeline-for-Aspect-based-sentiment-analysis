from src.crawl_movies import MoviesScraper
from src.crawl_reviews import MovieReviewScraper
import concurrent.futures
import json

def fetch_movie_reviews(movie_id, movie_title):
    scraper = MovieReviewScraper(movie_id=movie_id, movie_title=movie_title)  # Đảm bảo truyền dữ liệu phim
    movie_reviews  = scraper.fetch_reviews()
    
    return movie_reviews 

if __name__ == "__main__":
    # Get the movie_id first
    scraper = MoviesScraper(clicks=0, release_date_from='2024-01-01', release_date_to='2024-10-07')
    movie_data = scraper.fetch_movies()
    print(movie_data[3:6])  # In ra danh sách phim để kiểm tra

    # Lấy đánh giá cho từng phim bằng threading
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        movies_reviews = list(executor.map(lambda movie: fetch_movie_reviews(movie.get('Movie ID'), movie.get('Title')), movie_data[3:6]))

    # Save all reviews to a JSON file
    with open('movies_reviews.json', 'w', encoding='utf-8') as f:
        json.dump(movies_reviews, f, ensure_ascii=False, indent=4)
        print("Reviews saved to movies_reviews_test.json")