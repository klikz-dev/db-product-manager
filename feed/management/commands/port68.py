from django.core.management.base import BaseCommand
from feed.models import Port68

import os
import environ
import pymysql
import xlrd
import time
import datetime

from library import database, debug, common

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


BRAND = "Port 68"


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
            products = Port68.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=False)

        if "image" in options['functions']:
            processor.databaseManager.downloadImages(missingOnly=True)

        if "sample" in options['functions']:
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "shipping" in options['functions']:
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove")

        if "inventory" in options['functions']:
            while True:
                try:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/port68", dst=f"{FILEDIR}/port-68-inventory.xlsx", fileSrc=False)
                    processor.inventory()

                    print("Finished process. Waiting for next run. {}:{}".format(
                        BRAND, options['functions']))
                    time.sleep(86400)

                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    print("Failed process. Waiting for next run. {}:{}".format(
                        BRAND, options['functions']))
                    time.sleep(3600)


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Port68)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/port-68-master.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 2))
                sku = f"P68 {mpn}"

                pattern = common.formatText(sh.cell_value(i, 3))
                color = common.formatText(sh.cell_value(i, 4))
                if not pattern or not color:
                    debug.debug(
                        BRAND, 1, f"Missing primary attribute MPN: {mpn}")
                    continue

                upc = common.formatText(sh.cell_value(i, 13))

                # Categorization
                collection = common.formatText(sh.cell_value(i, 1))

                if collection == "Scalamandre":
                    manufacturer = "Scalamandre Maison"
                elif collection == "Madcap Cottage":
                    manufacturer = "Madcap Cottage Décor"
                else:
                    debug.debug(BRAND, 1, f"Unknown manufacturer {collection}")

                type = common.formatText(sh.cell_value(i, 5))

                if type == "Jar":
                    type = "Ginger Jar"
                elif type == "Planter":
                    type = "Planters"
                elif type == "Vase":
                    type = "Vases"
                elif type == "Tray":
                    type = "Trays"
                elif type == "Stool":
                    type = "Stools"
                elif type == "Table Lamp":
                    type = "Table Lamps"
                elif type == "Floor Lamp":
                    type = "Floor Lamps"
                elif type == "Bench":
                    type = "Benches"
                elif type == "Accent Table":
                    type = "Accent Tables"
                elif type == "Bowl":
                    type = "Bowls"
                elif type == "Lamp":
                    type = "Accent Lamps"
                elif type == "Chandelier":
                    type = "Chandeliers"

                # Main Information
                description = common.formatText(sh.cell_value(i, 19))
                size = common.formatText(sh.cell_value(
                    i, 18)).replace("Size:", "").strip()

                # Additional Information
                material = common.formatText(sh.cell_value(i, 12))
                care = common.formatText(sh.cell_value(i, 25))
                features = [common.formatText(sh.cell_value(i, 20))]
                country = common.formatText(sh.cell_value(i, 35))
                weight = common.formatFloat(sh.cell_value(i, 14))

                # Measurement
                uom = "Per Item"

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 7))
                map = common.formatFloat(sh.cell_value(i, 8))
                msrp = common.formatFloat(sh.cell_value(i, 9))

                # Tagging
                tags = f"{sh.cell_value(i, 11)}, {type}, {description}, {sh.cell_value(i, 20)}"
                colors = color

                # Image
                thumbnail = sh.cell_value(i, 51)

                roomsets = []
                for id in range(52, 65):
                    if sh.cell_value(i, id) != "":
                        roomsets.append(sh.cell_value(i, id))

                # Status
                statusP = True
                statusS = False

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,
                'upc': upc,

                'brand': BRAND,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'size': size,

                'features': features,
                'material': material,
                'care': care,
                'country': country,
                'weight': weight,

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

    def inventory(self):
        stocks = []

        wb = xlrd.open_workbook(f"{FILEDIR}/port-68-inventory.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            mpn = common.formatText(sh.cell_value(i, 0))
            sku = f"P68 {mpn}"

            stockP = common.formatInt(sh.cell_value(i, 2))

            stockNote = sh.cell_value(i, 3)
            if stockNote:
                date_tuple = xlrd.xldate_as_tuple(stockNote, wb.datemode)
                date_obj = datetime.datetime(*date_tuple)
                stockNote = date_obj.date()

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
