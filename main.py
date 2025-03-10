import json
import datetime
from src.models.db_service import DBConnect, SQLService
from src.scrapers.data_parsers import DaftRealEstateParser
from src.scrapers.daft_scraper import DaftScraper
from real_estate_static_map_gen import generate_html


def update_daft_data():
    daft_scraper = DaftScraper()
    db_connect = DBConnect()
    sql_service = SQLService(db_connect)
    ignore_ids = sql_service.get_real_estate_urls()

    categories = {
        "sharing": "sharing",
        "residential-to-rent": "residential-to-rent",
        "residential-for-sale": "residential-for-sale",
        "new-homes": "new-homes",
        "holiday-homes": "holiday-homes",
    }
    data = {}

    for tcategory in categories:
        data[tcategory] = daft_scraper.scrape_all_pages(tcategory, ignore_ids)

    with open(f"daft_updated_data_{str(datetime.datetime.now())}.json", "w", encoding="utf8") as json_file:
        json.dump(data, json_file)

    daft_parser = DaftRealEstateParser()
    properties = daft_parser.get_real_estates(data)

    ignore_ids = sql_service.get_real_estate_urls()
    scraped_urls = set()
    for realestate in properties:
        if realestate.url.replace("https://www.daft.ie", "") in ignore_ids:
            continue

        if realestate.url in scraped_urls:
            continue
        scraped_urls.add(realestate.url)

        realestate_id = sql_service.insert_real_estate(realestate)
        print(f"Inserted RealEstate with id: {realestate_id}")
    print(f"Added {len(scraped_urls)} items")


def daft_init_data():

    daft_parser = DaftRealEstateParser()
    with open("daft_test_data.json", "r", encoding="utf8") as json_file:
        data = json.load(json_file)

    properties = daft_parser.get_real_estates(data)

    with open("daft_test_data_new_and_holiday.json", "r", encoding="utf8") as json_file:
        data = json.load(json_file)

    properties.extend(daft_parser.get_real_estates(data))

    generate_html(properties, "static_map.html")
    print(len(properties))
    db_connect = DBConnect()
    sql_service = SQLService(db_connect)

    scraped_urls = set()
    for realestate in properties:
        if realestate.url in scraped_urls:
            continue
        scraped_urls.add(realestate.url)
        realestate_id = sql_service.insert_real_estate(realestate)
        print(f"Inserted RealEstate with id: {realestate_id}")


def daft_sold_init_data():

    daft_parser = DaftRealEstateParser()
    with open("daft_test_data_sold_0_datax.json", "r", encoding="utf8") as json_file:
        data = json.load(json_file)

    properties = daft_parser.get_real_estates(data)
    generate_html(properties, "static_map_sold.html")
    print(len(properties))
    db_connect = DBConnect()
    sql_service = SQLService(db_connect)

    scraped_urls = set()
    for realestate in properties:
        if realestate.url in scraped_urls:
            continue
        scraped_urls.add(realestate.url)
        realestate_id = sql_service.insert_real_estate(realestate)
        print(f"Inserted RealEstate with id: {realestate_id}")


if __name__ == "__main__":
    daft_init_data()
    daft_sold_init_data()
    update_daft_data()
