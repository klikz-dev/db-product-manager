from django.core.management.base import BaseCommand
from brands.models import Feed

import os
import requests
import json
import pymysql

from library import database, debug, shopify, markup, common

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.starkstudio
markup_trade = markup.starkstudio_trade

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


API_BASE_URL = "https://step-up-production.ue.r.appspot.com/v1"
API_KEY = "57d18c3398da46c9b19d8a5d86498765"
API_USERNAME = "orders@decoratorsbest.com"
API_PASSWORD = "m8q97J%7$MfC"


class Command(BaseCommand):
    help = 'Build Phillips Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "feed" in options['functions']:
            self.feed()

        if "sync" in options['functions']:
            self.sync()

        if "add" in options['functions']:
            self.add()

    def __init__(self):
        response = requests.request(
            "POST",
            "{}{}".format(API_BASE_URL, "/auth"),
            headers={
                'Content-type': 'application/json',
                'x-api-key': API_KEY
            },
            data=json.dumps({
                "email": API_USERNAME,
                "password": API_PASSWORD
            })
        )
        data = json.loads(response.text)
        self.token = data['data']['token']

        self.con = pymysql.connect(host=db_host, user=db_username,
                                   passwd=db_password, db=db_name, connect_timeout=5)
        self.databaseManager = database.DatabaseManager(self.con)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug("Phillips", 0, "Started fetching data from the supplier")

        # Get Product Types
        types = {}
        response = requests.request(
            "GET",
            "https://step-up-production.ue.r.appspot.com/v1/items-categories",
            headers={
                'x-api-key': API_KEY,
                'Authorization': "Bearer {}".format(self.token)
            }
        )
        data = json.loads(response.text)
        for type in data['data']:
            types[type['_id']] = type['name']

        # Get Product Collections
        collections = {}
        response = requests.request(
            "GET",
            "https://step-up-production.ue.r.appspot.com/v1/items-collections",
            headers={
                'x-api-key': API_KEY,
                'Authorization': "Bearer {}".format(self.token)
            }
        )
        data = json.loads(response.text)
        for collection in data['data']:
            collections[collection['_id']] = collection['name']

        # Get Product Feed
        products = []
        page = 1
        while True:
            response = requests.request(
                "GET",
                "{}{}?page={}&page_size=100".format(
                    API_BASE_URL, "/ecomm/items", page),
                headers={
                    'x-api-key': API_KEY,
                    'Authorization': "Bearer {}".format(self.token)
                }
            )
            data = json.loads(response.text)

            if len(data['data']) > 0:
                for row in data['data']:
                    try:
                        # Primary Keys
                        mpn = row['_id']
                        sku = "PC {}".format(mpn)
                        upc = row['upc']
                        pattern = row['desc']
                        color = str(row['descspec']).replace(",", "")

                        # Categorization
                        brand = "Phillips"

                        typeText = types.get(row['class']['category'], "")
                        if typeText == "Bowls / Vessels":
                            typeText = "Bowls"
                        if typeText == "Consoles / Sofa Tables":
                            typeText = "Consoles"
                        type = self.databaseManager.fetchType(typeText)
                        if type == "":
                            type = "Furniture"

                        manufacturer = "Phillips"

                        if len(row['class']['collection']) > 0:
                            collection = collections.get(
                                row['class']['collection'][0], "")
                        else:
                            collection = ""

                        # Main Information
                        description = row['description']['story']
                        width = row['description']['sizew']
                        length = row['description']['sizel']
                        height = row['description']['sizeh']
                        weight = row['description']['weight']

                        # Additional Information
                        material = ", ".join(row['description']['material'])
                        addmat = ", ".join(row['description']['addmat'])
                        material = "{}, {}".format(material, addmat)
                        finish = ", ".join(row['description']['finish'])
                        care = row['description']['care']
                        disclaimer = row['description']['disclaimer']
                        country = row.get('countryoforigin', "")

                        # Measurement
                        uom = row['price']['uom']
                        if uom == "each":
                            uom = "Per Item"
                        minimum = row['price']['factor']

                        # Tagging
                        tags = "{}, {}".format(", ".join(row['tags']), type)
                        colors = ", ".join(row['description']['color'])

                        # Pricing
                        if row['price']['pricelist'] == "BASE":
                            cost = row['price']['price']
                        else:
                            debug("Phillips", 1,
                                  "Price Error for MPN: {}".format(mpn))
                            continue
                        msrp = row['msrp']
                        map = row['map']

                        # Availability
                        statusP = False
                        if row['status'] == "ACTIVE":
                            statusP = True

                        # Assets
                        thumbnail = row['assets']['images']['main']
                        roomsets = []
                        for roomset in row['assets']['images']['details']:
                            roomsets.append(roomset['url'])
                        for roomset in row['assets']['images']['lifestyle']:
                            roomsets.append(roomset['url'])
                    except Exception as e:
                        debug.debug("Phillips", 1, str(e))
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
                        'height': height,
                        'weight': weight,

                        'material': material,
                        'finish': finish,
                        'care': care,
                        'disclaimer': disclaimer,
                        'country': country,

                        'uom': uom,
                        'minimum': minimum,

                        'tags': tags,
                        'colors': colors,

                        'cost': cost,
                        'msrp': msrp,
                        'map': map,

                        'statusP': statusP,

                        'thumbnail': thumbnail,
                        'roomsets': roomsets,
                    }
                    products.append(product)

                page += 1
            else:
                break

        debug.debug("Phillips", 0, "Finished fetching data from the supplier")
        return products

    def downloadImages(self, productId, thumbnail, roomsets):
        if thumbnail and thumbnail.strip() != "":
            try:
                common.picdownload2(thumbnail, "{}.jpg".format(productId))
            except Exception as e:
                debug.debug("Phillips", 1, str(e))

        if len(roomsets) > 0:
            idx = 2
            for roomset in roomsets:
                try:
                    common.roomdownload(
                        roomset, "{}_{}.jpg".format(productId, idx))
                    idx = idx + 1
                except Exception as e:
                    debug.debug("Phillips", 1, str(e))

    def feed(self):
        products = self.fetchFeed()
        self.databaseManager.writeFeed("Phillips", products)

    def sync(self):
        self.databaseManager.statusSync("Phillips")

    def add(self):
        products = Feed.objects.filter(brand="Phillips")

        for product in products:
            try:
                createdInDatabase = self.databaseManager.createProduct(
                    "Phillips", product)
                if not createdInDatabase:
                    continue
            except Exception as e:
                debug.debug("Phillips", 1, str(e))
                continue

            try:
                productId = shopify.NewProductBySku(product.sku, self.con)
                if productId == None:
                    continue

                product.productId = productId
                product.save()

                self.downloadImages(
                    productId, product.thumbnail, product.roomsets)

                debug.debug("Phillips", 0, "Created New product ProductID: {}, SKU: {}".format(
                    productId, product.sku))

            except Exception as e:
                debug.debug("Phillips", 1, str(e))
