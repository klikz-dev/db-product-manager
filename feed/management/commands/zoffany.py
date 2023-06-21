from django.core.management.base import BaseCommand
from feed.models import Zoffany

import os
import environ
import pymysql
import xlrd
import time
import csv
import codecs
from shutil import copyfile

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Zoffany"


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
            products = Zoffany.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=True)

        if "roomset" in options['functions']:
            processor = Processor()
            processor.roomset()

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="", dst=f"{FILEDIR}/zoffany-inventory.csv", fileSrc=False)
                    processor.inventory()

                    print("Finished process. Waiting for next run. {}:{}".format(
                        BRAND, options['functions']))
                    time.sleep(86400)


class Processor:
    def __init__(self):
        self.env = environ.Env()
        self.con = pymysql.connect(host=self.env('MYSQL_HOST'), user=self.env('MYSQL_USER'), passwd=self.env(
            'MYSQL_PASSWORD'), db=self.env('MYSQL_DATABASE'), connect_timeout=5)
        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Zoffany)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Best Sellers
        bestSellingMPNs = []

        # wb = xlrd.open_workbook(FILEDIR + "/files/zoffany-bestsellers.xlsx")
        # sh = wb.sheet_by_index(0)

        # for i in range(3, sh.nrows):
        #     bestSellingMPNs.append(common.formatText(sh.cell_value(i, 1)))

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/zoffany-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 2))
                sku = f"ZOF {mpn}"

                pattern = common.formatText(sh.cell_value(i, 8))
                color = common.formatText(sh.cell_value(i, 9))

                # Categorization
                brand = BRAND

                type = str(sh.cell_value(i, 12))
                if type == "WP":
                    type = "Wallpaper"
                elif type == "FB":
                    type = "Fabric"

                manufacturer = f"{common.formatText(sh.cell_value(i, 21)).title()} {type}"
                collection = common.formatText(sh.cell_value(i, 7))

                # Main Information
                description = common.formatText(sh.cell_value(i, 25))
                usage = common.formatText(sh.cell_value(i, 13))
                width = common.formatFloat(sh.cell_value(i, 18))
                repeatH = common.formatFloat(sh.cell_value(i, 20))
                repeatV = common.formatFloat(sh.cell_value(i, 19))

                # Additional Information
                match = common.formatText(sh.cell_value(i, 14))
                yards = common.formatFloat(sh.cell_value(i, 17))
                features = [
                    f"Reversible: {common.formatText(sh.cell_value(i, 15))}"]

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 4))
                map = common.formatFloat(sh.cell_value(i, 5))
                msrp = common.formatFloat(sh.cell_value(i, 6))

                # Measurement
                uom = common.formatText(sh.cell_value(i, 11))
                if uom.lower() == "yard" or uom.lower() == "y":
                    uom = "Per Yard"
                elif uom.lower() == "roll" or uom.lower() == "r":
                    uom = "Per Roll"
                elif uom.lower() == "panel":
                    uom = "Per Panel"

                minimum = 2

                # Tagging
                tags = f"{sh.cell_value(i, 10)}, {collection}, {usage}, {description}"
                colors = color

                # Image
                thumbnail = sh.cell_value(i, 24)

                # Status
                statusP = True
                statusS = False

                if mpn in bestSellingMPNs:
                    bestSeller = True
                else:
                    bestSeller = False

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
                'repeatH': repeatH,
                'repeatV': repeatV,

                'match': match,
                'yards': yards,
                'features': features,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'uom': uom,
                'minimum': minimum,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,
                'bestSeller': bestSeller
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def roomset(self):
        fnames = os.listdir(f"{FILEDIR}/images/zoffany/")
        for fname in fnames:
            if "_" in fname:
                mpn = fname.split("_")[0]
                idx = int(fname.split("_")[1].replace(".jpg", "")) + 1

                try:
                    product = Zoffany.objects.get(mpn=mpn)

                    if product.productId:
                        copyfile(f"{FILEDIR}/images/zoffany/{fname}",
                                 f"{FILEDIR}/../../../images/roomset/{product.productId}_{idx}.jpg")

                    os.remove(f"{FILEDIR}/images/zoffany/{fname}")
                except Zoffany.DoesNotExist:
                    continue

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/zoffany-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))
        for row in cr:
            if row[0] == "Supplier ID":
                continue

            mpn = common.formatText(row[1]).replace("/UC", "")
            sku = f"ZOF {mpn}"
            stockP = common.formatInt(row[2])
            stockNote = common.formatText(row[5])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
