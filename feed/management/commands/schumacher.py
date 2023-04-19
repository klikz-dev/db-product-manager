from django.core.management.base import BaseCommand
from feed.models import Schumacher

import os
import environ
import pymysql
import csv
import codecs
import paramiko
import time

from library import database, debug

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

BRAND = "Schumacher"


class Command(BaseCommand):
    help = f"Build {BRAND} Database"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            products = processor.fetchFeed()
            processor.databaseManager.writeFeed(products=products)

        if "sync" in options['functions']:
            processor.databaseManager.statusSync(fullSync=False)

        if "add" in options['functions']:
            processor.databaseManager.createProducts(formatPrice=True)

        if "update" in options['functions']:
            products = Schumacher.objects.all()
            processor.databaseManager.updateProducts(
                products=products, formatPrice=True)

        if "price" in options['functions']:
            processor.databaseManager.updatePrices(formatPrice=True)

        if "tag" in options['functions']:
            processor.databaseManager.updateTags(category=True)

        if "image" in options['functions']:
            processor.databaseManager.downloadImages(missingOnly=True)

        if "inventory" in options['functions']:
            while True:
                processor.inventory()
                print("Finished process. Waiting for next run. {}:{}".format(
                    BRAND, options['functions']))
                time.sleep(86400)

        if "pillow" in options['functions']:
            processor.databaseManager.linkPillowSample()


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(
            con=self.con, brand=BRAND, Feed=Schumacher)

    def __del__(self):
        self.con.close()

    def datasheet(self):
        debug.debug(
            BRAND, 0, "Download New Master CSV file from Schumacher FTP")

        host = "34.203.121.151"
        port = 22
        username = "schumacher"
        password = "Sch123Decbest!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug.debug("Schumacher", 2,
                        "Connection to Schumacher FTP Server Failed")
            return False

        sftp.get("../daily_feed/Assortment-DecoratorsBest.csv",
                 f"{FILEDIR}/schumacher-master.csv")

        sftp.close()

        debug.debug(BRAND, 0, "Schumacher FTP Master File Download Completed")
        return True

    def formatText(self, text):
        return str(text).replace('', '').replace('¥', '').replace('…', '').replace('„', '').strip()

    def formatFloat(self, value):
        if str(value).strip() != '':
            try:
                return round(float(str(value).replace('"', "").strip()), 2)
            except:
                return 0
        else:
            return 0

    def formatInt(self, value):
        if str(value).strip() != '':
            try:
                return int(float(str(value).replace('"', "").strip()))
            except:
                return 0
        else:
            return 0

    def fetchFeed(self):
        if not self.datasheet():
            return

        debug.debug(BRAND, 0, f"Started fetching data from {BRAND}")

        # Get Product Feed
        products = []

        f = open(f"{FILEDIR}/schumacher-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            if row[0] == "Category":
                continue

            try:
                # Primary Keys
                mpn = str(row[3]).strip().replace("'", "")
                sku = f"SCH {mpn}"

                pattern = self.formatText(row[4]).title()
                color = self.formatText(row[5]).title()

                type = str(row[0]).strip().title()

                if pattern == "" or color == "" or type == "":
                    continue

                if type == "Wallcovering":
                    type = "Wallpaper"
                if type == "Furniture & Accessories":
                    type = "Pillow"
                if type == "Rugs & Carpets":
                    type = "Rug"
                if "Throw" in pattern:
                    type = "Throw"

                pattern = pattern.replace(type, "").strip()

                # Categorization
                manufacturer = f"{BRAND} {type}"
                collection = str(row[2]).replace("Collection Name", "").strip()

                if "STAPETER" in collection:
                    manufacturer = f"BORÃSTAPETER {type}"
                    collection = "BORÃSTAPETER"

                # Main Information
                description = self.formatText(row[17])

                width = self.formatFloat(row[11])
                length = self.formatFloat(row[21])

                size = ""
                if (type == "Pillow" or type == "Rug" or type == "Throw") and width != "" and length != "":
                    size = f'{width}" x {length}"'

                repeatV = self.formatFloat(row[15])
                repeatH = self.formatFloat(row[16])

                # Additional Information
                match = str(row[14]).strip()

                yards = self.formatFloat(row[8])

                content = ", ".join(
                    (str(row[12]).strip(), str(row[13].strip())))

                # Measurement
                uom = str(row[9]).strip().upper()
                if "YARD" in uom or "REPEAT" in uom:
                    uom = "Per Yard"
                elif "ROLL" in uom:
                    uom = "Per Roll"
                elif "EA" in uom or "UNIT" in uom or "SET" in uom or "ITEM" in uom:
                    uom = "Per Item"
                elif "PANEL" in uom:
                    uom = "Per Panel"
                else:
                    debug.debug(BRAND, 1, f"UOM Error. mpn: {mpn}. uom: {uom}")

                minimum = self.formatInt(row[10])

                if type == "Wallpaper" and minimum > 1:
                    increment = ",".join([str(ii * minimum)
                                         for ii in range(1, 26)])
                else:
                    increment = ""

                # Pricing
                cost = self.formatFloat(row[7])

                # Tagging
                tags = ", ".join((collection, row[6], description))

                # Image
                thumbnail = str(row[18]).strip()
                roomsets = str(row[22]).split(",")

                # Status
                statusP = True

                if type == "Rug":
                    statusS = False
                else:
                    statusS = True

                if width > 107 or length > 107:
                    whiteShip = True
                else:
                    whiteShip = False

                # Stock
                stockP = int(float(row[19]))

                pass

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

                'description': description,
                'width': width,
                'length': length,
                'repeatV': repeatV,
                'repeatH': repeatH,
                'size': size,

                'match': match,
                'content': content,
                'yards': yards,

                'cost': cost,

                'uom': uom,
                'minimum': minimum,
                'increment': increment,

                'tags': tags,
                'colors': color,

                'thumbnail': thumbnail,
                'roomsets': roomsets,

                'statusP': statusP,
                'statusS': statusS,
                'whiteShip': whiteShip,

                'stockP': stockP,
            }
            products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def inventory(self):
        if not self.datasheet():
            return

        stocks = []

        f = open(f"{FILEDIR}/schumacher-master.csv", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            if row[0] == "Category":
                continue

            mpn = str(row[3]).strip().replace("'", "")
            sku = f"SCH {mpn}"
            stockP = int(float(row[19]))

            stock = {
                'sku': sku,
                'quantity': stockP,
                'note': ""
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks=stocks, stockType=1)
