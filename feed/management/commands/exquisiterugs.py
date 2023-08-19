from django.core.management.base import BaseCommand
from feed.models import ExquisiteRugs

import os
import environ
import pymysql
import xlrd

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Exquisite Rugs"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "validate" in options['functions']:
            processor = Processor()
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            processor = Processor()
            products = ExquisiteRugs.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=True)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=True)


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=ExquisiteRugs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/exquisiterugs-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 2))
                sku = f"ER {mpn}"

                pattern = common.formatText(sh.cell_value(i, 3))
                color = common.formatText(sh.cell_value(i, 4))

                name = common.formatText(sh.cell_value(i, 6))

                # Categorization
                brand = BRAND
                type = "Rug"
                manufacturer = brand
                collection = common.formatText(sh.cell_value(i, 1))

                # Main Information
                description = common.formatText(sh.cell_value(i, 19))
                disclaimer = common.formatText(sh.cell_value(i, 24))

                width = common.formatFloat(sh.cell_value(i, 15))
                length = common.formatFloat(sh.cell_value(i, 16))
                height = common.formatFloat(sh.cell_value(i, 17))

                size = f"{round(width / 12, 2)}'X{round(length / 12, 2)}'"
                dimension = common.formatText(sh.cell_value(i, 18))

                # Additional Information
                upc = common.formatInt(sh.cell_value(i, 13))
                weight = common.formatFloat(sh.cell_value(i, 14))
                care = common.formatText(sh.cell_value(i, 25))
                country = common.formatText(sh.cell_value(i, 35))

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 7))
                map = common.formatFloat(sh.cell_value(i, 8))

                # Measurement
                uom = "Per Item"

                # Tagging
                tags = f"{sh.cell_value(i, 11)}, {sh.cell_value(i, 12)}"
                colors = color

                # Image
                thumbnail = common.formatText(sh.cell_value(i, 51))

                roomsets = []
                for id in range(52, 58):
                    roomset = sh.cell_value(i, id)
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
                statusP = True
                statusS = False

                # Name
                name = f"{name} {size} Rug"

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,
                'name': name,

                'brand': brand,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'disclaimer': disclaimer,
                'width': width,
                'length': length,
                'height': height,
                'size': size,
                'dimension': dimension,

                'care': care,
                'weight': weight,
                'country': country,
                'upc': upc,

                'cost': cost,
                'map': map,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products
