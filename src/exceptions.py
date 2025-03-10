class ScraperException(Exception):
    """
    Base exception class for all scraper-related errors

    Attributes:
        error_code (str): Unique error code identifier
        message (str): Human-readable error description
        details (dict): Additional error context (optional)
    """

    def __init__(self, error_code: str, message: str, details: dict = None):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> dict:
        """
        Convert exception to dictionary format

        Returns:
            dict: Dictionary containing error details
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ScraperConfigException(ScraperException):
    """Exception raised for configuration errors"""


class ScraperNetworkException(ScraperException):
    """Exception raised for network-related errors"""


class ScraperParseException(ScraperException):
    """Exception raised for parsing errors"""
