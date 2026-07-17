import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def browse_website(user_id: str, url: str) -> str:
    """
    Fetches the content of a given URL and returns the clean text.
    user_id is included to maintain a consistent function signature across all tools.
    """
    logger.info(f"Browsing website: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        # Get text and clean it up
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)

        logger.info(f"Successfully scraped {len(clean_text)} characters from {url}.")
        return clean_text

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return f"Error: Could not fetch the website. {e}"
    except Exception as e:
        logger.error(f"An unexpected error occurred while browsing {url}: {e}", exc_info=True)
        return f"Error: An unexpected error occurred while processing the website."

