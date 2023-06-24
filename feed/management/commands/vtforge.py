from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import HubbardtonForge

import os
import environ
import pymysql
import xlrd
import requests
import json

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Hubbardton Forge"


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
            products = HubbardtonForge.objects.all()
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
            processor.image()

        if "sample" in options['functions']:
            processor = Processor()
            processor.databaseManager.customTags(
                key="statusS", tag="NoSample", logic=False)


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)
        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=HubbardtonForge)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/hubbardton-forge-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 1))
                sku = f"HF {mpn}"

                pattern = common.formatInt(sh.cell_value(i, 3))

                color = f"{common.formatText(sh.cell_value(i, 9))}"
                if sh.cell_value(i, 10):
                    color = f"{color} {sh.cell_value(i, 10)}"

                name = f"{color} {common.formatText(sh.cell_value(i, 2))}"

                # Categorization
                brand = BRAND

                type = common.formatText(sh.cell_value(i, 4))
                if "Chandelier" in name:
                    type = "Chandeliers"
                elif "Pendant" in name:
                    type = "Pendants"
                elif "Mount" in name:
                    type = "Flush Mounts"
                elif "Semi-Flush" in name:
                    type = "Semi-Flush Mounts"
                elif "Sconce" in name:
                    type = "Wall Sconces"
                elif "Side Table" in name:
                    type = "Side Tables"
                elif "Console" in name:
                    type = "Consoles"
                elif "Accent Table" in name:
                    type = "Accent Tables"
                else:
                    type = "Accessories"

                manufacturer = brand
                collection = common.formatText(sh.cell_value(i, 7))

                # Main Information
                description = f"{common.formatText(sh.cell_value(i, 72))} {common.formatText(sh.cell_value(i, 73))}"

                width = common.formatFloat(sh.cell_value(i, 21))
                height = common.formatFloat(sh.cell_value(i, 20))
                length = common.formatFloat(sh.cell_value(i, 22))

                # Additional Information
                weight = common.formatFloat(sh.cell_value(i, 26))

                finish = common.formatText(sh.cell_value(i, 9))
                if common.formatText(sh.cell_value(i, 10)):
                    finish = f"{finish}, {common.formatText(sh.cell_value(i, 10))}"

                features = []
                for id in range(74, 79):
                    feature = common.formatText(sh.cell_value(i, id))
                    if feature:
                        features.append(feature)

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 17))
                map = common.formatFloat(sh.cell_value(i, 18))
                msrp = common.formatFloat(sh.cell_value(i, 19))

                # Measurement
                uom = "Per Item"

                # Tagging
                tags = f"{sh.cell_value(i, 79)}, {sh.cell_value(i, 80)}, {sh.cell_value(i, 89)}, {type}, {name}"
                colors = color

                # Image
                thumbnail = sh.cell_value(i, 90)

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
                'name': name,

                'brand': BRAND,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'width': width,
                'description': description,
                'height': height,
                'length': length,

                'finish': finish,
                'weight': weight,
                'features': features,

                'cost': cost,
                'map': map,
                'msrp': msrp,

                'uom': uom,

                'tags': tags,
                'colors': colors,

                'thumbnail': thumbnail,

                'statusP': statusP,
                'statusS': statusS,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        csr = self.con.cursor()

        hasImage = []

        csr.execute("SELECT P.ProductID FROM ProductImage PI JOIN Product P ON PI.ProductID = P.ProductID JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE PI.ImageIndex = 1 AND M.Brand = '{}'".format(BRAND))
        for row in csr.fetchall():
            hasImage.append(str(row[0]))

        products = HubbardtonForge.objects.all()
        for product in products:
            if not product.productId or not product.thumbnail:
                continue

            if product.productId in hasImage:
                continue

            try:
                self.databaseManager.downloadFileFromLocalSFTP(
                    src=f"/vtforge/rendered_product_images/{product.thumbnail}",
                    dst=f"{FILEDIR}/../../../images/product/{product.productId}.jpg"
                )
            except Exception as e:
                debug.debug(BRAND, 1, str(e))

                try:
                    self.databaseManager.downloadFileFromLocalSFTP(
                        src=f"/vtforge/standard_product_images/{product.thumbnail}",
                        dst=f"{FILEDIR}/../../../images/product/{product.productId}.jpg"
                    )
                except Exception as e:
                    debug.debug(BRAND, 1, str(e))

        csr.close()
