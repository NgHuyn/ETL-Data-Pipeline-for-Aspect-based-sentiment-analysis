from movie_crawling.crawl_movies import MoviesScraper
from movie_crawling.crawl_reviews import MovieReviewScraper
import concurrent.futures
import json
import os

def fetch_movie_reviews(movie_id, movie_title):
    scraper = MovieReviewScraper(movie_id=movie_id, movie_title=movie_title)  # Đảm bảo truyền dữ liệu phim
    movie_reviews  = scraper.fetch_reviews()
    
    return movie_reviews 

def load_existing_data(file_path):
    """Đọc dữ liệu JSON nếu đã tồn tại, nếu không trả về danh sách rỗng."""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []  # Nếu lỗi định dạng, trả về danh sách rỗng
    return []

def save_data_to_json(data, file_path):
    """Ghi dữ liệu vào file JSON."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # Get the movie_id first
    scraper = MoviesScraper(clicks=0, release_date_from='2024-01-01', release_date_to='2024-10-07')
    movie_data = scraper.fetch_movies()
    # print(movie_data[10:20])  # In ra danh sách phim để kiểm tra

    file_path = 'movies_reviews_test.json'

    # 1. Đọc dữ liệu đã tồn tại trong file JSON (nếu có)
    movies_reviews = load_existing_data(file_path)

    # Lấy đánh giá cho từng phim bằng threading
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        new_movies_reviews = list(executor.map(lambda movie: fetch_movie_reviews(movie.get('Movie ID'), movie.get('Title')), movie_data[10:20]))

    # 3. Lọc bỏ các phần tử trống hoặc None trong new_reviews
    new_movies_reviews = [review for review in new_movies_reviews if review]

    # 4. Nối các review mới vào danh sách hiện tại
    movies_reviews.extend(new_movies_reviews)  # Dùng extend thay vì append để nối danh sách

    # # 5. Lưu lại dữ liệu đã được nối vào file JSON
    save_data_to_json(movies_reviews, file_path)




    # # Save all reviews to a JSON file
    # with open('movies_reviews.json', 'w', encoding='utf-8') as f:
    #     json.dump(movies_reviews, f, ensure_ascii=False, indent=4)
    #     print("Reviews saved to movies_reviews_test.json")