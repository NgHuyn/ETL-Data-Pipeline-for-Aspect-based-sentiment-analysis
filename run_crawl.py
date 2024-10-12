from src.crawl_reviews import MoviesScraper
from src.crawl_reviews import MovieReviewScraper
import concurrent.futures
import json
# if __name__ == "__main__":
#     # get the movie_id first
#     scraper = MoviesScraper(clicks=0, release_date_from='2024-01-01', release_date_to='2024-10-07')
#     movie_data = scraper.fetch_movies()
#     print(movie_data[1:2])

#     # get the reviews from each movie
#     scraper = MovieReviewScraper(movie_data=movie_data[1:2])
#     movie_reviews = scraper.fetch_reviews()

#     with open('movies_reviews.json', 'w', encoding='utf-8') as f:
#         json.dump(movie_reviews, f, ensure_ascii=False, indent=4)
#         print("Reviews saved to movies_reviews.json")

def fetch_movie_reviews(movie):
    scraper = MovieReviewScraper(movie_data=[movie])  # Đảm bảo truyền dữ liệu phim dưới dạng danh sách
    return scraper.fetch_reviews()

if __name__ == "__main__":
    # Get the movie_id first
    scraper = MoviesScraper(clicks=0, release_date_from='2024-01-01', release_date_to='2024-10-07')
    movie_data = scraper.fetch_movies()
    print(movie_data[:10])  # In ra danh sách phim để kiểm tra

    # Get the reviews from each movie using threading
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        movie_reviews = list(executor.map(fetch_movie_reviews, movie_data[:10]))

    # Save all reviews to a JSON file
    with open('movies_reviews.json', 'w', encoding='utf-8') as f:
        json.dump(movie_reviews, f, ensure_ascii=False, indent=4)
        print("Reviews saved to movies_reviews.json")