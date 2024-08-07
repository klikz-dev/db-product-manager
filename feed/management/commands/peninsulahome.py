from django.core.management.base import BaseCommand
from feed.models import PeninsulaHome

import os
import environ
import pymysql
import xlrd
import time
import datetime

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Peninsula Home"


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
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            processor = Processor()
            products = PeninsulaHome.objects.all()
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

        if "white-glove" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove", logic=True)

        if "quick-ship" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="quickShip", tag="Quick Ship")

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=False)

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    files = processor.databaseManager.browseSFTP(
                        src="/peninsulahome/")
                    for file in files:
                        if "xlsx" in file:
                            processor.databaseManager.downloadFileFromSFTP(
                                src=f"/peninsulahome/{file}", dst=f"{FILEDIR}/peninsulahome-inventory.xlsx", fileSrc=True, delete=True)

                    products = processor.fetchFeed()
                    processor.databaseManager.writeFeed(products=products)
                    processor.databaseManager.statusSync(fullSync=False)

                    processor.inventory()

                print("Finished process. Waiting for next run. {}:{}".format(
                    BRAND, options['functions']))
                time.sleep(86400)


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=PeninsulaHome)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Stocks & discontinued
        stocks = {}
        wb = xlrd.open_workbook(f"{FILEDIR}/peninsulahome-inventory.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            mpn = common.formatText(sh.cell_value(i, 0))
            stockP = common.formatFloat(sh.cell_value(i, 1))

            stockNote = sh.cell_value(i, 2)
            if str(stockNote).strip():
                date_tuple = xlrd.xldate_as_tuple(stockNote, wb.datemode)
                date_obj = datetime.datetime(*date_tuple)
                stockNote = date_obj.date()

            stocks[mpn] = (stockP, stockNote)

        discontinuedMPNs = []
        sh = wb.sheet_by_index(1)
        for i in range(1, sh.nrows):
            mpn = common.formatText(sh.cell_value(i, 0))
            discontinuedMPNs.append(mpn)

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/peninsulahome-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(2, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 0))
                sku = f"PH {mpn}"

                name = common.formatText(
                    sh.cell_value(i, 1)).replace(" ,", ",")

                if "," in name:
                    pattern = name.split(",")[0].strip()
                    color = name.split(",")[1].strip()
                elif sh.cell_value(i, 13):
                    pattern = name
                    color = common.formatText(sh.cell_value(i, 13))
                else:
                    pattern = name
                    color = name

                # Categorization
                brand = BRAND
                type = "Furniture"
                manufacturer = brand
                collection = common.formatText(sh.cell_value(i, 2))

                # Main Information
                description = common.formatText(sh.cell_value(i, 12))
                width = common.formatFloat(sh.cell_value(i, 9))
                height = common.formatFloat(sh.cell_value(i, 8))
                depth = common.formatFloat(sh.cell_value(i, 10))
                dimension = common.formatText(sh.cell_value(i, 11))

                weight = common.formatFloat(sh.cell_value(i, 7))
                specs = [
                    ("Weight", f"{weight} lbs"),
                ]

                # Additional Information
                material = common.formatText(sh.cell_value(i, 13))
                country = common.formatText(sh.cell_value(i, 15))
                features = []
                if sh.cell_value(i, 14):
                    features.append(
                        f"Fabric: {common.formatText(sh.cell_value(i, 14))}")

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 3))
                map = common.formatFloat(sh.cell_value(i, 4))

                # Measurement
                uom = f"Per Item"

                # Tagging
                colors = color
                tags = f"{material}, {name}, {description}"

                # Image
                thumbnail = sh.cell_value(i, 25).replace("dl=0", "dl=1")

                roomsets = []
                for id in range(26, 32):
                    roomset = sh.cell_value(i, id).replace("dl=0", "dl=1")
                    if roomset != "":
                        roomsets.append(roomset)

                # Status
                if mpn in discontinuedMPNs:
                    statusP = False
                else:
                    statusP = True
                statusS = False

                # Shipping
                shippingHeight = common.formatFloat(sh.cell_value(i, 20))
                shippingWidth = common.formatFloat(sh.cell_value(i, 21))
                shippingDepth = common.formatFloat(sh.cell_value(i, 22))
                shippingWeight = common.formatFloat(sh.cell_value(i, 19))
                if shippingWidth > 95 or shippingHeight > 95 or shippingDepth > 95 or shippingWeight > 40:
                    whiteGlove = True
                else:
                    whiteGlove = False

                leadtime = common.formatText(sh.cell_value(i, 17))
                if "days" in leadtime.lower() or "hours" in leadtime.lower() or "1 week" == leadtime.lower():
                    quickShip = True
                else:
                    quickShip = False

                # Stock
                if mpn in stocks:
                    stockP, stockNote = stocks[mpn]
                else:
                    stockP = 0
                    stockNote = ""

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
                'width': width,
                'height': height,
                'depth': depth,
                'dimension': dimension,
                'specs': specs,

                'material': material,
                'country': country,
                'features': features,

                'weight': shippingWeight,

                'cost': cost,
                'map': map,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,

                'whiteGlove': whiteGlove,
                'quickShip': quickShip,

                'stockP': stockP,
                'stockNote': stockNote
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        products = PeninsulaHome.objects.all()
        for product in products:
            stock = {
                'sku': product.sku,
                'quantity': product.stockP,
                'note': product.stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
