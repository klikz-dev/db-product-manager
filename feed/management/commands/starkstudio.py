from django.core.management.base import BaseCommand
from feed.models import Feed

import os
import environ
import pymysql
import xlrd
import csv
import time
import paramiko
from shutil import copyfile

from library import database, debug

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Stark Studio"


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

        if "price" in options['functions']:
            processor.price()

        if "image" in options['functions']:
            processor.image()

        if "tag" in options['functions']:
            processor.tag()

        if "sample" in options['functions']:
            processor.sample()

        if "shipping" in options['functions']:
            processor.shipping()

        if "inventory" in options['functions']:
            processor.inventory()

        if "main" in options['functions']:
            while True:
                processor.feed()
                processor.sync()
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

        # Price Update Manual
        prices = {}
        wb = xlrd.open_workbook(FILEDIR + 'stark-studio-price.xlsx')
        sh = wb.sheet_by_index(0)
        for i in range(2, sh.nrows):
            # Primary Keys
            mpn = str(sh.cell_value(i, 3)).strip()
            # Pricing
            try:
                cost = round(
                    float(str(sh.cell_value(i, 4)).replace("$", "")), 2)
            except:
                debug.debug(
                    BRAND, 1, "Produt Cost error {}".format(mpn))
                continue

            try:
                map = round(
                    float(str(sh.cell_value(i, 5)).replace("$", "")), 2)
            except:
                debug.debug(
                    BRAND, 1, "Produt MAP error {}".format(mpn))
                continue

            prices[mpn] = {
                'cost': cost,
                'map': map
            }

        # Stock
        self.downloadInvFile()
        stocks = {}
        f = open(FILEDIR + 'stark-studio-inventory.csv', "rt")
        cr = csv.reader(f)
        for row in cr:
            try:
                mpn = row[0]
                quantity = int(row[1])

                statusP = True
                if int(row[5]) == 1:
                    statusP = False

                statusS = False
                if int(row[7]) == 1:
                    statusS = True
            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            stocks[mpn] = {
                'stockP': quantity,
                'statusP': statusP,
                'statusS': statusS
            }

        # Get Product Feed
        products = []

        wb = xlrd.open_workbook(FILEDIR + 'stark-studio-master.xlsx')
        for index in [0, 1, 2]:
            sh = wb.sheet_by_index(index)
            for i in range(2, sh.nrows):
                try:
                    # Primary Keys
                    mpn_origin = str(sh.cell_value(i, 3)).strip()
                    mpn = str(sh.cell_value(i, 4)).strip()
                    sku = "SS {}".format(mpn)
                    try:
                        upc = int(sh.cell_value(i, 2))
                    except:
                        upc = ""

                    if "-" in str(sh.cell_value(i, 0)):
                        pattern = str(sh.cell_value(i, 0)).split(
                            "-")[0].strip()
                        color = str(sh.cell_value(i, 0)).split("-")[1].strip()
                    else:
                        pattern = str(sh.cell_value(i, 0)).strip()
                        color = str(sh.cell_value(i, 1)).strip()

                    # Categorization
                    brand = BRAND
                    type = "Rug"
                    manufacturer = "{} {}".format(brand, type)
                    if index == 0:
                        collection = "Essentials Machinemades"
                    if index == 1:
                        collection = "Essentials Handmades"
                    if index == 2:
                        collection = "Fabricated Rug Program"

                    # Main Information
                    description = str(sh.cell_value(i, 11)).strip()
                    try:
                        width = int(sh.cell_value(i, 8))
                    except:
                        width = 0
                    try:
                        length = int(sh.cell_value(i, 9))
                    except:
                        length = 0

                    # Additional Information
                    material = str(sh.cell_value(i, 19)).strip()
                    country = str(sh.cell_value(i, 20)).strip()
                    try:
                        weight = float(sh.cell_value(i, 12))
                    except:
                        weight = 5

                    # Measurement
                    uom = "Per Item"

                    # Pricing
                    try:
                        cost = round(
                            float(str(sh.cell_value(i, 5)).replace("$", "")), 2)
                    except:
                        debug.debug(
                            BRAND, 1, "Produt Cost error {}".format(mpn))
                        continue

                    try:
                        map = round(
                            float(str(sh.cell_value(i, 6)).replace("$", "")), 2)
                    except:
                        debug.debug(
                            BRAND, 1, "Produt MAP error {}".format(mpn))
                        continue

                    # Tagging
                    tags = description
                    colors = str(sh.cell_value(i, 1)).strip()

                    statusP = True
                    statusS = False
                    stockNote = str(sh.cell_value(i, 21)).strip().capitalize()
                    whiteShip = False
                    if "white glove" in str(sh.cell_value(i, 17)).lower() or "ltl" in str(sh.cell_value(i, 17)).lower():
                        whiteShip = True

                    # Custom Stock and Price data
                    if mpn_origin in prices:
                        cost = prices[mpn_origin]['cost']
                        map = prices[mpn_origin]['map']

                    if mpn_origin in stocks:
                        statusS = stocks[mpn_origin]['statusS']
                        statusP = stocks[mpn_origin]['statusP']
                        stockP = stocks[mpn_origin]['stockP']

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
                    'width': width,
                    'length': length,
                    'weight': weight,

                    'material': material,
                    'country': country,

                    'uom': uom,

                    'tags': tags,
                    'colors': colors,

                    'cost': cost,
                    'map': map,

                    'statusP': statusP,
                    'statusS': statusS,

                    'stockP': stockP,
                    'stockNote': stockNote,
                    'whiteShip': whiteShip
                }
                products.append(product)

        debug.debug(BRAND, 0, "Finished fetching data from the supplier")
        return products

    def image(self):
        imageDir = FILEDIR + "images/stark/"

        products = Feed.objects.filter(brand=BRAND)
        for product in products:
            productStr = "{} {}".format(product.pattern, product.color).replace(
                ",", "").replace("/", " ").lower()

            for fname in os.listdir(imageDir):
                if productStr in fname.lower() or product.pattern in fname.lower():
                    if "_CL" in fname:
                        print("Roomset 2: {}".format(fname))
                        copyfile(imageDir + fname, FILEDIR +
                                 "/../../../images/roomset/{}_2.jpg".format(product.productId))

                    elif "_ALT1" in fname:
                        print("Roomset 3: {}".format(fname))
                        copyfile(imageDir + fname, FILEDIR +
                                 "/../../../images/roomset/{}_3.jpg".format(product.productId))

                    elif "_ALT2" in fname:
                        print("Roomset 4: {}".format(fname))
                        copyfile(imageDir + fname, FILEDIR +
                                 "/../../../images/roomset/{}_4.jpg".format(product.productId))

                    elif "_RM" in fname:
                        print("Roomset 5: {}".format(fname))
                        copyfile(imageDir + fname, FILEDIR +
                                 "/../../../images/roomset/{}_5.jpg".format(product.productId))

                    else:
                        print("Product: {}".format(fname))
                        copyfile(imageDir + fname, FILEDIR +
                                 "/../../../images/product/{}.jpg".format(product.productId))

    def feed(self):
        products = self.fetchFeed()
        self.databaseManager.writeFeed(products)

    def sync(self):
        self.databaseManager.statusSync()

    def add(self):
        self.databaseManager.createProducts()

    def price(self):
        self.databaseManager.updatePrices(False)

    def update(self):
        self.databaseManager.updateProducts()

    def tag(self):
        self.databaseManager.updateTags(False)

    def sample(self):
        self.databaseManager.customTags("statusS", "NoSample")

    def shipping(self):
        self.databaseManager.customTags("whiteShip", "White Glove")

    def downloadInvFile(self):
        debug.debug(BRAND, 0, "Download New CSV from {} FTP".format(BRAND))

        host = "18.206.49.64"
        port = 22
        username = "stark"
        password = "Stark123!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug.debug(
                BRAND, 2, "Connection to {} FTP Server Failed".format(BRAND))
            return False

        try:
            sftp.chdir(path='/stark')
            files = sftp.listdir()
        except:
            debug.debug(BRAND, 1, "No New Inventory File")
            return False

        for file in files:
            if "EDI" in file:
                continue
            sftp.get(file, FILEDIR + 'stark-studio-inventory.csv')
            sftp.remove(file)

        sftp.close()

        debug.debug(BRAND, 0, "FTP Inventory Download Completed".format(BRAND))
        return True

    def inventory(self):
        stocks = []

        products = Feed.objects.filter(brand=BRAND)
        for product in products:
            stock = {
                'sku': product.sku,
                'quantity': product.stockP,
                'note': product.stockNote
            }
            stocks.append(stock)

        self.databaseManager.updateStock(stocks, 1)
