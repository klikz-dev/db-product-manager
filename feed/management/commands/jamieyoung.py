from django.core.management.base import BaseCommand
from feed.models import Feed

import os
import environ
import pymysql
import xlrd
import paramiko
import csv
import time

from library import database, debug, common

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Jamie Young"


class Command(BaseCommand):
    help = "Build {} Database".format(BRAND)

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()
        if "feed" in options['functions']:
            processor.feed()

        if "sync" in options['functions']:
            processor.sync()

        if "add" in options['functions']:
            processor.add()

        if "update" in options['functions']:
            processor.update()

        if "tag" in options['functions']:
            processor.tag()

        if "sample" in options['functions']:
            processor.sample()

        if "shipping" in options['functions']:
            processor.shipping()

        if "inventory" in options['functions']:
            while True:
                processor.inventory()
                print("Finished process. Waiting for next run. {}:{}".format(
                    BRAND, options['functions']))
                time.sleep(86400)


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(self.con, BRAND)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Discontinued
        discontinued_mpns = []
        wb = xlrd.open_workbook(FILEDIR + 'jamieyoung-discontinued.xlsx')
        sh = wb.sheet_by_index(0)
        for i in range(1, sh.nrows):
            discontinued_mpns.append(str(sh.cell_value(i, 0)).strip())

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(FILEDIR + 'jamieyoung-master.xlsx')
        sh = wb.sheet_by_index(0)
        for i in range(2, sh.nrows):
            try:
                # Primary Keys
                mpn = str(sh.cell_value(i, 0)).strip()
                if mpn in discontinued_mpns:
                    debug.debug(BRAND, 1, f"Item discontinued: {mpn}")
                    continue

                sku = "JY {}".format(mpn)
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
                try:
                    width = round(float(sh.cell_value(i, 11)), 2)
                except:
                    width = 0
                try:
                    length = round(float(sh.cell_value(i, 10)), 2)
                except:
                    length = 0
                try:
                    height = round(float(sh.cell_value(i, 12)), 2)
                except:
                    height = 0

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
                'length': length,
                'height': height,
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

    def image(self, productId, thumbnail, roomsets):
        if thumbnail and thumbnail.strip() != "":
            try:
                common.picdownload2(thumbnail, "{}.jpg".format(productId))
            except Exception as e:
                debug.debug(BRAND, 1, str(e))

        if len(roomsets) > 0:
            idx = 2
            for roomset in roomsets:
                try:
                    common.roomdownload(
                        roomset, "{}_{}.jpg".format(productId, idx))
                    idx = idx + 1
                except Exception as e:
                    debug.debug(BRAND, 1, str(e))

    def downloadInvFile(self):
        debug.debug(BRAND, 0, "Download New CSV from {} FTP".format(BRAND))

        host = "18.206.49.64"
        port = 22
        username = "jamieyoung"
        password = "JY123!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug.debug(
                BRAND, 2, "Connection to {} FTP Server Failed".format(BRAND))
            return False

        try:
            sftp.chdir(path='/jamieyoung')
            files = sftp.listdir()
        except:
            debug.debug(BRAND, 1, "No New Inventory File")
            return False

        for file in files:
            if "EDI" in file:
                continue
            sftp.get(file, FILEDIR + 'jamieyoung-inventory.csv')
            sftp.remove(file)

        sftp.close()

        debug.debug(BRAND, 0, "FTP Inventory Download Completed".format(BRAND))
        return True

    def feed(self):
        products = self.fetchFeed()
        self.databaseManager.writeFeed(products)

    def sync(self):
        self.databaseManager.statusSync()

    def add(self):
        self.databaseManager.createProducts()

    def update(self):
        self.databaseManager.updateProducts()

    def tag(self):
        self.databaseManager.updateTags(False)

    def sample(self):
        self.databaseManager.customTags("statusS", "NoSample")

    def shipping(self):
        self.databaseManager.customTags("whiteShip", "White Glove")

    def inventory(self):
        stocks = []

        if not self.downloadInvFile():
            return

        f = open(FILEDIR + 'jamieyoung-inventory.csv', "rt")
        cr = csv.reader(f)
        for row in cr:
            try:
                mpn = row[1]
                quantity = int(row[2])

                product = Feed.objects.get(mpn=mpn)
            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            stock = {
                'sku': product.sku,
                'quantity': quantity,
                'note': product.stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks, 1)
