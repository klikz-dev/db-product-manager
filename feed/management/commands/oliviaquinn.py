from django.core.management.base import BaseCommand
from feed.models import OliviaQuinn

import os
import environ
import pymysql
import xlrd

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Olivia & Quinn"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=False)

        if "update" in options['functions']:
            processor = Processor()
            products = OliviaQuinn.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=False)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=False)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "white-glove" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove", logic=True)

        if "best-seller" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="bestSeller", tag="Best Selling")

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=False)

        if "inventory" in options['functions']:
            processor = Processor()
            processor.inventory()


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=OliviaQuinn)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Product Feed
        products = []
        wb = xlrd.open_workbook(f"{FILEDIR}/oliviaquinn-master.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(2, sh.nrows):
            try:
                # Primary Keys
                pattern = common.formatText(sh.cell_value(i, 3))
                color = common.formatText(sh.cell_value(i, 4))

                mpn = common.formatInt(sh.cell_value(i, 2))

                # Buggy MPN
                mpn = f"{mpn}-{pattern.replace(' ', '-')}-{color.replace(' ', '-')}"
                sku = f"OQ {mpn}"

                # Categorization
                brand = BRAND
                type = common.formatText(sh.cell_value(i, 5)).title()
                manufacturer = brand
                collection = common.formatText(sh.cell_value(i, 1))

                # Main Information
                description = common.formatText(sh.cell_value(i, 19))

                width = common.formatFloat(sh.cell_value(i, 16))
                height = common.formatFloat(sh.cell_value(i, 15))
                depth = common.formatFloat(sh.cell_value(i, 17))
                dimension = common.formatText(sh.cell_value(i, 18))

                weight = common.formatFloat(sh.cell_value(i, 14))
                specs = [
                    ("Weight", f"{weight} lbs"),
                ]

                # Additional Information
                material = common.formatText(sh.cell_value(i, 12))
                country = common.formatText(sh.cell_value(i, 35))

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 7))

                # Measurement
                uom = "Per Item"

                # Taggingf
                colors = color
                tags = f"{material}, {description}"

                # Image
                thumbnail = sh.cell_value(i, 51).replace("dl=0", "dl=1")

                roomsets = []
                for id in range(52, 65):
                    roomset = sh.cell_value(i, id).replace("dl=0", "dl=1")
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
                statusP = True
                statusS = False

                # Shipping
                boxHeight = common.formatFloat(sh.cell_value(i, 43))
                boxWidth = common.formatFloat(sh.cell_value(i, 44))
                boxDepth = common.formatFloat(sh.cell_value(i, 45))
                boxWeight = common.formatFloat(sh.cell_value(i, 42))
                if boxWidth > 107 or boxHeight > 107 or boxDepth > 107 or boxWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                # Type Mapping
                name = f"{pattern} {color} {type}"
                type_map = {
                    "Sofa": "Sofas",
                    "Swivel Chair": "Chairs",
                    "Chair": "Chairs",
                    "Ottoman": "Ottomans",
                    "Loveseat": "Chairs",
                    "Executive Swivel Chair": "Chairs",
                    "Swivel Ottoman": "Ottomans",
                    "Bench": "Benches",
                    "Bench Ottoman": "Ottomans",
                    "Cube Ottoman": "Ottomans",
                }
                if type in type_map:
                    type = type_map[type]

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,
                "name": name,

                'brand': brand,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'width': width,
                'height': height,
                'depth': depth,
                'dimension': dimension,
                'specs': specs,

                'material': material,
                'country': country,

                'cost': cost,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,

                'whiteGlove': whiteGlove,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        products = OliviaQuinn.objects.all()
        for product in products:
            stock = {
                'sku': product.sku,
                'quantity': 5,
                'note': ''
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=3)
