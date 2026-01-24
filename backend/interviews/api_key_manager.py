from django.conf import settings  # type: ignore

class APIKeyManager:
    """
    API key manager with fallback system: .env -> settings -> universal paid key
    """
    def __init__(self):
        # Universal paid key as final fallback
        universal_key = 'AIzaSyB8tF9bjsK1hNpzIG74uBOSIQKs77VGx9g'
        # Use settings (which has .env fallback) or universal key
        self.key = settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY or universal_key
        if not self.key:
            # Final safety fallback
            self.key = universal_key

    def get_key(self):
        """Return the universal API key"""
        return self.key

    def rotate_key(self):
        """No-op: Single key, no rotation needed"""
        return self.key


# Initialize a single manager instance for your app
api_key_manager = APIKeyManager()
