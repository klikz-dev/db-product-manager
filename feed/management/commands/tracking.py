from django.core.management.base import BaseCommand

import os
import environ
import pymysql
import csv
import codecs
import requests
import json
import paramiko
import time
from ftplib import FTP

from library import debug, const, common


FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"


class Command(BaseCommand):
    help = f"Update Tracking"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "main" in options['functions']:
            while True:
                processor.kravet()
                processor.schumacher()
                processor.ups()

                print(
                    f"Finished process. Waiting for next run. Tracking:{options['functions']}")
                time.sleep(3600)

        if "ups" in options['functions']:
            processor.ups()

        if "schumacher" in options['functions']:
            processor.schumacher()

        if "kravet" in options['functions']:
            processor.kravet()


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.shopify_api_url = f"https://decoratorsbest.myshopify.com/admin/api/{env('shopify_api_version')}"
        self.shopify_api_header = {
            'X-Shopify-Access-Token': env('shopify_order_token'),
            'Content-Type': 'application/json'
        }

    def __del__(self):
        self.con.close()

    def ups(self):
        csr = self.con.cursor()

        files = os.listdir(f"{FILEDIR}/tracking/")
        if len(files) == 0:
            return False

        file = f"{FILEDIR}/tracking/{files[0]}"

        f = open(f"{FILEDIR}/tracking/{files[0]}", "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
        for row in cr:
            try:
                trackingNumber = row[0]

                if "BREWSTER" in row[4]:
                    brand = "Brewster"
                    orderNumber = row[1].split("|")[0]
                elif "F SCHUMACHER" in row[4] or "FOLIA-CH" in row[4]:
                    brand = "Schumacher"
                    orderNumber = row[1].split("|")[1]
                elif "CALHOUN OUTBOUND STARK" in row[4]:
                    brand = "Scalamandre"
                    orderNumber = row[1].split("|")[1].split("PO")[1][1:]
                elif "FRANK KASMIR ASSOC" in row[4]:
                    brand = "Kasmir"
                    orderNumber = row[1].split(
                        "/")[2].split("|")[0].replace("PO#", "")
                elif "WALLQUEST" in row[4]:
                    brand = "Seabrook"
                    orderNumber = row[1].split("|")[1]
                elif "J F FABRICS" in row[4]:
                    brand = "JF Fabrics"
                    orderNumber = row[1].split("|")[1]
                elif "PHILLIP JEFFRIES" in row[4]:
                    brand = "Phillip Jeffries"
                    orderNumber = row[1].split("|")[1]
                elif "STOUT BROTHERS" in row[4]:
                    brand = "Stout"
                    orderNumber = row[1].split("|")[1].split("/")[0]
                elif "YORK WALLCOVERINGS" in row[4]:
                    brand = "York"
                    orderNumber = row[1].split("|")[1]
                elif "KRAVET" in row[4]:
                    brand = "Kravet"
                    orderNumber = row[1].split("|")[0]
                elif "SCALAMANDRE" in row[4]:
                    brand = "Scalamandre"
                    orderNumber = row[1].split("|")[1].split("PO")[1][1:]
                elif "PREMIER PRINTS" in row[4]:
                    brand = "Premier Prints"
                    orderNumber = row[1].split("|")[0]
                elif "HERITAGE FABRICS LLC" in row[4]:
                    brand = "Maxwell"
                    referenceNumber = row[1].split(
                        "|")[0].replace("MAXWELL", "")
                    csr.execute(
                        "SELECT OrderNumber FROM Orders WHERE ReferenceNumber Like '%{}%' ORDER BY OrderNumber DESC".format(referenceNumber))
                    orderNumber = str((csr.fetchone())[0])
                elif "PINDLER AND PINDLER" in row[4]:
                    brand = "Pindler"
                    referenceNumber = row[1].split("|")[0]
                    csr.execute(
                        "SELECT OrderNumber FROM Orders WHERE ReferenceNumber Like '%{}%' ORDER BY OrderNumber DESC".format(referenceNumber))
                    orderNumber = str((csr.fetchone())[0])
                else:
                    continue

            except Exception as e:
                debug.debug("Tracking", 1, str(e))

            try:
                self.uploadTracking(
                    brand=brand, orderNumber=orderNumber, trackingNumber=trackingNumber)
            except Exception as e:
                debug.debug("Tracking", 1, str(e))

        f.close()
        os.remove(file)

        csr.close()

    def schumacher(self):
        try:
            transport = paramiko.Transport(
                (const.sftp["Schumacher"]["host"], const.sftp["Schumacher"]["port"]))
            transport.connect(
                username=const.sftp["Schumacher"]["user"], password=const.sftp["Schumacher"]["pass"])
            sftp = paramiko.SFTPClient.from_transport(transport)
        except Exception as e:
            debug.debug("Schumacher", 1,
                        f"Connection to Schumacher SFTP Server Failed. Error: {str(e)}")
            return False

        files = sftp.listdir('../EDI/EDI_to_DB')
        for file in files:
            if "ASN" in file:
                sftp.get(f"../EDI/EDI_to_DB/{file}",
                         f"{FILEDIR}/EDI/Schumacher/ASN/{file}")
                sftp.remove(f"../EDI/EDI_to_DB/{file}")

        for file in files:
            if "ASN" not in file:
                continue

            f = open(f"{FILEDIR}/EDI/Schumacher/ASN/{file}", "rb")
            cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
            for row in cr:
                if row[0] == "Customer PO Number":
                    continue

                PONumber = common.formatText(row[0])
                tracking = common.formatText(row[4])

                try:
                    self.uploadTracking("Schumacher", PONumber, tracking)
                except Exception as e:
                    debug.debug("Tracking", 1, str(e))

        sftp.close()

    def kravet(self):
        ftp = FTP(const.ftp['Kravet']['host'])
        ftp.login(const.ftp['Kravet']['user'], const.ftp['Kravet']['pass'])

        ftp.cwd("EDI TO ALL DECOR")

        files = ftp.nlst()
        for file in files:
            if "ShipExt" not in file:
                continue

            try:
                ftp.retrbinary(f"RETR {file}", open(
                    f"{FILEDIR}/EDI/Kravet/ShipExt/{file}", 'wb').write)
                ftp.delete(file)
            except Exception as e:
                print(e)
                continue

        for file in files:
            if "ShipExt" not in file:
                continue

            f = open(f"{FILEDIR}/EDI/Kravet/ShipExt/{file}", "rb")
            cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))
            for row in cr:
                if "Customer PO" in row[0]:
                    continue

                PONumber = common.formatText(row[0])
                tracking = common.formatText(row[7])

                try:
                    self.uploadTracking("Kravet", PONumber, tracking)
                except Exception as e:
                    debug.debug("Tracking", 1, str(e))

        ftp.close()

    def uploadTracking(self, brand, orderNumber, trackingNumber):
        debug.debug(
            "Tracking", 0, f"Adding {brand} Tracking for Order #{orderNumber}. Tracking: {trackingNumber}")

        csr = self.con.cursor()

        csr.execute(
            f"SELECT NULL FROM OrderTracking WHERE Brand = '{brand}' AND OrderNumber = '{orderNumber}' AND TrackingNumber = '{trackingNumber}'")

        if csr.fetchone() != None:
            debug.debug(
                "Tracking", 1, f"{brand} tracking info for Order #{orderNumber} is already exist")
            return False

        variantIds = []
        csr.execute(f"""SELECT VariantID, Email
                        FROM Orders O 
                        LEFT JOIN Orders_ShoppingCart OS ON O.ShopifyOrderID = OS.ShopifyOrderID 
                        LEFT JOIN ProductManufacturer PM ON OS.OrderedProductSKU = PM.SKU 
                        LEFT JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                        WHERE M.Brand = '{brand}' and O.OrderNumber = '{orderNumber}'""")
        for row in csr.fetchall():
            variantIds.append(row[0])

        # Get Order Id
        response = requests.get(
            f"{self.shopify_api_url}/orders.json?status=any&name={orderNumber}&fields=id,line_items", headers=self.shopify_api_header)
        data = json.loads(response.text)

        if 'orders' not in data.keys() or len(data['orders']) == 0:
            debug.debug("Tracking", 1, f"Order #{orderNumber} does not exist")
            return False

        order = data['orders'][0]
        orderId = order['id']
        ##############

        # Get Fulfillment Order Id
        response = requests.get(
            f"{self.shopify_api_url}/orders/{orderId}/fulfillment_orders.json", headers=self.shopify_api_header)
        data = json.loads(response.text)

        if 'fulfillment_orders' not in data.keys() or len(data['fulfillment_orders']) == 0:
            debug.debug(
                "Tracking", 1, f"Fulfillment Order id for order_id #{orderId} does not exist")
            return False

        fulfillmentOrderId = data['fulfillment_orders'][0]['id']

        lineItems = []
        for lineItem in data['fulfillment_orders'][0]['line_items']:
            if lineItem['variant_id'] in variantIds:
                if common.formatInt(lineItem['fulfillable_quantity']) == 0:
                    continue

                lineItems.append({
                    'id': lineItem['id'],
                    'quantity': lineItem['fulfillable_quantity']
                })

        if len(lineItems) == 0:
            debug.debug(
                "Tracking", 1, f"{brand} Order #{orderNumber} doesn't have items left to fullfill")
        ################

        # Upload tracking to Shopify
        trackingData = {
            "fulfillment": {
                "location_id": '14712864835',
                "tracking_info": {
                    "number": trackingNumber,
                    "url": f"https://www.ups.com/WebTracking?loc=en_US&requester=ST&trackNums={trackingNumber}/trackdetails",
                },
                "line_items_by_fulfillment_order": [{
                    "fulfillment_order_id": fulfillmentOrderId,
                    "fulfillment_order_line_items": lineItems
                }]
            }
        }
        response = requests.post(f"{self.shopify_api_url}/fulfillments.json",
                                 json=trackingData, headers=self.shopify_api_header)
        data = json.loads(response.text)

        if 'errors' in data:
            debug.debug("Tracking", 1, str(data['errors']))
            return False
        else:
            if "fulfillment" in data:
                debug.debug(
                    "Tracking", 0, f"{brand} Order #{orderNumber} has been fullfilled successfully")
            else:
                debug.debug(
                    "Tracking", 1, f"{brand} Order #{orderNumber} has already been fullfilled")
        #################

        # Upload tracking to database
        csr.execute(
            f"CALL AddToOrderTracking ('{orderNumber}', '{brand}', '{trackingNumber}')")
        self.con.commit()
        ##################

        csr.close()
