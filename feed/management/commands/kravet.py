from django.core.management.base import BaseCommand
from feed.models import Kravet

import os
import environ
import pymysql
import csv
import codecs
import urllib
import zipfile
import requests
import xlrd
import time
from bs4 import BeautifulSoup
from shutil import copyfile

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Kravet"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            processor.downloadFeed()

            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products)

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            products = Kravet.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "image" in options['functions']:
            processor.databaseManager.downloadImages(missingOnly=True)

        if "image-manual" in options['functions']:
            processor.image()

        if "sample" in options['functions']:
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)

        if "shipping" in options['functions']:
            processor.databaseManager.customTags(
                key="whiteGlove", tag="White Glove")

        if "inventory" in options['functions']:
            while True:
                processor.downloadFeed()

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
            con=self.con, brand=BRAND, Feed=Kravet)

    def __del__(self):
        self.con.close()

    def downloadFeed(self):
        try:
            self.databaseManager.downloadFileFromFTP(
                src="decbest.zip", dst=f"{FILEDIR}/kravet-master.zip")
            z = zipfile.ZipFile(f"{FILEDIR}/kravet-master.zip", "r")
            z.extractall(FILEDIR)
            z.close()
            os.rename(f"{FILEDIR}/item_info.csv",
                      f"{FILEDIR}/kravet-master.csv")

            self.databaseManager.downloadFileFromFTP(
                src="curated_onhand_info.zip", dst=f"{FILEDIR}/kravet-decor-inventory.zip")
            z = zipfile.ZipFile(f"{FILEDIR}/kravet-decor-inventory.zip", "r")
            z.extractall(FILEDIR)
            z.close()
            os.rename(f"{FILEDIR}/curated_onhand_info.csv",
                      f"{FILEDIR}/kravet-decor-inventory.csv")

            debug.debug(BRAND, 0, "Download Completed")
            return True
        except Exception as e:
            debug.debug(BRAND, 1, f"Download Failed. {str(e)}")
            return False

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Images
        images = {}

        wb = xlrd.open_workbook(f"{FILEDIR}/kravet-images.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            images[str(sh.cell_value(i, 0))] = str(sh.cell_value(i, 1))

        # Prices
        prices = {}

        wb = xlrd.open_workbook(f"{FILEDIR}/kravet-prices.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            prices[str(sh.cell_value(i, 0))] = round(
                float(sh.cell_value(i, 1)), 2)

        # Pillow Stock
        inventories = {}

        f = open(f"{FILEDIR}/kravet-decor-inventory.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            if row[0] == "Item":
                continue
            try:
                inventories[str(row[0]).strip()] = (
                    int(float(row[1])), int(float(row[2])), str(row[3]).strip())
            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

        # Get Product Feed
        products = []

        # Wallpaper, Fabric, and Trim
        f = open(f"{FILEDIR}/kravet-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            try:
                # Primary Keys
                mpn = row[0].strip()
                keys = mpn.split(".")
                if len(keys) != 3 or keys[2] != "0":
                    continue

                manufacturer_mapping = {
                    "LEE JOFA": ("Lee Jofa", "LJ"),
                    "LEE JOFA MODERN": ("Lee Jofa", "LJ"),
                    "FIRED EARTH": ("Lee Jofa", "LJ"),
                    "MONKWELL": ("Lee Jofa", "LJ"),
                    "PARKERTEX": ("Lee Jofa", "LJ"),
                    "SEACLOTH": ("Lee Jofa", "LJ"),
                    "WARNER LONDON": ("Lee Jofa", "LJ"),
                    "KRAVET SMART": ("Kravet", "K"),
                    "KRAVET DESIGN": ("Kravet", "K"),
                    "KRAVET BASICS": ("Kravet", "K"),
                    "KRAVET COUTURE": ("Kravet", "K"),
                    "KRAVET CONTRACT": ("Kravet", "K"),
                    "BAKER LIFESTYLE": ("Baker Lifestyle", ""),
                    "MULBERRY": ("Mulberry", ""),
                    "G P & J BAKER": ("G P & J Baker", "GPJ"),
                    "COLE & SON": ("Cole & Son", "CS"),
                    "GROUNDWORKS": ("Groundworks", "GW"),
                    "THREADS": ("Threads", ""),
                    "AVONDALE": ("Avondale", "AV"),
                    "LAURA ASHLEY": ("Laura Ashley", "LA"),
                    "BRUNSCHWIG & FILS": ("Brunschwig & Fils", "BF"),
                    "GASTON Y DANIELA": ("Gaston Y Daniela", "GD"),
                    "WINFIELD THYBONY": ("Winfield Thybony", "WF"),
                    "CLARKE AND CLARKE": ("Clarke & Clarke", "CC")
                }

                manufacturer = row[3]
                if manufacturer in manufacturer_mapping:
                    manufacturer, code_prefix = manufacturer_mapping[manufacturer]
                    sku = f"{code_prefix} {keys[0]}-{keys[1]}" if code_prefix else f"{keys[0]}-{keys[1]}"
                    if manufacturer == "Winfield Thybony":
                        r = requests.get(
                            f"http://www.winfieldthybony.com/home/products/details?sku={sku.replace('WF ', '')}")
                        soup = BeautifulSoup(r.content, "lxml")
                        try:
                            collection = soup.find(
                                "span", id="ctl00_mainContent_C001_collectionName").string
                        except:
                            pass
                        try:
                            picLoc = soup.find(
                                "a", id="ctl00_mainContent_C001_downloadRoomShotImageUrl2")["href"]
                        except:
                            pass
                else:
                    debug.debug(
                        BRAND, 1, f"Brand Error for MPN: {mpn}, Brand: {manufacturer}")
                    continue

                sku = sku.replace("'", "")

                pattern = row[1]
                if pattern == "." or pattern == ".." or pattern == "..." or pattern == "" or pattern.find("KF ") >= 0 or "KRAVET " in pattern:
                    pattern = keys[0]

                color = row[2]
                if color == "." or color == "" or color == "NONE" or "KRAVET " in pattern:
                    color = keys[1]

                if pattern == "" or color == "":
                    continue

                # Categorization
                brand = BRAND

                type_mapping = {
                    "WALLCOVERING": "Wallpaper",
                    "TRIM": "Trim",
                    "UPHOLSTERY": "Fabric",
                    "DRAPERY": "Fabric",
                    "MULTIPURPOSE": "Fabric"
                }

                type = type_mapping.get(row[17])
                if type is None:
                    debug.debug(BRAND, 1, f"Unknown product type {row[17]}")

                manufacturer = f"{manufacturer} {type}"

                collection = row[16]

                # Main Information
                usage = row[17]
                try:
                    width = float(row[7])
                except:
                    width = 0

                # Additional Information
                try:
                    repeatV = float(row[4])
                except:
                    repeatV = 0

                try:
                    repeatH = float(row[5])
                except:
                    repeatH = 0

                content = row[12]
                if content == "LEATHER - 100%":
                    continue

                try:
                    yards = float(row[37])
                except:
                    yards = 0

                # Measurement
                uom_mapping = {
                    "ROLL": "Roll",
                    "YARD": "Yard",
                    "EACH": "Item",
                    "FOOT": "Square Foot",
                    "SQUARE FOOT": "Square Foot",
                    "PANEL": "Panel"
                }

                if row[11] in uom_mapping:
                    uom = "Per " + uom_mapping[row[11]]
                else:
                    debug.debug(
                        BRAND, 1, f"UOM Error for MPN: {mpn}, UOM: {row[11]}")
                    continue

                minimum = int(float(row[38])) if row[38] else 1

                if row[39] and int(float(row[39])) > 1:
                    increment = ",".join(
                        str(int(float(row[39])) * ii) for ii in range(1, 21))
                else:
                    increment = ""

                # Pricing
                try:
                    cost = float(row[10] or row[32])
                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    continue

                try:
                    map = float(row[49])
                except Exception as e:
                    debug.debug(BRAND, 1, str(e))
                    continue

                if mpn in prices:
                    cost = prices[mpn]

                # Tagging
                tags = ",".join((row[20], row[21]))
                if "CLARKE & CLARKE BOTANICAL WONDERS" in collection:
                    tags = f"{tags}, Floral"

                colors = ",".join((row[26], row[27], row[28]))

                # Image
                thumbnail = str(row[24] or row[25]).strip()
                if mpn in images:
                    thumbnail = images[mpn]

                # Status
                statusP = True
                statusS = True
                outlet = False

                if str(row[22]).strip() != 'Y':
                    statusP = False

                if row[43].strip() != "YES":
                    statusS = False

                if row[31] == "Outlet":
                    outlet = True

                # Stock
                stockP = int(float(row[46]))
                stockS = int(float(row[50]))
                stockNote = f"{str(row[47]).strip()} days"

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

                'usage': usage,
                'width': width,
                'content': content,
                'repeatH': repeatH,
                'repeatV': repeatV,
                'yards': yards,

                'uom': uom,
                'minimum': minimum,
                'increment': increment,

                'tags': tags,
                'colors': colors,

                'cost': cost,
                'map': map,

                'statusP': statusP,
                'statusS': statusS,
                'outlet': outlet,

                'stockP': stockP,
                'stockS': stockS,
                'stockNote': stockNote,

                'thumbnail': thumbnail,
            }
            products.append(product)

        # Pillow
        wb = xlrd.open_workbook(f"{FILEDIR}/kravet-pillows.xlsx")
        sh = wb.sheet_by_index(1)
        for i in range(2, sh.nrows):
            try:
                # Primary Keys
                mpn = str(sh.cell_value(i, 0)).strip()
                if len(mpn.split(".")) != 3 or mpn.split(".")[2] != "0":
                    continue

                sku = "K {}".format(mpn)

                pattern = str(sh.cell_value(i, 1)).replace(
                    "Pillow", "").strip()
                color = mpn.split(".")[1]

                # Categorization
                brand = BRAND
                type = "Pillow"
                manufacturer = f"{brand} {type}"
                collection = "Decorative Pillows"

                # Main Information
                description = str(sh.cell_value(i, 2))
                usage = "Accessory"

                width = common.formatFloat(sh.cell_value(i, 9))
                height = common.formatFloat(sh.cell_value(i, 11))

                if width != 0 and height != 0:
                    size = f'{int(width)}" x {int(height)}"'
                else:
                    size = ""

                # Additional Information
                content = str(sh.cell_value(i, 19))
                country = str(sh.cell_value(i, 20))
                care = str(sh.cell_value(i, 23))

                # Measurement
                uom = "Per Item"

                # Pricing
                try:
                    cost = round(float(sh.cell_value(i, 14)), 2)
                except:
                    debug.debug(BRAND, 1, f"Pillow price error {mpn}")
                    continue

                if mpn in prices:
                    cost = prices[mpn]

                # Tagging
                tags = str(sh.cell_value(i, 5))

                colors = str(sh.cell_value(i, 7)).replace(";", "/")
                colors = f"{color} {str(sh.cell_value(i, 7))}"

                # Image
                thumbnail = str(sh.cell_value(i, 34))
                roomsets = [str(sh.cell_value(i, 35))]

                if mpn in images:
                    thumbnail = images[mpn]

                # Status
                statusP = True
                statusS = True
                if str(sh.cell_value(i, 4)) != "Active":
                    statusP = False

                # Stock
                stockP = 0
                stockNote = str(sh.cell_value(i, 17))
                whiteGlove = False

                if mpn in inventories:
                    (stockP, leadtime, shipping) = inventories[mpn]
                    stockNote = f"{leadtime} days"
                    if "White" in shipping:
                        whiteGlove = True

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
                'height': height,
                'size': size,

                'content': content,
                'country': country,
                'care': care,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'cost': cost,

                'statusP': statusP,
                'statusS': statusS,

                'stockP': stockP,
                'stockNote': stockNote,
                'whiteGlove': whiteGlove,

                'thumbnail': thumbnail,
                'roomsets': roomsets,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        products = Kravet.objects.all()
        for product in products:
            stock = {
                'sku': product.sku,
                'quantity': product.stockP,
                'note': product.stockNote or ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)

    def image(self):
        fnames = os.listdir(f"{FILEDIR}/images/kravet/")
        for fname in fnames:
            mpn = f"{fname.replace('_', '.').replace('.jpg', '').replace('.png', '')}.0".upper(
            )

            print(mpn)

            try:
                product = Kravet.objects.get(mpn=mpn)
            except Kravet.DoesNotExist:
                continue

            print(product.sku)

            productId = product.productId

            if productId:
                debug.debug(
                    BRAND, 0, f"Copying {FILEDIR}/images/kravet/{fname} to {productId}.jpg")
                copyfile(f"{FILEDIR}/images/kravet/{fname}",
                         f"{FILEDIR}/../../../images/product/{productId}.jpg")
