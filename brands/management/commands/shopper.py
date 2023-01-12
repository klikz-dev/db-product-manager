from django.core.management.base import BaseCommand

import requests
import json
import time
import datetime
import pymysql
import os
import boto3
import html

from library import debug

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))
aws_access_key = env('aws_access_key')
aws_secret_key = env('aws_secret_key')

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEEDDIR = FILEDIR + '/files/feed/DecoratorsBestSA.xml'


SHOPIFY_API_URL = "https://decoratorsbest.myshopify.com/admin/api/{}".format(
    env('shopify_api_version'))
SHOPIFY_ORDER_API_HEADER = {
    'X-Shopify-Access-Token': env('shopify_order_token')
}


class Command(BaseCommand):
    help = 'Shopper Approved'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "feed" in options['functions']:
            while True:
                self.feed()
                self.upload()
                print("Finished Process. Waiting for Next run")
                time.sleep(86400 * 3)

        if "main" in options['functions']:
            self.followup()
            self.reward()

    def formatter(self, s):
        if s != None and s != "":
            allowedCharaters = [" ", ",", ".", "'", "\"", "*",
                                "(", ")", "$", "&", "-", "=", "+", "/", "!", "%", "^", "@", ":", ";", "{", "}", "[", "]", "?"]

            cleaned = [character for character in s if character.isalnum()
                       or character in allowedCharaters]

            return html.escape("".join(cleaned))
        else:
            return ""

    def feed(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        if os.path.isfile(FEEDDIR):
            os.remove(FEEDDIR)
        f = open(FEEDDIR, "w+")

        csr.execute("""SELECT P.SKU, P.Title AS PName, P.Handle, PI.ImageURL, M.Name as Manufacturer, PV.Price * PV.MinimumQuantity AS Price, T.Name AS Type, 
                      (SELECT Name FROM Tag T JOIN ProductTag PT on T.TagID = PT.TagID WHERE T.Published=1 AND T.Deleted=0 AND T.ParentTagID=2 AND PT.SKU = P.SKU LIMIT 1) AS DesignStyle,
                      (SELECT Name FROM Tag T JOIN ProductTag PT on T.TagID = PT.TagID WHERE T.Published=1 AND T.Deleted=0 AND T.ParentTagID=3 AND PT.SKU = P.SKU LIMIT 1) AS Color,
                      PV.Weight,
                      PV.GTIN,
                      P.ManufacturerPartNumber,
                      P.BodyHTML,
                      PV.Cost,
                      PV.Price as SPrice,
                      P.ProductID
                      FROM Product P
                      LEFT JOIN ProductImage PI ON P.ProductID = PI.ProductID
                      LEFT JOIN ProductVariant PV ON P.ProductID = PV.ProductID
                      LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU
                      LEFT JOIN Manufacturer M ON M.ManufacturerID = PM.ManufacturerID
                      LEFT JOIN Type T ON P.ProductTypeID = T.TypeID
                      WHERE PI.ImageIndex = 1
                      AND PV.Cost != 0
                      AND P.Published = 1
                      AND P.ManufacturerPartNumber <> ''
                      AND PV.IsDefault=1
                      AND PV.Published=1
                      AND M.Published=1
                      AND P.Name NOT LIKE '%Borders'
                      AND P.SKU NOT IN (
                        SELECT P.SKU FROM Product P JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID 
                        WHERE (P.Name LIKE '%Disney%' AND M.Brand = 'York')
                      )""")

        f.write('<?xml version="1.0"?>')
        f.write('<products>')

        count = 0
        for row in csr.fetchall():
            sku = row[0]

            title = self.formatter("{} - {}".format(row[1].title(), sku))
            desc = self.formatter(row[12].replace(
                "<br/>", " ").replace("<br>", " "))
            if desc == "":
                desc = title
            handle = row[2]
            imageURL = row[3]

            brand = self.formatter(row[4])
            brand = brand.replace("Covington", "DB By DecoratorsBest").replace(
                "Premier Prints", "DB By DecoratorsBest")

            price = row[5]
            productID = row[15]

            debug.debug("Shopper", 0, "Writing -- ProductID: {}, SKU: {}, Brand: {}, Cost: {}".format(
                productID, sku, brand, price))

            ptype = row[6]
            gtin = row[10]
            mpn = row[11]
            if ptype == "Fabric":
                category = "Arts & Entertainment > Hobbies & Creative Arts > Arts & Crafts > Art & Crafting Materials > Textiles > Fabric"
                productType = "Home & Garden > Bed and Living Room > Home Fabric"
            elif ptype == "Wallpaper":
                category = "Home & Garden > Decor > Wallpaper"
                productType = "Home & Garden > Bed and Living Room > Home Wallpaper"
            else:
                category = "Home & Garden > Decor"
                productType = ""
            count = count + 1

            category = self.formatter(category)
            productType = self.formatter(productType)

            f.write('<product id="{}">'.format(productID))

            f.write('<name>{}</name>'.format(title))
            f.write('<description>{}</description>'.format(desc))
            f.write(
                '<url>https://www.decoratorsbest.com/products/{}</url>'.format(handle))
            f.write('<image>{}</image>'.format(imageURL))
            f.write('<mpn>{}</mpn>'.format(mpn))
            f.write('<sku>{}</sku>'.format(sku))
            f.write('<upc></upc>')
            f.write('<gtin>{}</gtin>'.format(gtin))
            f.write('<ean></ean>')
            f.write('<isbn></isbn>')
            f.write('<code></code>')

            f.write('</product>')

        f.write('</products>')
        f.close()

        csr.close()
        con.close()

    def upload(self):
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key,
                          aws_secret_access_key=aws_secret_key)
        bucket_name = 'decoratorsbestimages'

        s3.upload_file(FEEDDIR,
                       bucket_name, "DecoratorsBestSA.xml", ExtraArgs={'ACL': 'public-read'})
        debug.debug(
            "Shopper", 0, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestSA.xml')

    def followup(self):
        today = datetime.date.today()

        start = today - datetime.timedelta(days=7)
        to = today - datetime.timedelta(days=6)
        followup = today + datetime.timedelta(days=3)

        s = requests.Session()

        nextLink = "{}/orders.json?status=any&fulfillment_status=shipped&updated_at_min={}&updated_at_max={}".format(
            SHOPIFY_API_URL, start, to)

        page = 0
        while nextLink != "":
            page += 1
            res = s.get(nextLink, headers=SHOPIFY_ORDER_API_HEADER)

            headers = res.headers
            nextLink = ""
            try:
                if headers['Link'] != None:
                    rel = headers['Link'].split("rel=")[1].replace('"', '')
                    if rel == "next":
                        nextLink = headers['Link'].split(
                            ";")[0].replace("<", "").replace(">", "")
            except:
                pass

            body = json.loads(res.text)
            orders = body['orders']

            for order in orders:
                orderNumber = order['order_number']
                customerName = "{} {}".format(
                    order['customer']['first_name'], order['customer']['last_name'])
                email = order['email']

                productIds = []
                for line_item in order['line_items']:
                    productId = line_item['product_id']
                    productIds.append(productId)

                debug.debug("Shopper", 0, "Requesting Review for PO: {}, Customer: {}, Email: {}".format(
                    orderNumber, customerName, email))

                try:
                    saReq = s.post("https://api.shopperapproved.com/reviews/26410/{}".format(
                        orderNumber), data={"token": "a24cf54fa5", "followup": followup, "orderid": orderNumber,
                                            "name": customerName, "products": productIds, "email": email})

                    saRes = json.loads(saReq.text)
                    print(saRes)
                except Exception as e:
                    print(e)
                    continue

    def reward(self):
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        url = "https://api.shopperapproved.com/reviews/26410?token=a24cf54fa5&from={}".format(
            yesterday)

        payload = {}
        headers = {}

        yotpoURL = "https://loyalty.yotpo.com/api/v2/actions"
        yotpoHeaders = {
            'x-guid': 'iFmwz0U2X_848XL9wZaPsg',
            'x-api-key': 'QTi7jhR5TzhekEUwOpKn8Qtt'
        }

        try:
            response = requests.request(
                "GET", url, headers=headers, data=payload)
            j = json.loads(response.text)
        except Exception as e:
            print(e)
            return

        for row in j:
            if row != "total_count":
                email = j[row]['email_address']

                yotpoPayload = {
                    'type': 'CustomAction',
                    'customer_email': email,
                    'action_name': 'shopper_approval_signup',
                    'reward_points': '10',
                    'history_title': 'Leave a Review'
                }

                try:
                    req = requests.request(
                        "POST", yotpoURL, headers=yotpoHeaders, data=yotpoPayload)

                    res = json.loads(req.text)

                    print(email)
                    print(res)
                except Exception as e:
                    print(e)
                    continue
