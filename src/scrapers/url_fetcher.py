import sys
import os
from typing import Optional, Dict
import random
import time
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.exceptions import ScraperNetworkException


class ProxyManager:
    """
    Handles proxy management and selection
    """

    def __init__(self, proxies: Optional[Dict] = None):
        self.proxies = proxies or {}

    def get_random_proxy(self) -> Optional[str]:
        """
        Get random proxy from available proxies
        Returns:
            Optional[str]: Random proxy URL
        """
        if not self.proxies:
            return None
        return random.choice(list(self.proxies.values()))


class RequestIntervalManager:
    """
    Handles request interval timing
    """

    def __init__(self, min_interval: float = 1.0, max_interval: float = 4.0):
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.last_request_time = 0

    def respect_interval(self):
        """
        Respect minimum time interval between requests
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(random.uniform(self.min_interval, self.max_interval) - elapsed)
        self.last_request_time = time.time()


class UrlFetcher:
    """
    Class to handle fetching HTML or JSON data from URLs
    """

    def __init__(
        self,
        headers: Optional[Dict] = None,
        cookies: Optional[Dict] = None,
        proxy_manager: Optional[ProxyManager] = None,
        interval_manager: Optional[RequestIntervalManager] = None,
    ):
        self.session = requests.Session()
        self.session.cookies.update(cookies or {})
        self.headers = headers or {}
        self.proxy_manager = proxy_manager or ProxyManager()
        self.interval_manager = interval_manager or RequestIntervalManager()

    def fetch(self, url: str, fetch_method: str = "GET", payload: Optional[Dict] = None) -> requests.Response:
        """
        Fetch data from URL with optional headers, cookies, and proxies
        Args:
            url (str): URL to fetch data from
            return_type (str): Type of data to return ('html' or 'json')
        Returns:
            Union[str, Dict]: Fetched data in specified format
        """
        self.interval_manager.respect_interval()
        response = self.session.request(
            method=fetch_method,
            url=url,
            headers=self.headers,
            proxies=self.proxy_manager.get_random_proxy(),
            timeout=10,
            json=payload if fetch_method in ["POST", "PUT", "PATCH"] else None,
        )

        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ScraperNetworkException(
                error_code="NETWORK_ERROR",
                message=f"Network error occurred while fetching {url}",
                details={"exception": str(e)},
            ) from e

        return response
