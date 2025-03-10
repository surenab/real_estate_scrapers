from typing import Dict


class ScraperConfig:
    """
    Configuration class for scrapers
    """

    def __init__(self, base_url: str, selectors: Dict[str, str]):
        self.base_url = base_url
        self.selectors = selectors

    def get_selector(self, key: str) -> str:
        return self.selectors.get(key, "")
