from django.core.management.base import BaseCommand
from feed.models import MindTheGap

import os
import environ
import pymysql
import xlrd
import time
from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "MindTheGap"


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
            products = MindTheGap.objects.all()
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

        if "outlet" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="outlet", tag="Outlet", logic=True)

        if "image" in options['functions']:
            processor = Processor()
            processor.image()

        if "hires" in options['functions']:
            processor = Processor()
            processor.hires()

        if "inventory" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/mindthegap/Inventory/MINDTHEGAP STOCK cushions.xlsx", dst=f"{FILEDIR}/mindthegap-pillow-inventory.xlsx", fileSrc=True, delete=False)
                    processor.databaseManager.downloadFileFromSFTP(
                        src="/mindthegap/Inventory/MINDTHEGAP STOCK fabrics.xlsx", dst=f"{FILEDIR}/mindthegap-fabric-inventory.xlsx", fileSrc=True, delete=False)

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
            con=self.con, brand=BRAND, Feed=MindTheGap)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Outlet
        outletMPNs = [
            "LC40080",
            "LC40081",
            "LC40082",
            "LC40083",
            "LC40084",
            "LC40085",
            "LC40086",
            "LC40087",
            "LC40088",
            "LC40089",
            "LC40090",
            "LC40091",
            "LC40092",
            "LC40093",
            "LC40094",
            "LC40095",
            "LC40096",
            "LC40097",
            "LC40098",
            "LC40099",
            "LC40100",
            "LC40102",
            "AC00020",
            "AC00021",
            "AC00022",
            "LC40103",
            "LC40104",
            "LC40105",
            "LC40106",
            "LC40107",
            "AC00023",
            "AC00024"
        ]

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/mindthegap-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 2))
                sku = f"MTG {mpn}"

                pattern = common.formatText(sh.cell_value(i, 3))
                color = common.formatText(sh.cell_value(i, 4))

                # Categorization
                brand = BRAND

                type = common.formatText(sh.cell_value(i, 0)).lower()
                if "wallpaper" in type:
                    type = "Wallpaper"
                elif "fabric" in type:
                    type = "Fabric"
                elif "pillow" in type:
                    type = "Pillow"
                else:
                    debug.debug(BRAND, 1, f"Unknow Type {type}")
                    continue

                manufacturer = f"{brand} {type}"

                collection = common.formatText(sh.cell_value(i, 1))

                # Main Information
                description = common.formatText(sh.cell_value(i, 12))
                if sh.cell_value(i, 11):
                    description = f"{description} {common.formatText(sh.cell_value(i, 11))}"

                size = f"{common.formatText(sh.cell_value(i, 6))} cm / {common.formatText(sh.cell_value(i, 7)).replace(',', '.')}"

                repeat = common.formatText(sh.cell_value(i, 18))

                # Additional Information
                usage = common.formatText(sh.cell_value(i, 0))
                if sh.cell_value(i, 17):
                    usage = common.formatText(sh.cell_value(i, 17))

                material = common.formatText(sh.cell_value(i, 14))
                finish = common.formatText(sh.cell_value(i, 15))
                care = common.formatText(sh.cell_value(i, 20))
                country = common.formatText(sh.cell_value(i, 19))
                weight = common.formatFloat(sh.cell_value(i, 22)) * 2.2
                upc = common.formatInt(sh.cell_value(i, 23))

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 10))

                # Measurement
                if type == "Wallpaper":
                    uom = "Per Roll"
                elif type == "Fabric":
                    uom = "Per Yard"
                elif type == "Pillow":
                    uom = "Per Item"
                else:
                    debug.debug(BRAND, 1, f"Unknow Type {type}")
                    continue

                # Tagging
                colors = sh.cell_value(i, 5)
                tags = f"{pattern} {color} {sh.cell_value(i, 13)} {material} {finish} {description}"

                # Status
                statusP = True

                if type == "Pillow":
                    statusS = False
                else:
                    statusS = True

                if mpn in outletMPNs:
                    outlet = True
                else:
                    outlet = False

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
                'size': size,
                'repeat': repeat,

                'material': material,
                'finish': finish,
                'care': care,
                'weight': weight,
                'country': country,
                'upc': upc,

                'cost': cost,
                'uom': uom,

                'tags': tags,
                'colors': colors,

                'statusP': statusP,
                'statusS': statusS,
                'outlet': outlet
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        stocks = []

        wb = xlrd.open_workbook(f"{FILEDIR}/mindthegap-pillow-inventory.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            sku = f"MTG {common.formatText(sh.cell_value(i, 1))}"
            stockP = common.formatInt(sh.cell_value(i, 5))

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        wb = xlrd.open_workbook(f"{FILEDIR}/mindthegap-fabric-inventory.xlsx")
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            sku = f"MTG {common.formatText(sh.cell_value(i, 1))}"
            stockP = common.formatInt(sh.cell_value(i, 7))

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        products = MindTheGap.objects.filter(type="Wallpaper")
        for product in products:
            stock = {
                'sku': product.sku,
                'quantity': 5,
                'note': ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=2)

    def image(self):
        csr = self.con.cursor()

        hasImage = []

        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = '{}'".format(BRAND))
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        images = self.databaseManager.browseSFTP(
            src="/mindthegap/images/normal")

        for image in images:
            if "_" in image:
                mpn = image.split("_")[0]
                try:
                    idx = int(image.split("_")[1].split(".")[0]) + 1
                except Exception as e:
                    print(e)
                    continue

                try:
                    product = MindTheGap.objects.get(mpn=mpn)
                    if not product.productId or product.productId in hasImage:
                        continue
                except MindTheGap.DoesNotExist:
                    continue

                self.databaseManager.downloadFileFromSFTP(
                    src=f"/mindthegap/images/normal/{image}", dst=f"{FILEDIR}/../../../images/roomset/{product.productId}_{idx}.jpg", fileSrc=True, delete=False)

            else:
                mpn = image.split(".")[0]

                try:
                    product = MindTheGap.objects.get(mpn=mpn)
                    if not product.productId or product.productId in hasImage:
                        continue
                except MindTheGap.DoesNotExist:
                    continue

                self.databaseManager.downloadFileFromSFTP(
                    src=f"/mindthegap/images/normal/{image}", dst=f"{FILEDIR}/../../../images/product/{product.productId}.jpg", fileSrc=True, delete=False)

        csr.close()

    def hires(self):
        images = self.databaseManager.browseSFTP(
            src="/mindthegap/images/hires")
        for image in images:
            mpn = image.split("_")[0]

            try:
                product = MindTheGap.objects.get(mpn=mpn)
                if not product.productId:
                    continue
            except MindTheGap.DoesNotExist:
                continue

            self.databaseManager.downloadFileFromSFTP(
                src=f"/mindthegap/images/hires/{image}", dst=f"{FILEDIR}/../../../images/hires/{product.productId}_20.jpg", fileSrc=True, delete=False)
