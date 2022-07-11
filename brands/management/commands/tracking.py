from django.core.management.base import BaseCommand

import json
import pymysql
import requests
import csv
import os
import codecs
import time

from library import config, common, debug

debug = debug.debug
sq = common.sq

db_host = config.db_endpoint
db_username = config.db_username
db_password = config.db_password
db_name = config.db_name
db_port = config.db_port

api_version = config.shopify_api_version
shopify_api_key = config.shopify_fulfillment_key
shopify_api_password = config.shopify_fulfillment_password

api_url = "https://{}:{}@decoratorsbest.myshopify.com".format(
    shopify_api_key, shopify_api_password)


FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Seabrook Database'

    def handle(self, *args, **options):
        while True:
            self.getTracking()
            print("Finished Get Tracking, Waiting for next Run")
            time.sleep(3600)

    def getTracking(self):
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
                # elif "PINDLER AND PINDLER INC" in row[4]:
                #     brand = "Pindler"
                #     orderNumber = row[1].split("/")[2].replace("PO#", "")
                else:
                    continue
            except:
                continue

            try:
                self.addTracking(brand, orderNumber, trackingNumber)
            except Exception as e:
                print(e)
                debug("Tracking", 1, "Failed Adding Tracking for Order: {}".format(
                    orderNumber, brand, trackingNumber))

        f.close()
        os.remove(trackingFile)

    def addTracking(self, brand, orderNumber, tracking):
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

        r = s.get(
            api_url + '/admin/api/{}/orders.json?status=any&name={}&fields=id,line_items'.format(api_version, orderNumber))
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
