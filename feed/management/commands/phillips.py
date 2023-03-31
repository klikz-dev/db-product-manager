from django.core.management.base import BaseCommand
from brands.models import Feed

import environ
import requests
import json
import pymysql

from library import database, debug, shopify, common


API_BASE_URL = "https://step-up-production.ue.r.appspot.com/v1"
API_KEY = "57d18c3398da46c9b19d8a5d86498765"
API_USERNAME = "orders@decoratorsbest.com"
API_PASSWORD = "m8q97J%7$MfC"

BRAND = "Phillips"


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


class Processor:
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

        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.databaseManager = database.DatabaseManager(self.con)

    def __del__(self):
        self.con.close()

    def fetchFeed(self):
        debug.debug(BRAND, 0, "Started fetching data from {}".format(BRAND))

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
                        if color == "":
                            color = row['description']['color'][0]
                        title = " ".join((pattern, color))

                        # Categorization
                        brand = BRAND

                        typeText = types.get(row['class']['category'], "")
                        if typeText == "" or typeText == "Abstract" or typeText == "Animals":
                            type = "Decor"
                        elif typeText == "Pedestals" or typeText == "Seating" or typeText == "Figures" or typeText == "Framed":
                            type = "Accents"
                        elif typeText == "Bowls / Vessels":
                            type = "Bowls"
                        elif typeText == "Consoles / Sofa Tables":
                            type = "Consoles"
                        elif typeText == "Dining Tables":
                            type = "Dining Chairs"
                        elif typeText == "Hanging Lamps":
                            type = "Accent Lamps"
                        else:
                            type = typeText

                        manufacturer = BRAND

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
                        tags = ", ".join((typeText, ", ".join(row['tags'])))
                        colors = ", ".join(row['description']['color'])

                        # Pricing
                        if row['price']['pricelist'] == "BASE":
                            cost = row['price']['price']
                        else:
                            debug(BRAND, 1,
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
                        debug.debug(BRAND, 1, str(e))
                        continue

                    product = {
                        'mpn': mpn,
                        'sku': sku,
                        'upc': upc,
                        'pattern': pattern,
                        'color': color,
                        'title': title,

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

    def feed(self):
        products = self.fetchFeed()
        self.databaseManager.writeFeed(BRAND, products)

    def sync(self):
        self.databaseManager.statusSync(BRAND)

    def add(self):
        products = Feed.objects.filter(brand=BRAND)

        for product in products:
            try:
                createdInDatabase = self.databaseManager.createProduct(
                    BRAND, product)
                if not createdInDatabase:
                    continue
            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            try:
                product.productId = shopify.NewProductBySku(
                    product.sku, self.con)
                product.save()

                self.image(product.productId,
                           product.thumbnail, product.roomsets)

                debug.debug(BRAND, 0, "Created New product ProductID: {}, SKU: {}".format(
                    product.productId, product.sku))

            except Exception as e:
                debug.debug(BRAND, 1, str(e))

    def update(self):
        products = Feed.objects.filter(brand=BRAND)

        for product in products:
            try:
                createdInDatabase = self.databaseManager.createProduct(
                    BRAND, product)
                if not createdInDatabase:
                    continue
            except Exception as e:
                debug.debug(BRAND, 1, str(e))
                continue

            try:
                self.csr.execute(
                    "CALL AddToPendingUpdateProduct ({})".format(product.productId))
                self.con.commit()

                debug.debug(BRAND, 0, "Updated the product ProductID: {}, SKU: {}".format(
                    product.productId, product.sku))

            except Exception as e:
                debug.debug(BRAND, 1, str(e))

    def tag(self):
        self.databaseManager.updateTags(BRAND, False)

    def sample(self):
        self.databaseManager.sample(BRAND)

    def inventory(self, mpn):
        try:
            response = requests.request(
                "GET",
                "https://step-up-production.ue.r.appspot.com/v1/ecomm/items/{}/inventory".format(
                    mpn),
                headers={
                    'x-api-key': API_KEY,
                    'Authorization': "Bearer {}".format(self.token)
                }
            )
            data = json.loads(response.text)
            stock = data['data']['qtyavailable']
        except Exception as e:
            debug.debug(BRAND, 1, str(e))
            stock = 0

        try:
            response = requests.request(
                "GET",
                "https://step-up-production.ue.r.appspot.com/v1/ecomm/items/{}/leadtime".format(
                    mpn),
                headers={
                    'x-api-key': API_KEY,
                    'Authorization': "Bearer {}".format(self.token)
                }
            )
            data = json.loads(response.text)
            leadtime = data['data']['leadtime'][0]['message']
        except Exception as e:
            debug.debug(BRAND, 1, str(e))
            leadtime = ""

        return {
            'stock': stock,
            'leadtime': leadtime
        }
