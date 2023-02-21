import environ
from django.core.management.base import BaseCommand

import json
import pymysql
import requests
import csv
import os
import codecs
import time
import paramiko
from ftplib import FTP
import datetime
import urllib.request

from library import common, debug

debug = debug.debug
sq = common.sq

env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

api_version = env('shopify_api_version')
shopify_api_key = env('shopify_order_key')
shopify_api_password = env('shopify_order_sec')

api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
    shopify_api_key, shopify_api_password)


FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SHOPIFY_API_URL = "https://decoratorsbest.myshopify.com/admin/api/{}".format(
    env('shopify_api_version'))
SHOPIFY_ORDER_API_HEADER = {
    'X-Shopify-Access-Token': env('shopify_order_token'),
    'Content-Type': 'application/json'
}


class Command(BaseCommand):
    help = 'Build Seabrook Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "main" in options['functions']:
            while True:
                self.manual()
                self.schumacherTracking()
                self.kravetTracking()

                print("Finished Get Tracking, Waiting for next Run")
                time.sleep(3600)

        if "manual" in options['functions']:
            self.manual()

        if "schumacherTracking" in options['functions']:
            self.schumacherTracking()

        if "kravetTracking" in options['functions']:
            self.kravetTracking()

    def manual(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        trackingFile = ""
        files = os.listdir(FILEDIR + "/files/tracking/")
        for file in files:
            trackingFile = FILEDIR + "/files/tracking/" + file
            break

        if trackingFile == "":
            return

        f = open(trackingFile, "rb")
        cr = csv.reader(codecs.iterdecode(f, encoding="ISO-8859-1"))

        for row in cr:
            try:
                trackingNumber = row[0]
                if "FABRICUT" in row[4]:
                    brand = "Fabricut"
                    orderNumber = row[1].split("|")[1]
                elif "BREWSTER" in row[4]:
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
                print(e)
                continue

            try:
                self.addTracking(brand, orderNumber, trackingNumber)
            except Exception as e:
                print(e)
                debug("Tracking", 1, "Failed Adding Tracking for Order: {}".format(
                    orderNumber, brand, trackingNumber))

        f.close()
        os.remove(trackingFile)

    def schumacherTracking(self):
        host = "34.203.121.151"
        port = 22
        username = "schumacher"
        password = "Sch123Decbest!"

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
        except:
            debug("Schumacher EDI", 2, "Connection to Schumacher FTP Server Failed")
            return False

        files = sftp.listdir('../EDI/EDI_to_DB')
        for file in files:
            if "ASN" in file:
                sftp.get("../EDI/EDI_to_DB/{}".format(file),
                         FILEDIR + '/files/EDI/Schumacher/{}'.format(file))
                sftp.remove("../EDI/EDI_to_DB/{}".format(file))

        sftp.close()

        for file in files:
            if "ASN" not in file:
                continue

            f = open(FILEDIR + "/files/EDI/Schumacher/{}".format(file), "rt")
            cr = csv.reader(f)

            for row in cr:
                if str(row[0]).strip() == "Customer PO Number":
                    continue

                try:
                    PONumber = str(row[0]).strip()
                except Exception as e:
                    print(e)
                    continue

                try:
                    tracking = str(row[4]).strip()
                except Exception as e:
                    print(e)
                    continue

                print(PONumber, tracking)

                try:
                    self.addTracking("Schumacher", PONumber, tracking)
                except Exception as e:
                    print(e)
                    debug("Tracking", 1, "Failed Adding Tracking for Order: {}".format(
                        PONumber, "Schumacher", tracking))

    def kravetTracking(self):
        ftp = FTP("file.kravet.com")
        ftp.login('decbest', 'mArker999')
        ftp.cwd("EDI TO ALL DECOR")

        files = ftp.nlst()
        for file in files:
            if "ShipExt" in file:
                pass
            else:
                continue

            print(file)

            try:
                ftp.retrbinary("RETR {}".format(file), open(
                    FILEDIR + '/files/EDI/Kravet/' + file, 'wb').write)
                ftp.delete(file)
            except Exception as e:
                print(e)
                continue

            f = open(FILEDIR + '/files/EDI/Kravet/' + file, "r")
            cr = csv.reader(f)
            for row in cr:
                if "Customer PO" in row[0]:
                    continue

                po = str(row[0]).strip()
                tracking = str(row[7]).strip()

                print(po, tracking)

                try:
                    self.addTracking("Kravet", po, tracking)
                except Exception as e:
                    print(e)
                    debug("Tracking", 1, "Failed Adding Tracking for Order: {}".format(
                        po, "Kravet", tracking))

        ftp.close()

    def addTracking(self, brand, orderNumber, tracking):
        tracking = str(tracking).replace("'", "")
        debug("Tracking", 0, "Adding Tracking for Order: {}, Brand: {}, Tracking Number: {}".format(
            orderNumber, brand, tracking))

        s = requests.Session()

        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("SELECT NULL FROM OrderTracking WHERE OrderNumber = {} AND Brand = '{}' AND TrackingNumber = '{}'".format(
            orderNumber, brand, tracking))
        if csr.fetchone() != None:
            debug("Tracking", 1, "Tracking info for Order #{} is already exist".format(
                orderNumber))
            return

        vids = []
        csr.execute("""SELECT VariantID, Email
                        FROM Orders O 
                        LEFT JOIN Orders_ShoppingCart OS ON O.ShopifyOrderID = OS.ShopifyOrderID 
                        LEFT JOIN ProductManufacturer PM ON OS.OrderedProductSKU = PM.SKU 
                        LEFT JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                        WHERE O.OrderNumber = {} AND M.Brand = '{}'""".format(orderNumber, brand))
        for row in csr.fetchall():
            vids.append(row[0])

        r = s.get("{}/orders.json?status=any&name={}&fields=id,line_items".format(
            SHOPIFY_API_URL, orderNumber), headers=SHOPIFY_ORDER_API_HEADER)
        j = json.loads(r.text)

        if j['orders'] == None or len(j['orders']) == 0:
            return

        oObj = j['orders'][0]
        oid = oObj['id']
        items = []
        for iObj in oObj['line_items']:
            if iObj['variant_id'] in vids:
                items.append({'id': iObj['id']})

        tObj = {}
        tObj['location_id'] = int(14712864835)
        tObj['line_items'] = items
        tObj['tracking_numbers'] = [tracking]
        tObj['tracking_url'] = "https://www.ups.com/WebTracking?loc=en_US&requester=ST&trackNums={}/trackdetails".format(
            tracking)

        r2 = s.post(api_url + "/admin/api/{}/orders/{}/fulfillments.json".format(
            api_version, oid), json={'fulfillment': tObj})

        if "id" in r2.text:
            debug("Tracking", 0, "{} Order #{} has been fullfilled successfully".format(
                brand, orderNumber))
        else:
            debug("Tracking", 1, "{} Order #{} has been already fullfilled".format(
                brand, orderNumber))

        csr.execute("CALL AddToOrderTracking ({}, {}, {})".format(
            orderNumber, sq(brand), sq(tracking)))
        con.commit()

        csr.close()
        con.close()

    def sq(x):
        return "N'" + x.replace("'", "''") + "'"
