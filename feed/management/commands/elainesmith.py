from django.core.management.base import BaseCommand
from feed.models import ElaineSmith

import os
import environ
import pymysql
import xlrd

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Elaine Smith"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "validate" in options['functions']:
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            products = ElaineSmith.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "image" in options['functions']:
            processor.databaseManager.downloadImages(missingOnly=True)


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=ElaineSmith)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/elainesmith-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 0))
                sku = "ES {}".format(mpn)

                pattern = common.formatText(sh.cell_value(i, 1))
                color = common.formatText(sh.cell_value(i, 16))

                # Categorization
                brand = BRAND
                type = "Pillow"
                manufacturer = f"{BRAND} {type}"
                collection = pattern

                # Main Information
                description = common.formatText(sh.cell_value(i, 15))
                size = common.formatText(sh.cell_value(i, 2))

                # Additional Information

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 4))
                map = common.formatFloat(sh.cell_value(i, 5))
                msrp = common.formatFloat(sh.cell_value(i, 6))

                # Measurement
                uom = "Per Item"

                # Tagging
                tags = f"{str(sh.cell_value(i, 17))}, {str(sh.cell_value(i, 18))}, {pattern}, {description}"
                colors = color

                # Image
                thumbnail = sh.cell_value(i, 7)
                roomsets = []
                for id in range(8, 15):
                    if sh.cell_value(i, id):
                        roomsets.append(sh.cell_value(i, id))

                # Status
                statusP = True
                statusS = False

                # Stock

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
                'size': size,

                'cost': cost,
                'map': map,
                'msrp': msrp,
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
