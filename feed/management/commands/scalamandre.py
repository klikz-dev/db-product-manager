from django.core.management.base import BaseCommand
from feed.models import Feed

import os
import environ
import pymysql
import requests
import paramiko
import csv
import time
import json

from library import database, debug, common

API_ADDRESS = 'http://scala-api.scalamandre.com/api'
API_USERNAME = 'Decoratorsbest'
API_PASSWORD = 'EuEc9MNAvDqvrwjgRaf55HCLr8c5B2^Ly%C578Mj*=CUBZ-Y4Q5&Sc_BZE?n+eR^gZzywWphXsU*LNn!'

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

BRAND = "Scalamandre"


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
                print("Finished process. Waiting for next run. {}:{}".format(BRAND, options['functions']))
                time.sleep(86400)


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(self.con)

        r = requests.post("{}/Auth/authenticate".format(API_ADDRESS), headers={'Content-Type': 'application/json'},
                        data=json.dumps({"Username": API_USERNAME, "Password": API_PASSWORD}))
        j = json.loads(r.text)
        self.token = j['Token']

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

        # Get Product Feed
        products = []

        try:
            r = requests.get("{}/ScalaFeedAPI/FetchProductsFeed".format(API_ADDRESS),
                             headers={'Authorization': 'Bearer {}'.format(self.token)})
            j = json.loads(r.text)
            rows = j['FEEDPRODUCTS']

        except Exception as e:
            debug.debug(BRAND, 1, str(e))
            return

        for row in rows:
            try:
                # Primary Keys
                mpn = row['ITEMID']
                sku = "SCALA {}".format(row['SKU'])
                pattern = str(row['PATTERN_DESCRIPTION']).replace(
                    "PILLOW", "").strip().title()
                color = str(row['COLOR']).strip().title()

                # Categorization
                brand = BRAND

                type = row['CATEGORY']
                if "FABR" in type:
                    type = "Fabric"
                elif "WALL" in type:
                    type = "Wallpaper"
                elif "TRIM" in type:
                    type = "Trim"
                elif "PILL" in type:
                    type = "Pillow"
                else:
                    debug.debug(BRAND, 1, "Unknown product type: {}".format(type))
                    continue

                manufacturer = str(row['BRAND']).strip()
                if "Scalamandre" in manufacturer or "Wallquest" in manufacturer or "Scalamandré" in manufacturer:
                    manufacturer = "Scalamandre"
                elif "Old World Weavers" in manufacturer:
                    sku = "OWW {}".format(mpn)
                elif "Grey Watkins" in brand:
                    sku = "GWA {}".format(mpn)

                collection = row.get('WEB COLLECTION NAME', '')

                # Main Information
                description = str(row['DESIGN_INSPIRATION']).strip()
                try:
                    width = round(float(row['WIDTH']), 2)
                except:
                    width = 0
                try:
                    size = row['PIECE SIZE']
                except:
                    size = ""
                try:
                    yards = round(float(row['YARDS PER ROLL']), 2)
                except:
                    yards = 0
                try:
                    repeatV = round(float(row['PATTERN REPEAT LENGTH']), 2)
                except:
                    repeatV = 0
                try:
                    repeatH = round(float(row['PATTERN REPEAT WIDTH']), 2)
                except:
                    repeatH = 0
                try:
                    content = row['FIBER CONTENT']
                except:
                    content = ""
                    pass

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
                    cost = round(float(row['NETPRICE']), 2)
                except:
                    debug.debug(BRAND, 1, "Produt Cost error {}".format(mpn))
                    continue

                # Tagging
                tags = "{}, {}, {}, {}".format(str(sh.cell_value(i, 19)).strip(), ", ".join(features), collection, description)
                colors = color

                statusP = True
                statusS = False
                stockNote = "3 days"
                shipping = str(sh.cell_value(i, 35)).strip()

                # Image
                thumbnail = str(sh.cell_value(i, 49)).strip().replace("dl=0", "dl=1")
                roomsets = []
                for id in range(50, 63):
                    roomset = str(sh.cell_value(i, id)).strip().replace("dl=0", "dl=1")
                    if roomset != "":
                        roomsets.append(roomset)

                # Pattern Name
                ptypeTmp = type
                if ptypeTmp[len(ptypeTmp) - 1] == "s":
                    ptypeTmp = ptypeTmp[:-1]

                for typeword in ptypeTmp.split(" "):
                    pattern = pattern.replace(typeword, "")

                pattern = pattern.replace("**MUST SHIP COMMON CARRIER**", "").replace("  ", " ").strip()
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
            debug.debug(BRAND, 2, "Connection to {} FTP Server Failed".format(BRAND))
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
        self.databaseManager.writeFeed(BRAND, products)

    def sync(self):
        self.databaseManager.statusSync(BRAND)

    def add(self):
        self.databaseManager.createProducts(BRAND)

    def update(self):
        self.databaseManager.updateProducts(BRAND)

    def tag(self):
        self.databaseManager.updateTags(BRAND, False)

    def sample(self):
        self.databaseManager.customTags(BRAND, "statusS", "NoSample")

    def shipping(self):
        self.databaseManager.customTags(BRAND, "whiteShip", "White Glove")

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

        self.databaseManager.updateStock(BRAND, stocks, 1)
