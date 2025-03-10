import re
import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum
from time import sleep
from geopy.geocoders import Photon, Nominatim
from geopy.exc import GeocoderUnavailable
import concurrent.futures
from random import randint

# Simple caching mechanism to reduce API calls
CACHE_FILE = "address_cache.json"


def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


CACHE = load_cache()


def get_cache_key(query):
    return hashlib.md5(query.encode()).hexdigest()


class RelaEstateAdvertEnum(Enum):
    RENT = "Rent"
    SALE = "Sale"
    SHARE = "Share"
    SOLD = "Sold"


@dataclass
class Offers:
    "Data class for an Offers"

    awaiting_bidders: int = 0
    booking_deposit: float = 0.0
    highest_offer: Optional[float] = None
    highest_offer_currency: Optional[str] = None
    make_offer_private: bool = False
    minimum_increment: float = 0.0
    minimum_offer_amount: float = 0.0
    offers_count: int = 0
    status: str = ""

    @staticmethod
    def parse_price(price_str: str) -> tuple[Optional[float], Optional[str]]:
        """
        Extracts the numeric value and currency symbol from a price string.
        """
        match = re.search(r"([€£$])?([\d,]+\.?\d*)", price_str)
        if match:
            currency = match.group(1) or None
            price = float(match.group(2).replace(",", ""))
            return price, currency
        return None, None

    @classmethod
    def from_dict(cls, data: dict):
        """
        Creates an Offer instance from a dictionary.
        """
        highest_offer, highest_offer_currency = cls.parse_price(data.get("highestOffer", ""))

        return cls(
            awaiting_bidders=data.get("awaitingBidders", 0),
            booking_deposit=data.get("bookingDeposit", 0.0),
            highest_offer=highest_offer,
            highest_offer_currency=highest_offer_currency,
            make_offer_private=data.get("makeOfferPrivate", False),
            minimum_increment=data.get("minimumIncrement", 0.0),
            minimum_offer_amount=data.get("minimumOfferAmount", 0.0),
            offers_count=data.get("offersCount", 0),
            status=data.get("status", ""),
        )


@dataclass
class Ber:
    rating: str | None = None
    code: str | None = None
    epi: str | None = None


@dataclass
class Category:
    name: str
    parent: Optional["Category"] = field(default=None, repr=False)

    def __str__(self):
        return f"{self.name} (Parent: {self.parent.name if self.parent else None})"


@dataclass
class Address:
    "Data class for Address"

    address1: Optional[str] = None
    address2: Optional[str] = None
    address3: Optional[str] = None
    address4: Optional[str] = None
    city: str = ""
    postal_code: str = ""
    county: str = ""
    country: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    local_authority: Optional[str] = None

    def __post_init__(self):
        self.fill_missing_data()

    def fill_missing_data(self):
        """Fill missing details by fetching address data"""
        geolocators = [Photon(user_agent="estylith"), Nominatim(user_agent="estylith")]

        # Use a thread pool to fetch data faster
        with concurrent.futures.ThreadPoolExecutor() as executor:
            if self.latitude and self.longitude and not self.address1:
                # Reverse geocoding
                future = executor.submit(self.reverse_geocode, geolocators)
            elif self.address1 and not self.latitude:
                # Forward geocoding
                future = executor.submit(self.forward_geocode, geolocators)
            else:
                return

            result = future.result()
            if result:
                self._update_from_location(result)

    def reverse_geocode(self, geolocators):
        """Reverse geocode with caching and retries"""
        cache_key = get_cache_key(f"{self.latitude},{self.longitude}")
        if cache_key in CACHE:
            return CACHE[cache_key]

        for geolocator in geolocators:
            try:
                location = geolocator.reverse((self.latitude, self.longitude), language="en")
                if location and location.raw.get("address"):
                    CACHE[cache_key] = location.raw["address"]
                    save_cache(CACHE)
                    return location.raw["address"]
            except GeocoderUnavailable:
                sleep(randint(3, 7))

    def forward_geocode(self, geolocators):
        """Forward geocode with caching and retries"""
        cache_key = get_cache_key(self.address1)
        if cache_key in CACHE:
            return CACHE[cache_key]

        for geolocator in geolocators:
            try:
                location = geolocator.geocode(self.address1 + " Ireland")
                if location:
                    self.latitude, self.longitude = location.latitude, location.longitude
                    if location.raw.get("address"):
                        CACHE[cache_key] = location.raw["address"]
                        save_cache(CACHE)
                        return location.raw["address"]
            except GeocoderUnavailable:
                sleep(randint(3, 7))

    def _update_from_location(self, address_data):
        """Update fields from geocoder response"""
        self.address1 = address_data.get("road") or self.address1
        self.city = address_data.get("city") or address_data.get("town") or address_data.get("village") or self.city
        self.postal_code = address_data.get("postcode") or self.postal_code
        self.county = address_data.get("county") or self.county
        self.country = address_data.get("country") or self.country
        self.local_authority = address_data.get("state") or self.local_authority


@dataclass
class Seller:
    "Data class for Seller info"

    seller_id: int
    name: str
    phone: Optional[str] = None
    branch: Optional[str] = None
    address: Optional[Address] = None
    profile_image: Optional[str] = None
    profile_rounded_image: Optional[str] = None
    standard_logo: Optional[str] = None
    square_logo: Optional[str] = None
    background_colour: Optional[str] = ""
    seller_type: Optional[str] = ""
    available: bool = True


@dataclass
class RelaEstateImage:
    "Data class for RelaEstateImage"

    url: str
    size_name: str


@dataclass
class PriceHistory:
    "Data class for Price History"

    price: float
    timestamp: datetime
    current: bool = True
    source: Optional[str] = None
    currency: str = "€"
    category: RelaEstateAdvertEnum = RelaEstateAdvertEnum.RENT  # Can only be "Rent" or "Sale"

    @staticmethod
    def parse_price(price_str: str) -> tuple[float, str]:
        """
        Parses a price string like "€39,500" and returns (price, currency).
        """
        match = re.search(r"([€£$])?([\d,]+\.?\d*)", price_str)
        if match:
            currency = match.group(1) or "€"
            price = int(match.group(2).replace(",", ""))
            return price, currency
        raise ValueError(f"Invalid price format: {price_str}")

    @classmethod
    def from_dict(cls, data: dict, category: str) -> "PriceHistory":
        """
        Creates a list of PriceHistory instances from a dictionary.
        """
        if category not in (RelaEstateAdvertEnum.RENT, RelaEstateAdvertEnum.SALE):
            raise ValueError(f"Invalid category: {category}. Must be 'Rent' or 'Sale' or 'Share'.")

        price, currency = cls.parse_price(data["price"])
        timestamp = datetime.strptime(data["date"], "%d/%m/%Y")
        direction = data.get("direction", "").upper()
        price_difference, _ = cls.parse_price(data.get("priceDifference", "€0"))
        if direction == "DECREASE":
            real_price = price + price_difference
        elif direction == "INCREASE":
            real_price = price - price_difference
        else:
            real_price = price  # No change if direction is missing

        current = data.get("current", False)
        return cls(price=real_price, timestamp=timestamp, currency=currency, category=category, current=current)


@dataclass
class RealEstate:
    "Data class for generic base of Real Estate"

    title: str = ""
    seo_title: str = ""
    publish_date: datetime = field(default_factory=datetime.now)
    property_type: str = ""
    price_history: List[PriceHistory] = field(default_factory=list)
    seller: Seller = field(default=None)
    real_estate_images: List[RelaEstateImage] = field(default_factory=list)
    category: Category = field(default=None)
    url: Optional[str] = None
    date_of_construction: datetime | None = None
    about: str = ""
    description: str = ""
    sold: bool = field(default=False)
    advert_type: RelaEstateAdvertEnum = RelaEstateAdvertEnum.SALE
    ber: Optional[Ber] = None
    # Location & Address
    address: Address = field(default=None)
    brochure: Optional[str] = None
    offers: Offers = field(default=None)

    # Property Details
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    size_sq_m: Optional[float] = None  # Total property size in square meters
    floor_area_sq_m: Optional[float] = None  # Usable floor area
    furnished: Optional[bool] = None  # Fully Furnished, Semi-Furnished, Unfurnished
    pets_allowed: Optional[bool] = None
    parking_spaces: Optional[int] = None
    garden: Optional[bool] = None
    balcony: Optional[bool] = None
    terrace: Optional[bool] = None
    swimming_pool: Optional[bool] = None
    heating_type: Optional[str] = None  # Gas, Electric, Oil, Solar, etc.

    # Apartment-Specific Fields
    is_apartment: bool = False
    floor_number: Optional[int] = None  # Floor the unit is on
    total_floors: Optional[int] = None  # Total floors in the building
    elevator: Optional[bool] = None

    # Ownership & Fees
    lease_type: Optional[str] = None  # Freehold, Leasehold, etc.
    service_charge: Optional[float] = None  # Apartment maintenance fees
    property_tax: Optional[float] = None
    rent_payment_frequency: Optional[str] = None

    video_tour_url: Optional[str] = None  # Link to a virtual tour

    # Construction & Legal
    building_condition: Optional[str] = None  # New, Good, Needs Renovation, etc.
    planning_permission: Optional[bool] = None  # For renovations/extensions
    developer_name: str = ""

    def add_price(self, price: float, timestamp: Optional[datetime] = None, current: bool = True, source: Optional[str] = None):
        if timestamp is None:
            timestamp = datetime.now()
        for ph in self.price_history:
            ph.current = False
        self.price_history.append(PriceHistory(price=price, timestamp=timestamp, current=current, source=source))
