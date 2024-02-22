from django.core.management.base import BaseCommand
from feed.models import Kravet
from django.db.models import Q

import os
import environ
import pymysql
import csv
import codecs
import zipfile
import xlrd
import time
from shutil import copyfile
import glob

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Kravet"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "feed" in options['functions']:
            processor = Processor()
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products)

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
            products = Kravet.objects.filter(
                Q(manufacturer="Cole & Son Wallpaper") |
                Q(manufacturer="Winfield Thybony Wallpaper")
            )
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
            processor.image()

        if "manual-image" in options['functions']:
            processor = Processor()
            processor.manual_image()

        if "hires" in options['functions']:
            processor = Processor()
            processor.hires()

        if "manual-hires" in options['functions']:
            processor = Processor()
            processor.manual_hires()

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.downloadInventory()
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
            con=self.con, brand=BRAND, Feed=Kravet)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def downloadInventory(self):
        try:
            self.databaseManager.downloadFileFromFTP(
                src="decbest.zip", dst=f"{FILEDIR}/kravet-master.zip")
            z = zipfile.ZipFile(f"{FILEDIR}/kravet-master.zip", "r")
            z.extractall(FILEDIR)
            z.close()
            os.rename(f"{FILEDIR}/item_info.csv",
                      f"{FILEDIR}/kravet-master.csv")

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

        # Get Product Feed
        products = []

        # Wallpaper, Fabric, and Trim
        f = open(f"{FILEDIR}/kravet-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            # Primary Keys
            mpn = common.formatText(row[0])
            keys = mpn.split(".")
            if len(keys) != 3 or keys[2] != "0":
                continue

            manufacturer = common.formatText(row[3])
            collection = common.formatText(row[16])

            european = False
            if "LIZZO" in collection:
                manufacturer = "LIZZO"
                european = True
            elif "ANDREW MARTIN" in collection:
                manufacturer = "ANDREW MARTIN"
                european = True
            elif "BLITHFIELD" in collection or "JAGTAR" in collection or "JOSEPHINE MUNSEY" in collection or "MISSONI HOME" in collection or "PAOLO MOSCHINO" in collection:
                european = True

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
                "CLARKE AND CLARKE": ("Clarke & Clarke", "CC"),
                "LIZZO": ("Lizzo", "LI"),
                "ANDREW MARTIN": ("Andrew Martin", "AM"),
                "DONGHIA": ("Donghia", "K"),
            }

            if manufacturer in manufacturer_mapping:
                manufacturer, code_prefix = manufacturer_mapping[manufacturer]

                if manufacturer == "Cole & Son" or manufacturer == "Winfield Thybony" or manufacturer == "Clarke & Clarke":
                    sku = f"{code_prefix} {keys[0]}"
                else:
                    sku = f"{code_prefix} {keys[0]}-{keys[1]}" if code_prefix else f"{keys[0]}-{keys[1]}"

            else:
                debug.debug(
                    BRAND, 1, f"Brand Error for MPN: {mpn}, Brand: {manufacturer}")
                continue

            sku = sku.replace("'", "")

            pattern = common.formatText(row[1])
            if pattern == "." or pattern == ".." or pattern == "..." or pattern == "" or pattern.find("KF ") >= 0 or "KRAVET " in pattern:
                pattern = keys[0]

            color = common.formatText(row[2])
            if color == "." or color == "" or color == "NONE" or "KRAVET" in pattern:
                color = keys[1]

            if pattern == "" or color == "":
                continue

            # Categorization
            brand = BRAND

            type = common.formatText(row[17])
            type_mapping = {
                "WALLCOVERING": "Wallpaper",
                "TRIM": "Trim",
                "UPHOLSTERY": "Fabric",
                "DRAPERY": "Fabric",
                "MULTIPURPOSE": "Fabric"
            }
            type = type_mapping.get(type, type)

            manufacturer = f"{manufacturer} {type}"

            # Main Information
            usage = common.formatText(row[17])
            width = common.formatFloat(row[7])
            repeatV = common.formatFloat(row[4])
            repeatH = common.formatFloat(row[5])

            # Additional Information
            content = common.formatText(row[12])
            yards = common.formatFloat(row[37])

            # Measurement
            uom = common.formatText(row[11]).title()
            uom_mapping = {
                "Each": "Item",
                "Foot": "Square Foot",
            }
            uom = uom_mapping.get(uom, uom)
            uom = f"Per {uom}"

            if uom == "Per Hide":
                continue

            minimum = common.formatInt(row[38])

            increment = common.formatInt(row[39])
            if increment > 1:
                increment = ",".join(str(increment * ii)
                                     for ii in range(1, 21))
            else:
                increment = ""

            # Pricing
            cost = common.formatFloat(row[10])
            map = common.formatFloat(row[49])

            # Tagging
            tags = f"{row[20]}, {row[21]}"
            colors = f"{row[26]}, {row[27]}, {row[28]}"

            # Image
            thumbnail = common.formatText(row[24] or row[25])
            if mpn in images and not thumbnail:
                thumbnail = images[mpn]

            # Status
            statusP = True
            statusS = True
            outlet = False

            blockCollections = [
                "CANDICE OLSON AFTER EIGHT",
                "CANDICE OLSON COLLECTION",
                "CANDICE OLSON MODERN NATURE 2ND EDITION",
                "RONALD REDDING",
                "RONALD REDDING ARTS & CRAFTS",
                "RONALD REDDING TRAVELER",
                "DAMASK RESOURCE LIBRARY",
                "MISSONI HOME",
                "MISSONI HOME 2020",
                "MISSONI HOME 2021",
                "MISSONI HOME 2022 INDOOR/OUTDOOR",
                "MISSONI HOME WALLCOVERINGS 03",
                "MISSONI HOME WALLCOVERINGS 04",
            ]
            if collection in blockCollections and type == "Wallpaper":
                statusP = False

            if row[43].strip() != "YES":
                statusS = False

            if row[31] == "Outlet":
                outlet = True

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
                'european': european,
                'outlet': outlet,

                'thumbnail': thumbnail,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        f = open(f"{FILEDIR}/kravet-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            try:
                mpn = common.formatText(row[0])
                product = Kravet.objects.get(mpn=mpn)
            except Kravet.DoesNotExist:
                continue

            stockP = common.formatInt(row[46])
            stockNote = f"{common.formatText(row[47])} days"

            stock = {
                'sku': product.sku,
                'quantity': stockP,
                'note': stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)

    def image(self):
        csr = self.con.cursor()

        hasImage = []

        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = '{}'".format(BRAND))
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        csr.close()

        products = Kravet.objects.all()
        for product in products:
            if not product.productId or not product.thumbnail:
                continue

            if product.productId not in hasImage:
                if "http" in product.thumbnail:
                    self.databaseManager.downloadImage(product.productId,
                                                       product.thumbnail, product.roomsets)
                else:
                    self.databaseManager.downloadFileFromFTP(
                        src=product.thumbnail, dst=f"{FILEDIR}/../../../images/product/{product.productId}.jpg")

    def manual_image(self):
        for infile in glob.glob(f"{FILEDIR}/images/kravet/*.*"):
            fpath, ext = os.path.splitext(infile)
            fname = os.path.basename(fpath)

            mpn = f"{fname.replace('_', '.')}.0"

            try:
                product = Kravet.objects.get(mpn=mpn)
            except Kravet.DoesNotExist:
                continue

            if product.productId:
                copyfile(f"{FILEDIR}/images/kravet/{fname}{ext}",
                         f"{FILEDIR}/../../../images/product/{product.productId}{ext}")
                debug.debug(
                    BRAND, 0, f"Copied {fname}{ext} to {product.productId}{ext}")

            os.remove(
                f"{FILEDIR}/images/kravet/{fname}{ext}")

    def hires(self):
        csr = self.con.cursor()

        hasHiresImage = []

        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 20 AND M.Brand = '{}'".format(BRAND))
        for row in csr.fetchall():
            hasHiresImage.append(str(row[0]))

        csr.close()

        products = Kravet.objects.all()
        for product in products:
            if not product.productId or not product.thumbnail:
                continue

            if product.productId not in hasHiresImage:
                if "http" not in product.thumbnail and "HIRES" in product.thumbnail:
                    self.databaseManager.downloadFileFromFTP(
                        src=product.thumbnail, dst=f"{FILEDIR}/../../../images/hires/{product.productId}_20.jpg")

    def manual_hires(self):
        for infile in glob.glob(f"{FILEDIR}/images/kravet/*.*"):
            fpath, ext = os.path.splitext(infile)
            fname = os.path.basename(fpath)

            mpn = f"{fname.replace('_', '.')}.0"

            try:
                product = Kravet.objects.get(mpn=mpn)
            except Kravet.DoesNotExist:
                continue

            if product.productId:
                copyfile(f"{FILEDIR}/images/kravet/{fname}{ext}",
                         f"{FILEDIR}/../../../images/hires/{product.productId}_20{ext}")
                debug.debug(
                    BRAND, 0, f"Copied {fname}{ext} to {product.productId}_20{ext}")

            os.remove(
                f"{FILEDIR}/images/kravet/{fname}{ext}")
