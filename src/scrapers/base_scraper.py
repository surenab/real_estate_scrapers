import logging
from abc import ABC, abstractmethod
from typing import Dict, List
from time import sleep
from requests import Response
from requests.exceptions import RequestException

from src.exceptions import ScraperNetworkException

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class BaseScraper(ABC):
    """
    Abstract base class for scrapers
    """

    @abstractmethod
    def get_url_payload(self, page: int, category: str) -> Dict:
        """
        Get the URL payload for the given page and category
        Args:
            page (int): The page number
            category (str): The category of the page
        Returns:
            Dict: URL and payload for the given page and category
        """

    @abstractmethod
    def parse(self, response: Response, ignore_ids: list = None) -> List[Dict]:
        """
        Abstract method to parse the scraped content
        Args:
            response (Response): The scraped response object
        Returns:
            List[Dict]: Parsed data in a structured format
        """

    def scrape_page(self, page: int, category: str, ignore_ids: list = None) -> List[Dict]:
        """
        Abstract method to be implemented by specific scrapers
        Args:
            page (int): The page number to scrape
            category (str): The category of the page
        Returns:
            List[Dict]: Scraped data in a structured format
        """
        current_page_inputs = self.get_url_payload(page, category)
        while True:
            try:
                response = self.url_fetcher.fetch(
                    current_page_inputs.get("url"),
                    payload=current_page_inputs.get("payload"),
                    fetch_method=current_page_inputs.get("fetch_method"),
                )
                break
            except (ConnectionError, TimeoutError, RequestException, ScraperNetworkException) as e:
                print(f"Error occurred: {e}. Retrying...")
                sleep(120)

        return self.parse(response, ignore_ids)

    def scrape_pages(self, start_page: int, end_page: int, category: str, ignore_ids: list = None) -> List[Dict]:
        """
        Scrape multiple pages
        Args:
            start_page (int): The starting page number
            end_page (int): The ending page number
            category (str): The category of the pages
        Returns:
            List[Dict]: Scraped data for all pages
        """
        scraped_data = []
        for page in range(start_page, end_page + 1):
            page_data = self.scrape_page(page, category, ignore_ids)
            if not page_data:
                break
            scraped_data.extend(page_data)
            logger.info("Up to %d page scraped %d items", page, len(scraped_data))
        return scraped_data

    def scrape_all_pages(self, category: str, ignore_ids: list = None) -> List[Dict]:
        """
        Scrape all available pages
        Args:
            category (str): The category of the pages
        Returns:
            List[Dict]: Scraped data for all pages
        """
        scraped_data = []
        page = 1
        while True:
            page_data = self.scrape_page(page, category, ignore_ids)
            if not page_data:
                break
            scraped_data.extend(page_data)
            logger.info("Up to %d page scraped %d items", page, len(scraped_data))
            page += 1
        return scraped_data
