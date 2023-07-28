from django.core.management.base import BaseCommand
from feed.models import Seabrook

import os
import environ
import pymysql
import xlrd

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Seabrook"


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
            products = Seabrook.objects.all()
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
            con=self.con, brand=BRAND, Feed=Seabrook)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/seabrook-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(2, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 3))
                sku = f"SB {mpn}"

                pattern = common.formatText(sh.cell_value(i, 5))
                color = common.formatText(sh.cell_value(i, 10))

                # Categorization
                brand = BRAND

                usage = common.formatText(sh.cell_value(i, 18))
                if usage in ["Sidewall", "Mural", "Residential Use"]:
                    type = "Wallpaper"
                elif usage == "Fabric":
                    type = "Fabric"
                else:
                    type = usage

                manufacturer = f"{BRAND} {type}"

                collection = common.formatText(sh.cell_value(i, 2))

                # Main Information
                description = common.formatText(sh.cell_value(i, 6))

                if float(sh.cell_value(i, 34)) != 0 and float(sh.cell_value(i, 33)) != 0:
                    repeat = "{} in / {} cm".format(float(sh.cell_value(i, 34)),
                                                    float(sh.cell_value(i, 33)))
                else:
                    repeat = ""

                width = common.formatFloat(sh.cell_value(i, 29))
                length = common.formatFloat(sh.cell_value(i, 30))
                size = f"{common.formatText(sh.cell_value(i, 32))} sqft"

                # Additional Information
                finish = common.formatText(sh.cell_value(i, 11))
                material = common.formatText(sh.cell_value(i, 40))
                care = common.formatText(sh.cell_value(i, 38))
                specs = [("Removal", common.formatText(sh.cell_value(i, 39)))]
                weight = common.formatFloat(sh.cell_value(i, 21))
                country = common.formatText(sh.cell_value(i, 42))
                yards = common.formatFloat(sh.cell_value(i, 22))
                upc = common.formatInt(sh.cell_value(i, 16))

                # Pricing
                if 'Bolt' in sh.cell_value(i, 43):
                    cost = common.formatFloat(sh.cell_value(i, 13))
                    map = common.formatFloat(sh.cell_value(i, 15))
                else:
                    cost = common.formatFloat(sh.cell_value(i, 12))
                    map = common.formatFloat(sh.cell_value(i, 14))

                if cost == 0:
                    debug.debug(BRAND, 1, f"Cost Error for MPN: {mpn}")
                    continue

                # Measurement
                if 'S/R' in sh.cell_value(i, 43) or 'Bolt' in sh.cell_value(i, 43) or 'Roll' in sh.cell_value(i, 43):
                    uom = "Per Roll"
                elif 'Yd' in sh.cell_value(i, 43) or 'Mural' in sh.cell_value(i, 43) or 'Yard' in sh.cell_value(i, 43):
                    uom = 'Per Yard'
                else:
                    uom = sh.cell_value(i, 43)

                # Tagging
                tags = f"{sh.cell_value(i, 7)}, {sh.cell_value(i, 8)}"
                colors = str(sh.cell_value(i, 9))

                # Image
                thumbnail = sh.cell_value(i, 45)
                roomsets = [sh.cell_value(i, 46)]

                # Status
                if collection == 'Lillian August Grasscloth Binder' or collection == 'Indigo' or collection == 'New Hampton':
                    statusP = False
                else:
                    statusP = True

                if common.formatText(sh.cell_value(i, 17)) == "Y" and "JP3" not in mpn:
                    statusS = True
                else:
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
                'usage': usage,
                'width': width,
                'length': length,
                'size': size,
                'repeat': repeat,

                'material': material,
                'finish': finish,
                'care': care,
                'specs': specs,
                'weight': weight,
                'country': country,
                'yards': yards,
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
