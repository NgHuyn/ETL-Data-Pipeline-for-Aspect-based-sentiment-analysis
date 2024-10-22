import requests
import logging
import time
from rate_limit_exception import RateLimitException

logging.basicConfig(level=logging.INFO)

class TMDBApi:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.timeout = 10

    def _make_request(self, url):
        """Helper method to send GET requests and handle rate limiting and errors."""
        for attempt in range(3):  # Retry up to 3 times
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logging.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif e.response.status_code in {500, 503}:
                    logging.error(f"Server error {e.response.status_code}. Retrying...")
                    time.sleep(2)
                else:
                    logging.error(f"HTTP error: {e}")
                    raise e
        raise Exception(f"Failed to fetch data after multiple attempts: {url}")

    def get_movie_genres(self):
        """Get the list of available movie genres from TMDB."""
        url = f"{self.base_url}/genre/movie/list?api_key={self.api_key}&language=en-US"
        return self._make_request(url).get('genres', [])

    def find_tmdb_id_by_imdb_id(self, imdb_id):
        """Get TMDB movie ID based on IMDb ID."""
        url = f"{self.base_url}/find/{imdb_id}?api_key={self.api_key}&external_source=imdb_id"
        response = self._make_request(url)
        
        movie_results = response.get('movie_results', [])
        if movie_results:  # Check if list is not empty
            return movie_results[0].get('id', None)
        else:
            return None  # Return None if no movie found

    def get_movie_details(self, tmdb_id):
        """Get the movie details."""
        url = f"{self.base_url}/movie/{tmdb_id}?api_key={self.api_key}&language=en-US"
        return self._make_request(url)

    def get_cast_and_crew(self, tmdb_id):
        """Get the cast and crew of a movie."""
        url = f"{self.base_url}/movie/{tmdb_id}/credits?api_key={self.api_key}"
        return self._make_request(url)

    def get_person_details(self, person_id):
        """Get the details of a person."""
        url = f"{self.base_url}/person/{person_id}?api_key={self.api_key}&language=en-US"
        return self._make_request(url)

    def get_actor_details(self, cast):
        """Get the details of all actors in the cast."""
        return [self.get_person_details(member['id']) for member in cast if member['known_for_department'] == 'Acting']

    def get_director_details(self, crew):
        """Get the details of the director(s) in the crew."""
        return [self.get_person_details(member['id']) for member in crew if member['job'] == 'Director']
    
    def get_top_popular_movies(self, top_n=10):
        """Get the top N popular movies, sorted by popularity."""
        url = f"{self.base_url}/movie/popular?api_key={self.api_key}&language=en-US&page=1"
        
        try:
            data = self._make_request(url)
            movies = data.get('results', [])
            
            # Sort by 'popularity'
            sorted_movies = sorted(movies, key=lambda x: x['popularity'], reverse=True)
            
            # Retrieve top 10 movies
            top_movies = sorted_movies[:top_n]
            return top_movies
        
        except Exception as e:
            logging.error(f"Failed to fetch popular movies: {e}")
            return []
