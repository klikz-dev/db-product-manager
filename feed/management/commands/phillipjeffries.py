from django.core.management.base import BaseCommand
from feed.models import PhillipJeffries

import os
import environ
import pymysql
import requests
import json
import xlrd

from library import database, debug

API_BASE_URL = "https://www.phillipjeffries.com/api/products/skews"

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Phillip Jeffries"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            processor.feed()

        if "sync" in options['functions']:
            processor.sync()

        if "add" in options['functions']:
            processor.add()

        if "update" in options['functions']:
            processor.update()

        if "price" in options['functions']:
            processor.price()

        if "tag" in options['functions']:
            processor.tag()


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(self.con, BRAND)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(FILEDIR + "pj-master-2023.04.05.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                try:
                    mpn = int(sh.cell_value(i, 0))
                except:
                    mpn = str(sh.cell_value(i, 0))

                debug.debug(BRAND, 0, "Fetching Product MPN: {}".format(mpn))
                response = requests.get("{}/{}.json".format(API_BASE_URL, mpn))
                data = json.loads(response.text)

                sku = 'PJ {}'.format(mpn)
                pattern = str(data["collection"]["name"]
                              ).replace("NEW - ", "").strip()
                color = str(data["name"]).replace(
                    pattern, "").replace("-", "").replace(pattern, "").strip()

                if pattern == "" or color == "":
                    continue

                # Categorization
                brand = BRAND
                type = "Wallpaper"
                manufacturer = "{} {}".format(brand, type)
                if "collection" in data and "binders" in data["collection"] and len(data["collection"]["binders"]) > 0:
                    collection = str(data["collection"]["binders"][0]["name"])
                else:
                    collection = ""

                # Main Information
                description = str(data["collection"]["description"])
                usage = "Wallcovering"

                # Additional Information
                specs = [
                    {
                        "key": "Width",
                        "value": str(data["specs"]["width"])
                    },
                    {
                        "key": "Horizontal Repeat",
                        "value": str(data["specs"]["horizontal_repeat"])
                    },
                    {
                        "key": "Vertical Repeat",
                        "value": str(data["specs"]["vertical_repeat"])
                    },
                ]
                features = [data["specs"]["maintenance"]]

                # Measurement
                try:
                    uom = data["order"]["wallcovering"]["price"]["unit_of_measure"]
                    if "YARD" == uom:
                        uom = "Per Yard"
                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    continue

                try:
                    minimum = int(
                        data["order"]["wallcovering"]["minimum_order"])
                    incre = data["order"]["wallcovering"]["order_increment"]
                    if int(float(incre)) > 1:
                        increment = ",".join(
                            [str(ii * int(float(incre))) for ii in range(1, 21)])
                    else:
                        increment = ""
                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    continue

                # Pricing
                cost = float(str(sh.cell_value(i, 2)).replace("$", ""))

                # Tagging
                tags = "{}, {}".format(collection, description)
                colors = color

                # Assets
                thumbnail = data["assets"]["about_header_src"]

                # Availability
                statusP = True
                statusS = True

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,

                'brand': brand,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'usage': usage,

                'specs': specs,
                'features': features,

                'uom': uom,
                'minimum': minimum,
                'increment': increment,

                'tags': tags,
                'colors': colors,

                'cost': cost,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def feed(self):
        products = self.fetchFeed()
        self.databaseManager.writeFeed(products)

    def sync(self):
        self.databaseManager.statusSync(fullSync=False)

    def add(self):
        self.databaseManager.createProducts(formatPrice=True)

    def update(self):
        products = PhillipJeffries.objects.all()
        self.databaseManager.updateProducts(
            products=products, formatPrice=True)

    def price(self):
        self.databaseManager.updatePrices(formatPrice=True)

    def tag(self):
        self.databaseManager.updateTags(category=True)

    def cutFee(self):
        self.databaseManager.customTags(key="cutFee", tag="Cut Fee")
