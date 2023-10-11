import xlrd
import pymysql
import environ
import os
from feed.models import Poppy
from django.core.management.base import BaseCommand

from library import database, debug, common

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Poppy"


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
            products = Poppy.objects.all()
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
            processor.databaseManager.downloadImages(missingOnly=True)


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)
        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Poppy)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/poppy-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(2, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 2))
                sku = f"TP {mpn}"

                pattern = common.formatText(sh.cell_value(i, 3))
                color = common.formatText(sh.cell_value(i, 4))

                # Categorization
                brand = BRAND
                type = "Wallpaper"
                manufacturer = "Poppy Print Studio"
                collection = common.formatText(sh.cell_value(i, 1))

                # Main Information
                description = common.formatText(sh.cell_value(i, 8))
                width = common.formatFloat(sh.cell_value(i, 16))
                length = common.formatFloat(sh.cell_value(i, 17)) * 12
                size = common.formatText(sh.cell_value(i, 18))
                repeatV = common.formatFloat(sh.cell_value(i, 20))
                repeatH = common.formatFloat(sh.cell_value(i, 21))

                # Additional Information
                yards = common.formatInt(sh.cell_value(i, 13))
                weight = common.formatFloat(sh.cell_value(i, 19))
                country = common.formatText(sh.cell_value(i, 29))

                match = common.formatText(sh.cell_value(i, 22))
                paste = common.formatText(sh.cell_value(i, 23))
                material = common.formatText(sh.cell_value(i, 24))
                washability = common.formatText(sh.cell_value(i, 25))
                removability = common.formatText(sh.cell_value(i, 26))
                features = [
                    f"Match: {match}",
                    f"Paste: {paste}",
                    f"Material: {material}",
                    f"Washability: {washability}",
                    f"Removability: {removability}",
                ]

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 9))
                map = common.formatFloat(sh.cell_value(i, 10))

                # Measurement
                uom = f"Per {common.formatText(sh.cell_value(i, 12))}"

                # Tagging
                colors = color
                tags = f"{match}, {paste}, {material}, {washability}, {removability}, {common.formatText(sh.cell_value(i, 27))}, {collection}, {pattern}, {description}"

                # Image
                thumbnail = f'https://drive.google.com/u/0/uc?id={sh.cell_value(i, 30).replace("https://drive.google.com/file/d/", "").split("/")[0]}&export=download'

                roomsets = []
                for id in range(31, 35):
                    roomset = f'https://drive.google.com/u/0/uc?id={sh.cell_value(i, id).replace("https://drive.google.com/file/d/", "").split("/")[0]}&export=download'
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
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
                'width': width,
                'length': length,
                'size': size,
                'repeatV': repeatV,
                'repeatH': repeatH,

                'yards': yards,
                'weight': weight,
                'country': country,
                'features': features,

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
