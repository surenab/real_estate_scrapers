import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Protocol

from src.models.models import RelaEstateAdvertEnum, RealEstate, Ber, PriceHistory, Seller, RelaEstateImage, Address, Category, Offers


class RealEstateParser(Protocol):
    """_summary_

    Args:
        Protocol (_type_): _description_
    """

    def get_real_estates(self, data: List[Dict]) -> List[RealEstate]:
        """Function to parse scraped data and Return list of RealEstate data objects"""


class DaftRealEstateParser(RealEstateParser):
    """Daft data pasrer"""

    @staticmethod
    def parse_price(price_str: str) -> Dict[str, Optional[str | int]]:
        """
        Parse a price string and return the real price, rent payment frequency, and currency symbol.
        Supports formats like "€1,200 per month", "From €1,000 per month", and "Price on Application".

        :param price_str: The price string to parse.
        :return: A dictionary containing price, frequency, and currency symbol.
        """
        price_str = price_str.strip().replace("From ", "").replace("AMV: ", "")

        if "Price on Application" in price_str or "POA" in price_str:
            return {"price": None, "frequency": None, "currency_symbol": None}

        regex = re.compile(r"([€£]?)\s*(\d[\d,]*\.?\d*)\s*(per\s*(month|week))?", re.IGNORECASE)
        match = regex.match(price_str)

        if not match:
            return {"price": None, "frequency": None, "currency_symbol": None}

        currency_symbol = match.group(1) or "€"  # Default to Euro
        price = int(match.group(2).replace(",", ""))
        frequency = match.group(4) or "month"

        return {"price": price, "frequency": frequency, "currency_symbol": currency_symbol}

    @staticmethod
    def build_category_hierarchy(category_names: List[str]) -> Category:
        """
        Build a hierarchical category structure.

        :param category_names: A list of category names.
        :return: The root Category object.
        """
        parent = None
        root = None
        category = None

        for name in category_names:
            category = Category(name, parent)
            if root is None:
                root = category  # Keep reference to the root category
            parent = category  # Update parent for the next category

        return category

    @staticmethod
    def parse_seller_info(seller_data: Dict[str, str]) -> Seller:
        """
        Parse seller information from raw data.

        :param seller_data: Dictionary containing seller details.
        :return: A Seller object.
        """
        return Seller(
            seller_id=seller_data.get("sellerId"),
            name=seller_data.get("name"),
            phone=seller_data.get("phone"),
            branch=seller_data.get("branch"),
            address=Address(address1=seller_data.get("address")) if seller_data.get("address") else None,
            profile_image=seller_data.get("profileImage"),
            profile_rounded_image=seller_data.get("profileRoundedImage"),
            standard_logo=seller_data.get("standardLogo"),
            square_logo=seller_data.get("squareLogo"),
            background_colour=seller_data.get("backgroundColour"),
            seller_type=seller_data.get("sellerType"),
            available=seller_data.get("sellerAvailable"),
        )

    @staticmethod
    def parse_advert_type(category_data: str) -> Optional[RelaEstateAdvertEnum]:
        """
        Parse the advert type from category data.

        :param category_data: The category name.
        :return: The corresponding advertisement type enum.
        """
        category_map = {
            "Buy": RelaEstateAdvertEnum.SALE,
            "Holiday Homes": RelaEstateAdvertEnum.RENT,
            "Share": RelaEstateAdvertEnum.SHARE,
            "Rent": RelaEstateAdvertEnum.RENT,
            "New Homes": RelaEstateAdvertEnum.SALE,
            "Sold": RelaEstateAdvertEnum.SOLD,
        }
        return category_map.get(category_data)

    @staticmethod
    def parse_ber_info(ber_data: Optional[Dict[str, str]]) -> Optional[Ber]:
        """
        Parse BER (Building Energy Rating) information.

        :param ber_data: Dictionary with BER details.
        :return: A Ber object or None.
        """
        ber = None
        if ber_data:
            ber = Ber(rating=ber_data.get("rating"), code=ber_data.get("code"), epi=ber_data.get("epi"))
        return ber

    @staticmethod
    def parse_media_data(media: Dict[str, List[Dict[str, str]]]) -> Tuple[List[RelaEstateImage], Optional[str]]:
        """
        Extract media images and brochure URL from media data.

        :param media: Dictionary containing media information.
        :return: A tuple with a list of images and an optional brochure URL.
        """
        images = []
        for image_data in media.pop("images", []):
            for size_name in image_data:
                images.append(RelaEstateImage(url=image_data.get(size_name), size_name=size_name))

        # Identifing brochure
        brochure = None
        if media.get("hasBrochure") and "brochure" in media and len(media.get("brochure", [])) > 0:
            brochure = media.get("brochure")[0].get("url")

        return images, brochure

    @staticmethod
    def parse_price_history(price_data: str, publish_date: str, advert_type: RelaEstateAdvertEnum) -> Tuple[PriceHistory, Optional[str]]:
        """
        Parse price history details.

        :param price_data: The price data string.
        :param publish_date: The publish date string.
        :param advert_type: The advert type.
        :return: A tuple containing PriceHistory object and optional frequency.
        """

        parsed_price_data = DaftRealEstateParser.parse_price(price_data)
        price_history = PriceHistory(
            price=parsed_price_data.get("price"),
            currency=parsed_price_data.get("currency_symbol"),
            timestamp=publish_date,
            source="daft",
            category=advert_type,
        )
        return price_history, parsed_price_data.get("frequency")

    @staticmethod
    def parse_address_info(point_data: Dict[str, List[float]]) -> Address:
        """
        Parse address information from coordinate data.

        :param point_data: Dictionary containing latitude and longitude coordinates.
        :return: An Address object.
        """
        coordinates = point_data.get("coordinates")
        address = Address(latitude=coordinates[1], longitude=coordinates[0])
        return address

    @staticmethod
    def parse_bedbathrooms(bedbathrooms_data: Optional[str]) -> Optional[int]:
        """
        Parse the number of bedrooms or bathrooms from raw text.

        :param bedbathrooms_data: The raw bedroom/bathroom data string.
        :return: The number of bedrooms/bathrooms as an integer, or None if unavailable.
        """
        if not bedbathrooms_data:
            return None

        bedbathrooms_map = {"Double": "2", "Single": "1", "Shared": "1", "Twin": "1"}
        for key, value in bedbathrooms_map.items():
            bedbathrooms_data = bedbathrooms_data.replace(key, value)

        try:
            return int(bedbathrooms_data.replace(",", " ").split()[0])
        except (ValueError, IndexError):
            return None

    def get_real_estates(self, data):
        properties = []
        parsed_urls = set()
        for category in data.keys():
            category_data = data.get(category, {})
            for one_data in category_data:

                one_data = one_data.get("listing", {})

                poped_keywords = [
                    "abbreviatedPrice",
                    "daftShortcode",
                    "featuredLevel",
                    "featuredLevelFull",
                    "id",
                    "platform",
                    "premierPartner",
                    "saleType",
                    "state",
                    "sticker",
                    "openViewings",
                    "label",
                    "pageBranding",
                ]
                for keyword in poped_keywords:
                    one_data.pop(keyword, None)

                if one_data.get("seoFriendlyPath") is None:
                    continue

                if one_data.get("title") is None:
                    continue

                # Getting url
                url = "https://www.daft.ie" + one_data.pop("seoFriendlyPath")
                if url in parsed_urls:
                    continue
                title = one_data.pop("title")
                seo_title = one_data.pop("seoTitle")

                parsed_urls.add(url)

                # Getting Seller info
                seller = DaftRealEstateParser.parse_seller_info(one_data.pop("seller", {}))
                # Getting Images
                images, brochure = DaftRealEstateParser.parse_media_data(one_data.pop("media", {}))
                # Identifing Category
                category_type = one_data.pop("category", "")
                advert_type = DaftRealEstateParser.parse_advert_type(category_type)
                # Getting address Info
                if "point" in one_data:
                    address = DaftRealEstateParser.parse_address_info(one_data.pop("point"))
                elif advert_type == RelaEstateAdvertEnum.SOLD:
                    address = Address(address1=title)
                else:
                    address = None
                # Getting BER info
                ber = DaftRealEstateParser.parse_ber_info(one_data.pop("ber", None))
                # Getting publish date
                if "publishDate" in one_data:
                    publish_date = datetime.fromtimestamp(one_data.pop("publishDate") / 1000)
                else:
                    publish_date = None
                # Getting price Info
                current_price_history, rent_payment_frequency = DaftRealEstateParser.parse_price_history(
                    one_data.pop("price", None), publish_date, advert_type
                )
                price_history = [current_price_history]

                sold_price = one_data.pop("soldPrice", None)
                sold_date = one_data.pop("soldDate", None)
                if sold_price and sold_date:
                    sold_date = datetime.strptime(sold_date, "%d/%m/%Y")
                    price_history.append(DaftRealEstateParser.parse_price_history(sold_price, sold_date, advert_type)[0])

                floor_area = None
                if "floorArea" in one_data:
                    floor_area = one_data.pop("floorArea").get("value")

                category = DaftRealEstateParser.build_category_hierarchy(one_data.pop("sections", []))

                # Parsing bedrooms and bathrooms
                bedrooms = DaftRealEstateParser.parse_bedbathrooms(one_data.pop("numBedrooms", None))
                bathrooms = DaftRealEstateParser.parse_bedbathrooms(one_data.pop("numBathrooms", None))

                offers_data = one_data.pop("offers", None)
                offers = None
                if offers_data:
                    offers = Offers.from_dict(offers_data)

                property_size = None
                if "propertySize" in one_data:
                    try:
                        property_size = float(one_data.pop("propertySize").split()[0])
                    except ValueError:
                        property_size = None

                date_of_construction = one_data.pop("dateOfConstruction", None)
                if date_of_construction and date_of_construction == "NA":
                    date_of_construction = None

                if date_of_construction and date_of_construction.isdigit():
                    date_of_construction = int(date_of_construction)

                price_history_data = one_data.pop("priceHistory", [])
                for price_data in price_history_data:
                    old_price = PriceHistory.from_dict(price_data, advert_type)
                    if old_price not in price_history:
                        price_history.append(old_price)

                property_type = one_data.pop("propertyType", None)

                if "prs" in one_data and "subUnits" in one_data.get("prs"):
                    prs = one_data.get("prs")
                    sub_units = prs.pop("subUnits")
                    prs.pop("tagLine")
                    prs.pop("location", None)
                    brochure = prs.pop("brochure", None)
                    about = prs.pop("aboutDevelopment", None)
                    price_history.clear()
                    for unit in sub_units:
                        media = unit.pop("media")
                        unit_images = []
                        for image_data in media.get("images", []):
                            for size_name in image_data:
                                unit_images.append(RelaEstateImage(url=image_data.get(size_name), size_name=size_name))

                        bedrooms = DaftRealEstateParser.parse_bedbathrooms(unit.pop("numBedrooms", None))
                        bathrooms = DaftRealEstateParser.parse_bedbathrooms(unit.pop("numBathrooms", None))
                        current_price_history, rent_payment_frequency = DaftRealEstateParser.parse_price_history(
                            unit.pop("price", None), publish_date, advert_type
                        )
                        price_history = [current_price_history]
                        url = "https://www.daft.ie" + unit.pop("seoFriendlyPath")
                        property_type = unit.pop("propertyType", None)
                        ber.rating = unit.get("ber").pop("rating")
                        properties.append(
                            RealEstate(
                                title=title,
                                seo_title=seo_title,
                                publish_date=publish_date,
                                property_type=property_type,
                                ber=ber,
                                rent_payment_frequency=rent_payment_frequency,
                                price_history=price_history,
                                seller=seller,
                                real_estate_images=unit_images,
                                brochure=brochure,
                                category=category,
                                url=url,
                                date_of_construction=date_of_construction,
                                about=about,
                                sold=False,
                                advert_type=advert_type,
                                address=address,
                                bedrooms=bedrooms,
                                bathrooms=bathrooms,
                                size_sq_m=property_size,
                                floor_area_sq_m=floor_area,
                                offers=offers,
                                # furnished=one_data.pop("seoTitle"),  # Fully Furnished, Semi-Furnished, Unfurnished
                                # pets_allowed=one_data.pop("seoTitle"),
                                # parking_spaces=one_data.pop("seoTitle"),
                                # garden=one_data.pop("seoTitle"),
                                # balcony=one_data.pop("seoTitle"),
                                # terrace=one_data.pop("seoTitle"),
                                # swimming_pool=one_data.pop("seoTitle"),
                                # heating_type=one_data.pop("seoTitle"),  # Gas, Electric, Oil, Solar, etc.
                                # is_apartment=one_data.pop("seoTitle"),
                                # floor_number=one_data.pop("seoTitle"),  # Floor the unit is on
                                # total_floors=one_data.pop("seoTitle"),  # Total floors in the building
                                # elevator=one_data.pop("seoTitle"),
                                # lease_type=one_data.pop("seoTitle"),  # Freehold, Leasehold, etc.
                                # service_charge=one_data.pop("seoTitle"),  # Apartment maintenance fees
                                # property_tax=one_data.pop("seoTitle"),
                                # video_tour_url=one_data.pop("seoTitle"),  # Link to a virtual tour
                                # building_condition=one_data.pop("seoTitle"),  # New, Good, Needs Renovation, etc.
                                # planning_permission=one_data.pop("seoTitle"),  # For renovations/extensions
                                # developer_name=one_data.pop("seoTitle"),
                            )
                        )

                elif one_data and "newHome" in one_data and "subUnits" in one_data.get("newHome"):
                    new_homes = one_data.get("newHome")
                    price_history.clear()
                    sub_units = new_homes.pop("subUnits")
                    developer_name = new_homes.pop("developmentName", None)
                    about = new_homes.pop("about", None)
                    brochure = new_homes.pop("brochure", None)
                    for unit in sub_units:
                        media = unit.pop("media")
                        unit_images = []
                        for image_data in media.get("images", []):
                            for size_name in image_data:
                                unit_images.append(RelaEstateImage(url=image_data.get(size_name), size_name=size_name))

                        property_type = unit.pop("propertyType", None)
                        ber.rating = unit.get("ber").pop("rating")
                        bedrooms = DaftRealEstateParser.parse_bedbathrooms(unit.pop("numBedrooms", None))
                        bathrooms = DaftRealEstateParser.parse_bedbathrooms(unit.pop("numBathrooms", None))
                        current_price_history, rent_payment_frequency = DaftRealEstateParser.parse_price_history(
                            unit.get("price", None), publish_date, advert_type
                        )
                        price_history = [current_price_history]
                        properties.append(
                            RealEstate(
                                title=title,
                                seo_title=seo_title,
                                publish_date=publish_date,
                                property_type=property_type,
                                ber=ber,
                                rent_payment_frequency=rent_payment_frequency,
                                price_history=price_history,
                                seller=seller,
                                real_estate_images=unit_images,
                                brochure=brochure,
                                category=category,
                                url=url,
                                date_of_construction=date_of_construction,
                                about=about,
                                sold=False,
                                advert_type=advert_type,
                                address=address,
                                bedrooms=bedrooms,
                                bathrooms=bathrooms,
                                size_sq_m=property_size,
                                floor_area_sq_m=floor_area,
                                offers=offers,
                                developer_name=developer_name,
                            )
                        )

                else:
                    # Creating real estate propery
                    properties.append(
                        RealEstate(
                            title=title,
                            seo_title=seo_title,
                            publish_date=publish_date,
                            property_type=property_type,
                            ber=ber,
                            rent_payment_frequency=rent_payment_frequency,
                            price_history=price_history,
                            seller=seller,
                            real_estate_images=images,
                            brochure=brochure,
                            category=category,
                            url=url,
                            date_of_construction=date_of_construction,
                            sold=advert_type == RelaEstateAdvertEnum.SOLD,
                            advert_type=advert_type,
                            address=address,
                            bedrooms=bedrooms,
                            bathrooms=bathrooms,
                            size_sq_m=property_size,
                            floor_area_sq_m=floor_area,
                            offers=offers,
                        )
                    )

        return properties
