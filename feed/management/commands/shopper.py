from django.core.management.base import BaseCommand

import os
import environ
import pymysql
import datetime
import re
import boto3
import xml.etree.ElementTree as ET
import requests
import json
import time

from library import debug, inventory


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"
FEEDDIR = f"{FILEDIR}/feed/DecoratorsBestSA.xml"

PROCESS = "SA Feed"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "feed" in options['functions']:
            while True:
                processor.feed()
                processor.upload()
                print("Finished Process. Waiting for Next run")
                time.sleep(86400 * 3)

        if "main" in options['functions']:
            processor.followup()
            processor.reward()


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)
        self.s3 = boto3.client('s3', aws_access_key_id=env(
            'aws_access_key'), aws_secret_access_key=env('aws_secret_key'))
        self.bucket = 'decoratorsbestimages'

        self.api_url = f"https://decoratorsbest.myshopify.com/admin/api/{env('shopify_api_version')}"
        self.api_header = {
            'X-Shopify-Access-Token': env('shopify_order_token')}

    def __del__(self):
        self.con.close()

    def fmt(self, s):
        if s != None and s != "":
            allowedCharaters = [" ", ",", ".", "'", "\"", "*",
                                "(", ")", "$", "&", ">", "-", "=", "+", "/", "!", "%", "^", "@", ":", ";", "{", "}", "[", "]", "?"]

            cleaned = [character for character in s if character.isalnum()
                       or character in allowedCharaters]

            return "".join(cleaned)
        else:
            return ""

    def feed(self):
        debug.debug(PROCESS, 0, f"Started running {PROCESS} processor.")

        if os.path.isfile(FEEDDIR):
            os.remove(FEEDDIR)

        csr = self.con.cursor()
        csr.execute("""
            SELECT 
                P.SKU,
                P.Title AS PName,
                P.Handle,
                PI.ImageURL,
                M.Name as Manufacturer,
                PV.Price * PV.MinimumQuantity AS Price,
                T.Name AS Type,
                (SELECT Name FROM Tag T JOIN ProductTag PT on T.TagID = PT.TagID WHERE T.Published=1 AND T.Deleted=0 AND T.ParentTagID=2 AND PT.SKU = P.SKU LIMIT 1) AS DesignStyle,
                (SELECT Name FROM Tag T JOIN ProductTag PT on T.TagID = PT.TagID WHERE T.Published=1 AND T.Deleted=0 AND T.ParentTagID=3 AND PT.SKU = P.SKU LIMIT 1) AS Color,
                PV.Weight,
                PV.GTIN,
                P.ManufacturerPartNumber,
                P.BodyHTML,
                PV.Cost,
                PV.Price as SPrice,
                P.ProductID,
                P.Pattern,
                PV.MinimumQuantity
            FROM Product P
                LEFT JOIN ProductImage PI ON P.ProductID = PI.ProductID
                LEFT JOIN ProductVariant PV ON P.ProductID = PV.ProductID
                LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU
                LEFT JOIN Manufacturer M ON M.ManufacturerID = PM.ManufacturerID
                LEFT JOIN Type T ON P.ProductTypeID = T.TypeID
            WHERE PI.ImageIndex = 1
                AND M.Published=1
                AND P.Published = 1
                AND P.ManufacturerPartNumber <> ''
                AND PV.IsDefault=1
                AND PV.Published=1
                AND PV.Cost != 0
            """)

        products = csr.fetchall()
        csr.close()

        total = len(products)
        skiped = 0

        root = ET.Element("products")

        for index, row in enumerate(products):
            sku = self.fmt(str(row[0]))
            pName = self.fmt(str(row[1]).title())
            handle = str(row[2])
            imageURL = str(row[3])
            gtin = row[10]
            mpn = self.fmt(str(row[11]))
            bodyHTML = str(row[12])
            productID = str(row[15])

            # Refine Information
            title = f"{pName} - {sku}"

            desc = self.fmt(bodyHTML.replace(
                "<br />", "").replace("<br/>", " ").replace("<br>", " "))
            if not desc:
                desc = title
            ##################

            item = ET.SubElement(root, "product")
            item.set("id", f"{productID}")

            ET.SubElement(item, "name").text = f"{title}"
            ET.SubElement(item, "description").text = f"{desc}"
            ET.SubElement(
                item, "url").text = f"https://www.decoratorsbest.com/products/{handle}"
            ET.SubElement(item, "image").text = f"{imageURL}"
            ET.SubElement(item, "mpn").text = f"{mpn}"
            ET.SubElement(item, "sku").text = f"{sku}"
            ET.SubElement(item, "upc").text = ""
            ET.SubElement(item, "gtin").text = f"{gtin}"
            ET.SubElement(item, "ean").text = ""
            ET.SubElement(item, "isbn").text = ""
            ET.SubElement(item, "code").text = ""

            debug.debug(
                PROCESS, 0, f"{index}/{total}: Success for SKU {sku}. Skiped {skiped} SKUs")

        tree = ET.ElementTree(root)
        tree.write(FEEDDIR, encoding="UTF-8", xml_declaration=True)

        return (total, skiped)

    def upload(self):
        self.s3.upload_file(FEEDDIR, self.bucket, "DecoratorsBestSA.xml", ExtraArgs={
                            'ACL': 'public-read'})
        debug.debug(
            PROCESS, 0, 'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/DecoratorsBestSA.xml')

    def followup(self):
        today = datetime.date.today()

        start = today - datetime.timedelta(days=7)
        to = today - datetime.timedelta(days=6)
        followup = today + datetime.timedelta(days=3)

        s = requests.Session()

        nextLink = f"{self.api_url}/orders.json?status=any&fulfillment_status=shipped&updated_at_min={start}&updated_at_max={to}"

        page = 0
        while nextLink != "":
            page += 1
            res = s.get(nextLink, headers=self.api_header)

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

                debug.debug(
                    PROCESS, 0, f"Requesting Review for PO: {orderNumber}, Customer: {customerName}, Email: {email}")

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
