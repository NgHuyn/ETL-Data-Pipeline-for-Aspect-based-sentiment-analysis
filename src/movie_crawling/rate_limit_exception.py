class RateLimitException(Exception):
    """Custom exception for exceeding rate limit when calling API."""
    
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
