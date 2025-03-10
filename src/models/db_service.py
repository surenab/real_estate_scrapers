import sys
import os
import dataset
from dataclasses import asdict
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.models.models import Address, Seller, RealEstate, PriceHistory, RelaEstateImage, Category, Ber, Offers


class DBConnect:
    """
    DBConnect is responsible for managing database connections.
    This ensures a single source of truth for database connections,
    following the Dependency Inversion Principle (SOLID).
    """

    def __init__(self, db_url: str = "sqlite:///realestate.db"):
        """Init Db Connector

        Args:
            db_url (str, optional): db url address. Defaults to "sqlite:///realestate.db".
        """
        self.db = dataset.connect(db_url)

    def get_db(self):
        return self.db


class SQLService:
    """
    SQLService handles all database operations.
    It ensures data persistence while keeping the code DRY and adhering to SOLID principles.
    """

    def __init__(self, db_connect: DBConnect):
        self.db = db_connect.get_db()
        self.address_table = self.db["addresses"]
        self.seller_table = self.db["sellers"]
        self.images_table = self.db["real_estate_images"]
        self.price_history_table = self.db["price_history"]
        self.real_estate_table = self.db["realestate"]
        self.category_table = self.db["category"]
        self.ber_table = self.db["ber"]
        self.offers_table = self.db["offers"]

    def get_real_estate_urls(self) -> list:
        """Fetch all URLs from the real_estate table and remove 'https://www.daft.ie' prefix."""
        urls = [row["url"] for row in self.real_estate_table.all()]
        cleaned_urls = [url.replace("https://www.daft.ie", "") for url in urls if url.startswith("https://www.daft.ie")]
        return cleaned_urls

    def get_existing_record(self, table, data):
        """Check if a record with the same fields exists and return its ID if found."""
        return table.find_one(**data)

    def insert_offers(self, offers: Offers) -> int:
        data = asdict(offers)
        return self.offers_table.insert(data)

    def insert_ber(self, ber: Ber) -> int:
        data = asdict(ber)
        existing_ber = self.get_existing_record(self.ber_table, data)
        return existing_ber["id"] if existing_ber else self.ber_table.insert(data)

    def insert_address(self, address: Address) -> int:
        data = asdict(address)
        existing_address = self.get_existing_record(self.address_table, data)
        return existing_address["id"] if existing_address else self.address_table.insert(data)

    def insert_category(self, category: Category) -> int:
        data = asdict(category)

        # Recursively insert parent categories and get the topmost available parent_id
        parent_id = None
        if category.parent:
            parent_id = self._ensure_parent_exists(category.parent)

        data["parent"] = parent_id  # Store the resolved parent ID (or None if root category)

        existing_category = self.get_existing_record(self.category_table, data)
        return existing_category["id"] if existing_category else self.category_table.insert(data)

    def _ensure_parent_exists(self, category: Category) -> int:
        """Recursively ensures the parent category exists and returns its ID."""
        parent_category = self.category_table.find_one(name=category.name)

        if parent_category:
            return parent_category["id"]  # Return existing ID

        # Recursively ensure parent of parent exists
        parent_id = None
        if category.parent:
            parent_id = self._ensure_parent_exists(category.parent)

        data = asdict(category)
        data["parent"] = parent_id  # Store resolved parent ID

        existing_category = self.get_existing_record(self.category_table, data)
        return existing_category["id"] if existing_category else self.category_table.insert(data)

    def insert_seller(self, seller: Seller) -> int:
        data = asdict(seller)

        if seller.address:
            addr_id = self.insert_address(seller.address)
            data["address_id"] = addr_id
        else:
            data["address_id"] = None

        del data["address"]

        existing_seller = self.get_existing_record(self.seller_table, data)
        return existing_seller["id"] if existing_seller else self.seller_table.insert(data)

    def insert_image(self, image: RelaEstateImage, realestate_id: int) -> int:
        data = asdict(image)
        data["realestate_id"] = realestate_id
        return self.images_table.insert(data)

    def insert_price_history(self, ph: PriceHistory, realestate_id: int) -> int:
        data = asdict(ph)
        data["timestamp"] = ph.timestamp.isoformat() if ph.timestamp else None
        data["realestate_id"] = realestate_id
        data["category"] = ph.category.value
        return self.price_history_table.insert(data)

    def insert_real_estate(self, realestate: RealEstate) -> int:
        data = asdict(realestate)

        if realestate.address:
            addr_id = self.insert_address(realestate.address)
        else:
            addr_id = None
        data["address_id"] = addr_id

        if realestate.offers:
            offers_id = self.insert_offers(realestate.offers)
        else:
            offers_id = None
        data["offers_id"] = offers_id

        if realestate.ber:
            ber_id = self.insert_ber(realestate.ber)
        else:
            ber_id = None
        data["ber_id"] = ber_id

        if realestate.seller:
            seller_id = self.insert_seller(realestate.seller)
        else:
            seller_id = None
        data["seller_id"] = seller_id

        if realestate.category:
            category_id = self.insert_category(realestate.category)
        else:
            category_id = None
        data["category_id"] = category_id

        data.pop("address", None)
        data.pop("seller", None)
        data.pop("category", None)
        data.pop("ber", None)

        data.pop("real_estate_images", [])
        data.pop("price_history", [])

        data.pop("offers", None)

        data["publish_date"] = realestate.publish_date.isoformat() if realestate.publish_date else None
        data["date_of_construction"] = realestate.date_of_construction
        data["advert_type"] = realestate.advert_type.value

        realestate_id = self.real_estate_table.insert(data)

        for img in realestate.real_estate_images:
            self.insert_image(img, realestate_id)

        for ph in realestate.price_history:
            self.insert_price_history(ph, realestate_id)

        return realestate_id


# ----------------------
# Example Usage
# ----------------------


def main():
    db_connect = DBConnect()
    sql_service = SQLService(db_connect)

    address = Address(
        address1="123 Main St",
        city="Anytown",
        postal_code="12345",
        county="AnyCounty",
        country="CountryX",
        latitude=40.7128,
        longitude=-74.0060,
        local_authority="LocalAuth",
    )

    seller = Seller(
        seller_id=1,
        name="John Doe",
        phone="555-1234",
        branch="Branch A",
        address=address,
        profile_image="http://example.com/profile.jpg",
    )

    image = RelaEstateImage(url="http://example.com/image1.jpg", size_name="size720x480")

    ph1 = PriceHistory(price=100.0, timestamp=datetime.now(), current=True, source="source1")

    parent_category = Category("Property")

    category = Category("Rental", parent=parent_category)

    realestate = RealEstate(
        title="Sample Property",
        seo_title="Sample SEO Title",
        publish_date=datetime.now(),
        property_type="Apartment",
        address=address,
        seller=seller,
        real_estate_images=[image],
        category=category,
        url="http://example.com/property",
        price_history=[ph1],
        date_of_construction=datetime.now(),
    )

    realestate_id = sql_service.insert_real_estate(realestate)
    print(f"Inserted RealEstate with id: {realestate_id}")


if __name__ == "__main__":
    main()
