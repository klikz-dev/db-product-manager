from django.core.management.base import BaseCommand
from feed.models import Surya
from django.db.models import Q

import os
import environ
import pymysql
import xlrd
import csv
import codecs
import time

from library import database, debug, common

formatText = common.formatText
formatInt = common.formatInt
formatFloat = common.formatFloat

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Surya"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products)

        if "validate" in options['functions']:
            processor.databaseManager.validateFeed()

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=False)

        if "update" in options['functions']:
            products = Surya.objects.filter(sku="SR AML2323-710102")
            processor.databaseManager.updateProducts(
                products=products, formatPrice=False)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=False)

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
            if True:
                try:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/surya/inventory_dbest.csv", dst=f"{FILEDIR}/surya-inventory.csv")
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
            con=self.con, brand=BRAND, Feed=Surya)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(FILEDIR + 'surya-master.xlsx')
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = formatText(sh.cell_value(i, 1))
                debug.debug(BRAND, 0, "Fetching Product MPN: {}".format(mpn))

                sku = f"SR {mpn}"
                pattern = formatText(sh.cell_value(i, 4))
                color = formatText(sh.cell_value(i, 2))

                # Categorization
                brand = BRAND

                typeText = formatText(sh.cell_value(i, 0)).title()
                if typeText == "Bedding":
                    type = "Furniture"
                elif typeText == "Accent And Lounge Chairs":
                    type = "Accents"
                elif typeText == "Ceiling Lighting":
                    type = "Lighting"
                elif typeText == "Rugs":
                    type = "Rug"
                elif typeText == "Wall Art - Stock":
                    type = "Wall Art"
                else:
                    type = typeText

                manufacturer = BRAND
                collection = formatText(sh.cell_value(i, 4))

                # Main Information
                description = formatText(sh.cell_value(i, 3))
                usage = typeText
                width = formatFloat(sh.cell_value(i, 16))
                height = formatFloat(sh.cell_value(i, 17))
                depth = formatFloat(sh.cell_value(i, 15))

                if height == 0 and depth != 0:
                    height = depth
                    depth = 0

                if "D" in sh.cell_value(i, 13):
                    size = ""
                    dimension = formatText(sh.cell_value(i, 13))
                else:
                    size = formatText(sh.cell_value(i, 13))
                    dimension = ""

                # Additional Information
                material = formatText(sh.cell_value(i, 10))
                weight = formatFloat(sh.cell_value(i, 18)) or 5
                specs = [
                    ("Color", formatText(sh.cell_value(i, 9))),
                    ("Construction", formatText(sh.cell_value(i, 21))),
                ]
                upc = formatInt(sh.cell_value(i, 5))

                # Measurement
                uom = "Per Item"

                # Pricing
                cost = formatFloat(sh.cell_value(i, 6))
                map = formatFloat(sh.cell_value(i, 7))
                msrp = formatFloat(sh.cell_value(i, 8))

                if cost == 0:
                    debug.debug(BRAND, 1, "Produt Cost error {}".format(mpn))
                    continue

                # Tagging
                tags = f"{formatText(sh.cell_value(i, 11))}, {formatText(sh.cell_value(i, 12))}"
                if formatText(sh.cell_value(i, 23)) == "Yes":
                    tags = "{}, Outdoor".format(tags)
                tags = f"{tags}, {type}, {collection}, {pattern}"

                colors = formatText(sh.cell_value(i, 9))

                # Status
                statusP = True
                statusS = False

                whiteGlove = False
                if "white glove" in str(sh.cell_value(i, 17)).lower() or "ltl" in str(sh.cell_value(i, 17)).lower():
                    whiteGlove = True

                # Image
                thumbnail = sh.cell_value(i, 25)

                roomsets = []
                for id in range(26, 31):
                    if sh.cell_value(i, id) != "":
                        roomsets.append(sh.cell_value(i, id))

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'upc': upc,
                'pattern': pattern,
                'color': color,

                'brand': brand,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'description': description,
                'usage': usage,
                'width': width,
                'height': height,
                'depth': depth,
                'weight': weight,
                'size': size,
                'dimension': dimension,

                'material': material,
                'specs': specs,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'statusP': statusP,
                'statusS': statusS,
                'whiteGlove': whiteGlove,

                'thumbnail': thumbnail,
                'roomsets': roomsets,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/surya-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "Sku":
                continue

            sku = f"SR {formatText(row[0])}"
            stockP = formatInt(row[1])
            stockNote = formatText(row[2])

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': stockNote,
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
