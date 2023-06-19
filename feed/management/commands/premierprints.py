from django.core.management.base import BaseCommand
from django.db.models import Q
from feed.models import PremierPrints

import os
import environ
import pymysql
import xlrd
import time
from shutil import copyfile

from library import database, debug, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Premier Prints"


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
            processor.databaseManager.createProducts(
                formatPrice=True, private=True)

        if "update" in options['functions']:
            products = PremierPrints.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor.image()

        if "roomset" in options['functions']:
            processor.roomset()

        if "inventory" in options['functions']:
            while True:
                try:
                    processor.databaseManager.downloadFileFromSFTP(
                        src="inv_export.new.csv", dst=f"{FILEDIR}/premierprints-inventory.csv")
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
            con=self.con, brand=BRAND, Feed=PremierPrints)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(f"{FILEDIR}/premierprints-master.xlsx")
        sh = wb.sheet_by_index(0)

        for i in range(1, sh.nrows):
            try:
                # Primary Keys
                mpn = common.formatText(sh.cell_value(i, 0))
                sku = f"DBP {mpn}"
                pattern = common.formatText(sh.cell_value(i, 4))
                color = common.formatText(sh.cell_value(i, 5))

                # Categorization
                brand = BRAND
                type = common.formatText(sh.cell_value(i, 3))
                manufacturer = f"{brand} {type}"
                collection = common.formatText(sh.cell_value(i, 2))

                # Main Information
                description = common.formatText(sh.cell_value(i, 9))
                width = common.formatFloat(sh.cell_value(i, 10))
                repeatH = common.formatFloat(sh.cell_value(i, 14))
                repeatV = common.formatFloat(sh.cell_value(i, 13))
                usage = common.formatText(sh.cell_value(i, 20))

                # Additional Information

                # Pricing
                cost = common.formatFloat(sh.cell_value(i, 8))

                # Measurement
                uom = f"Per {common.formatText(sh.cell_value(i, 19))}"
                minimum = 2

                # Tagging
                tags = f"{sh.cell_value(i, 20)}, {sh.cell_value(i, 25)}, {pattern}"
                colors = sh.cell_value(i, 24)

                if "Outdoor" in tags:
                    tags = f"Performance Fabric, {tags}"

                # Image

                # Status
                statusP = True
                statusS = True

                blandMPNs = [
                    'W-SLUB08',
                    'W-SLUB07',
                    'W-FLAXWH',
                    'W-FLAX',
                    'W-COTTWHITE',
                    'W-COTNAT10',
                    'TSPUN',
                    'LINITWHT'
                ]
                if mpn in blandMPNs:
                    statusP = False

            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            product = {
                'mpn': mpn,
                'sku': sku,
                'pattern': pattern,
                'color': color,

                'brand': BRAND,
                'type': type,
                'manufacturer': manufacturer,
                'collection': collection,

                'width': width,
                'description': description,
                'repeatH': repeatH,
                'repeatV': repeatV,
                'usage': usage,

                'cost': cost,

                'uom': uom,
                'minimum': minimum,

                'tags': tags,
                'colors': colors,

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

        products = PremierPrints.objects.all()
        for product in products:
            if not product.productId or not product.thumbnail:
                continue

            if product.productId in hasImage:
                continue

            self.databaseManager.downloadFileFromSFTP(
                src=f"{product.mpn}-L.jpg",
                dst=f"{FILEDIR}/../../../images/product/{product.productId}.jpg"
            )

        csr.close()

    def roomset(self):
        fnames = os.listdir(f"{FILEDIR}/images/premier-prints/")

        for fname in fnames:
            try:
                if "-" in fname:
                    mpn = fname.split("-")[0]
                    print(mpn)
                    roomId = 2

                    product = PremierPrints.objects.get(mpn=mpn)
                    productId = product.productId

                    if productId:
                        copyfile(f"{FILEDIR}/images/premier-prints/{fname}",
                                 f"{FILEDIR}/../../../images/roomset/{productId}_{roomId}.jpg")

                        debug.debug(BRAND, 0, "Roomset Image {}_{}.jpg".format(
                            productId, roomId))

                        os.remove(f"{FILEDIR}/images/premier-prints/{fname}")
                    else:
                        print("No product found with MPN: {}".format(mpn))
                else:
                    continue

            except Exception as e:
                print(e)
                continue
