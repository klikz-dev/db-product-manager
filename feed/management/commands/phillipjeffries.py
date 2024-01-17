from django.core.management.base import BaseCommand
from feed.models import PhillipJeffries

import os
import environ
import pymysql
import requests
import json
import xlrd

from library import database, debug, common

API_BASE_URL = "https://www.phillipjeffries.com/api/products/skews"

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Phillip Jeffries"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products)

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            processor = Processor()
            products = PhillipJeffries.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=False)

        if "quick-ship" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="quickShip", tag="Quick Ship")


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=PhillipJeffries)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/phillipjeffries-master.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatInt(sh.cell_value(i, 0))
                if mpn == 0:
                    continue
                if mpn < 100:
                    mpn = f"0{mpn}"

                sku = 'PJ {}'.format(mpn)

                debug.debug(BRAND, 0, "Fetching Product MPN: {}".format(mpn))
                response = requests.get("{}/{}.json".format(API_BASE_URL, mpn))
                data = json.loads(response.text)

                pattern = common.formatText(data['collection']['name'])
                color = common.formatText(data['specs']['color'])

                # Categorization
                brand = BRAND
                type = "Wallpaper"
                manufacturer = f"{brand} {type}"

                collection = ""
                for binder in data['collection']['binders']:
                    if binder['name']:
                        collection = common.formatText(binder['name'])
                        break

                # Main Information
                description = common.formatText(
                    data['collection']['description'])

                # Additional Information
                specs = []
                for key, value in data['specs'].items():
                    if value:
                        specs.append((key.replace("_", " ").title(), value))

                # Measurement
                uom = "Per Yard"
                minimum = common.formatInt(
                    data['order']['wallcovering']['minimum_order'])
                incre = common.formatInt(
                    data['order']['wallcovering']['order_increment'])
                increment = ",".join([str(i * incre) for i in range(1, 21)])

                # Pricing
                cost = common.formatFloat(
                    data['order']['wallcovering']['price']['amount'])

                # Tagging
                tags = f"{collection}, {description}, {pattern}"
                colors = color

                # Assets
                thumbnail = f"https://www.phillipjeffries.com{data['assets']['download_src']}"

                # Status
                statusP = True
                statusS = True

                if data['order']['wallcovering']['purcode'] == "NJSTOCKED":
                    quickShip = True
                else:
                    quickShip = False

            except Exception as e:
                print(e)
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

                'specs': specs,

                'uom': uom,
                'minimum': minimum,
                'increment': increment,

                'tags': tags,
                'colors': colors,

                'cost': cost,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,
                'quickShip': quickShip
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products
