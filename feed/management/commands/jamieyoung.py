from django.core.management.base import BaseCommand
from feed.models import JamieYoung

import os
import environ
import pymysql
import xlrd
import csv
import codecs
import time
from shutil import copyfile

from library import database, debug, common

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Jamie Young"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor = Processor()
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor = Processor()
            processor.databaseManager.createProducts(formatPrice=False)

        if "update" in options['functions']:
            processor = Processor()
            products = JamieYoung.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=False)

        if "price" in options['functions']:
            processor = Processor()
            processor.databaseManager.updatePrices(formatPrice=False)

        if "image" in options['functions']:
            processor = Processor()
            processor.databaseManager.downloadImages(missingOnly=False)

        if "hires" in options['functions']:
            processor = Processor()
            processor.hires()

        if "tag" in options['functions']:
            processor = Processor()
            processor.databaseManager.updateTags(category=False)

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "whiteglove" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove")

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="jamieyoung", dst=f"{FILEDIR}/jamieyoung-inventory.csv", fileSrc=False)
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
            con=self.con, brand=BRAND, Feed=JamieYoung)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Discontinued
        discontinued_mpns = []
        wb = xlrd.open_workbook(f"{FILEDIR}/jamieyoung-discontinued.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            discontinued_mpns.append(str(sh.cell_value(i, 0)).strip())

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/jamieyoung-master.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(2, sh.nrows):
            try:
                # Primary Keys
                mpn = str(sh.cell_value(i, 0)).strip()
                if mpn in discontinued_mpns:
                    debug.debug(BRAND, 1, f"Item discontinued: {mpn}")
                    continue

                sku = f"JY {mpn}"
                try:
                    upc = int(sh.cell_value(i, 8))
                except:
                    upc = ""
                pattern = str(sh.cell_value(i, 1)).strip()
                if "Sideboard" in pattern or "Console" in pattern:
                    # we won't sell large peices for Jamie Young. 1/25/23 from BK.
                    continue
                color = str(sh.cell_value(i, 21)).strip().replace(",", " /")

                # Categorization
                brand = BRAND
                type = str(sh.cell_value(i, 3)).strip().title()
                if type == "Accessories":
                    type = "Accents"
                manufacturer = BRAND
                collection = str(sh.cell_value(i, 2))

                # Main Information
                description = str(sh.cell_value(i, 14)).strip()
                disclaimer = str(sh.cell_value(i, 22)).strip()
                width = common.formatFloat(sh.cell_value(i, 11))
                height = common.formatFloat(sh.cell_value(i, 10))
                depth = common.formatFloat(sh.cell_value(i, 12))

                # Additional Information
                material = str(sh.cell_value(i, 20)).strip()
                care = str(sh.cell_value(i, 23)).strip()
                country = str(sh.cell_value(i, 33)).strip()
                try:
                    weight = float(sh.cell_value(i, 9))
                except:
                    weight = 5
                features = []
                for id in range(15, 19):
                    feature = str(sh.cell_value(i, id)).strip()
                    if feature != "":
                        features.append(feature)
                specs = []
                for id in range(24, 32):
                    spec = str(sh.cell_value(i, id)).strip()
                    if spec != "":
                        specs.append(spec)

                # Measurement
                uom = "Per Item"

                # Pricing
                try:
                    cost = round(float(sh.cell_value(i, 4)), 2)
                except:
                    debug.debug(BRAND, 1, "Produt Cost error {}".format(mpn))
                    continue

                try:
                    map = round(float(sh.cell_value(i, 5)), 2)
                except:
                    debug.debug(BRAND, 1, "Produt MAP error {}".format(mpn))
                    continue

                try:
                    msrp = round(float(sh.cell_value(i, 6)), 2)
                except:
                    debug.debug(BRAND, 1, "Produt MSRP error {}".format(mpn))
                    msrp = 0

                # Tagging
                tags = "{}, {}, {}, {}".format(str(sh.cell_value(i, 19)).strip(
                ), ", ".join(features), collection, description)
                colors = color

                statusP = True
                statusS = False
                stockNote = "3 days"
                shipping = str(sh.cell_value(i, 35)).strip()

                # Image
                thumbnail = str(sh.cell_value(
                    i, 49)).strip().replace("dl=0", "dl=1")
                roomsets = []
                for id in range(50, 63):
                    roomset = str(sh.cell_value(i, id)
                                  ).strip().replace("dl=0", "dl=1")
                    if roomset != "":
                        roomsets.append(roomset)

                # Pattern Name
                ptypeTmp = type
                if ptypeTmp[len(ptypeTmp) - 1] == "s":
                    ptypeTmp = ptypeTmp[:-1]

                for typeword in ptypeTmp.split(" "):
                    pattern = pattern.replace(typeword, "")

                pattern = pattern.replace(
                    "**MUST SHIP COMMON CARRIER**", "").replace("  ", " ").strip()
                ##############

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
                'disclaimer': disclaimer,
                'width': width,
                'height': height,
                'depth': depth,
                'weight': weight,

                'material': material,
                'care': care,
                'country': country,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'statusP': statusP,
                'statusS': statusS,
                'stockNote': stockNote,
                'shipping': shipping,

                'thumbnail': thumbnail,
                'roomsets': roomsets,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/jamieyoung-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, 'utf-8'))
        for row in cr:
            try:
                mpn = row[1]
                quantity = int(row[2])

                product = JamieYoung.objects.get(mpn=mpn)
            except JamieYoung.DoesNotExist:
                continue
            except Exception as e:
                print(str(e))
                continue

            stock = {
                'sku': product.sku,
                'quantity': quantity,
                'note': product.stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)

    def hires(self):
        images = os.listdir(f"{FILEDIR}/images/jamie-young")

        for image in images:
            mpn = image.split(".")[0]

            try:
                product = JamieYoung.objects.get(mpn=mpn)
                if not product.productId:
                    continue

            except JamieYoung.DoesNotExist:
                continue

            copyfile(f"{FILEDIR}/images/jamie-young/{image}",
                     f"{FILEDIR}/../../../images/hires/{product.productId}_20.png")

            debug.debug(
                BRAND, 0, f"Copied {image} to {product.productId}_20.png")

            os.remove(f"{FILEDIR}/images/jamie-young/{image}")
