import sys
import os
import logging
from typing import Dict, List
from requests import Response

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


from src.scrapers.base_scraper import BaseScraper
from src.scrapers.url_fetcher import UrlFetcher, RequestIntervalManager, ProxyManager
from src.models.db_service import DBConnect, SQLService

# Set up logging
logger = logging.getLogger(__name__)


class DaftScraper(BaseScraper):
    """
    Concrete implementation of the BaseScraper for Daft.ie
    """

    def __init__(self):
        super().__init__()
        logger.info("Initializing DaftScraper")
        self.headers = {
            "accept": "application/json",
            "accept-language": "en-GB,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,hy-AM;q=0.6,hy;q=0.5,en-US;q=0.4",
            "brand": "daft",
            "cache-control": "no-cache, no-store",
            "content-type": "application/json",
            "dnt": "1",
            "expires": "0",
            "origin": "https://www.daft.ie",
            "platform": "web",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://www.daft.ie/",
            "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        self.cookies = {}
        self.url = "https://gateway.daft.ie/api/v2/ads/listings?&mediaSizes=size720x480&mediaSizes=size72x52"
        self.url_fetcher = UrlFetcher(
            headers=self.headers,
            cookies=self.cookies,
            proxy_manager=ProxyManager(None),
            interval_manager=RequestIntervalManager(7.0, 10.0),
        )
        self.fetch_method = "POST"
        logger.debug("DaftScraper initialized with URL: %s", self.url)

    def get_url_payload(self, page: int, category: str) -> Dict:
        """
        Get the URL payload for the given page and category
        Args:
            page (int): The page number
            category (str): The category of the page
        Returns:
            Dict: URL and payload for the given page and category
        """
        logger.info("Generating payload for page %s, category: %s", page, category)
        if "sold" not in category:
            json_data = {
                "section": category,
                "filters": [
                    {
                        "name": "adState",
                        "values": [
                            "published",
                        ],
                    },
                ],
                "andFilters": [],
                "ranges": [],
                "paging": {
                    "from": f"{20*page}",
                    "pageSize": "20",
                },
                "geoFilter": {
                    "storedShapeIds": [],
                },
                "terms": "",
                "sort": "publishDateDesc",
            }

        else:
            json_data = {
                "section": "residential-sold",
                "filters": [],
                "andFilters": [],
                "ranges": [],
                "paging": {
                    "from": f"{20*page}",
                    "pageSize": "20",
                },
                "geoFilter": {
                    "storedShapeIds": [],
                },
                "terms": "",
                "sort": "soldDateDesc",
            }
        logger.debug("Generated payload: %s", json_data)
        return {"url": self.url, "payload": json_data, "fetch_method": self.fetch_method}

    def parse(self, response: Response, ignore_ids: list = None) -> List[Dict]:
        logger.info("Parsing response")
        if ignore_ids is None:
            ignore_ids = []
        json_data = response.json()
        logger.info("Found %d listings", len(json_data.get("listings", [])))
        filtered_listings = []
        for item in json_data.get("listings", []):
            current_id = item.get("listing", dict()).get("seoFriendlyPath")
            if current_id in ignore_ids:
                continue

            filtered_listings.append(item)
            ignore_ids.append(current_id)

        logger.info("Filtered %d listings, ignore ids amount is: %d", len(filtered_listings), len(ignore_ids))
        return filtered_listings


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    db_connect = DBConnect()
    sql_service = SQLService(db_connect)
    ignore_ids = sql_service.get_real_estate_urls()
    logger.info("Starting DaftScraper")
    daft_scraper = DaftScraper()
    import json

    categories = {
        # "sharing": "sharing",
        # "residential-to-rent": "residential-to-rent",
        # "residential-for-sale": "residential-for-sale",
        "residential-sold": "residential-sold",
        # "new-homes": "new-homes",
        # "holiday-homes": "holiday-homes",
        # "parking-to-rent": "parking-to-rent",
        # "commercial-to-rent": "commercial-to-rent",
    }

    data = {}
    output_file = "daft_test_data_testing.json"

    for tcategory in categories:
        for i in range(1, 104):
            output_file = f"daft_test_data_sold_{i}.json"
            data[tcategory] = daft_scraper.scrape_pages(i * 300, (i + 1) * 300, tcategory)
            # data[tcategory] = daft_scraper.scrape_all_pages(tcategory, ignore_ids)

            logger.info("Writing data to %s", output_file)
            with open(output_file, "w", encoding="utf8") as json_file:
                json.dump(data, json_file)
