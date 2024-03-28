from ftplib import FTP
import json
from django.core.management.base import BaseCommand

import os
import pymysql
import datetime
import pytz
import csv
import urllib.request

import requests

from library import debug, common, emailer

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'EDI commands'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "main" in options['functions']:
            self.main()

        if "getRef" in options['functions']:
            self.getRef()

        if "uploadAll" in options['functions']:
            self.uploadAll()

    def main(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        orderRows = self.fetchOrders('Order')
        sampleRows = self.fetchOrders('Sample')

        maxPOOrder = self.genXMLbyType(orderRows, 'Order')
        debug(
            "York EDI", 0, "York Orders have been submitted succssfully. Max PO: {}".format(maxPOOrder))

        maxPOSample = self.genXMLbyType(sampleRows, 'Sample')
        debug(
            "York EDI", 0, "York Samples have been submitted succssfully. Max PO: {}".format(maxPOSample))

        maxPO = maxPOOrder
        if maxPOSample > maxPOOrder:
            maxPO = maxPOSample

        if maxPO != -1:
            csr.execute(
                "UPDATE PORecord SET YorkEDI = {}".format(maxPO))
            con.commit()

        csr.close()
        con.close()

    def fetchOrders(self, type):
        try:
            con = pymysql.connect(host=db_host, user=db_username,
                                  passwd=db_password, db=db_name, connect_timeout=5)
            csr = con.cursor()

            csr.execute("""SELECT DISTINCT
                    O.OrderNumber AS OrderNumber, 
                    DATE_FORMAT(O.CreatedAt, '%d-%b-%y') AS OrderDate, 
                    CONCAT(O.ShippingFirstName, ' ', O.ShippingLastName) AS Name,
                    O.ShippingAddress1 AS Address1,
                    O.ShippingAddress2 AS Address2,
                    O.ShippingCompany AS Suite,
                    O.ShippingCity AS City,
                    O.ShippingState AS State,
                    '' AS County,
                    O.ShippingZip AS Zip,
                    CASE
                        WHEN O.ShippingCountry = 'United States' THEN 'US'
                        WHEN O.ShippingCountry = 'Canada' THEN 'CA'
                        WHEN O.ShippingCountry = 'Australia' THEN 'AU'
                        WHEN O.ShippingCountry = 'United Kingdom' THEN 'UK'
                        WHEN O.ShippingCountry = 'Finland' THEN 'FI'
                        WHEN O.ShippingCountry = 'Egypt' THEN 'EG'
                        WHEN O.ShippingCountry = 'China' THEN 'CN'
                        WHEN O.ShippingCountry = 'France' THEN 'FR'
                        WHEN O.ShippingCountry = 'Germany' THEN 'DE'
                        WHEN O.ShippingCountry = 'Mexico' THEN 'MX'
                        WHEN O.ShippingCountry = 'Russia' THEN 'RU'
                        WHEN O.ShippingCountry = 'Ireland' THEN 'IE'
                        WHEN O.ShippingCountry = 'Greece' THEN 'GR'
                        ELSE O.ShippingCountry
                    END AS Country,

                    CASE
                        WHEN O.ShippingMethod LIKE '%2nd Day%' THEN '2nd Day'
                        WHEN O.ShippingMethod LIKE '%2-day%' THEN '2nd Day'
                        WHEN O.ShippingMethod LIKE '%Overnight%' THEN 'Overnight'
                        WHEN O.ShippingMethod LIKE '%Next Day%' THEN 'Overnight'
                    ELSE 'Ground'
                    END AS ShippingMethod,

                    O.OrderNote AS ShipInstruction,
                    CONCAT('DecoratorsBest/', O.ShippingLastName) AS PackInstruction/*,
                    CAST(O.PaymentMethod AS nvarchar(max)) AS PaymentMethod,
                    CAST(O.Notes AS nvarchar(max)) AS Notes*/,
                    O.ShopifyOrderID,
                    O.ShippingPhone

                    FROM Orders_ShoppingCart OS JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Orders O ON OS.ShopifyOrderID = O.ShopifyOrderID

                    WHERE PV.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'York')
                        AND O.OrderNumber > (SELECT YorkEDI FROM PORecord)
                        AND O.Status NOT LIKE '%Hold%'
                        AND O.Status NOT LIKE '%Back Order%'
                        AND O.Status NOT LIKE '%Cancel%'
                        AND O.Status NOT LIKE '%Processed%'
                        AND O.Status NOT LIKE '%CFA%'
                        AND O.Status NOT LIKE '%Call Manufacturer%'
                        AND O.Status NOT LIKE '%York EDI%'

                        AND O.OrderType LIKE '%{}%'

                    ORDER BY O.OrderNumber ASC""".format(type))

            rows = csr.fetchall()
            csr.close()
            con.close()

            return rows

        except Exception as e:
            debug(
                "York EDI", 2, "York EDI ERROR: Failed Fetching orders. Error: {}".format(str(e)))

            csr.close()
            con.close()

            return None

    def genXMLbyType(self, rows, type):
        try:
            con = pymysql.connect(host=db_host, user=db_username,
                                  passwd=db_password, db=db_name, connect_timeout=5)
            csr = con.cursor()

            now = datetime.datetime.now(pytz.timezone("America/New_York"))
            date = now.strftime("%Y%m%d")
            ctime = now.strftime("%H%M%S")

            filename = "PO_{}_{}_{}.xml".format(date, ctime, type)

            f = open(FILEDIR + '/files/EDI/York/' + filename, 'w')
            f.write("<KFI_ORDER_LINE_XML><LIST_G_HDR>")

            maxPO = -1

            for row in rows:
                orderNumber = row[0]
                orderDate = row[1]

                name = row[2]

                address1 = row[3].replace("\n", "")
                address2 = row[4]
                if "," in address1:
                    address2 = str(address1).split(",")[1]
                    address1 = str(address1).split(",")[0]

                suite = row[5]
                city = row[6]
                state = row[7]
                country = row[8]
                postal = str(row[9])
                country = row[10]
                shippingMethod = row[11]
                shipInstruction = row[12]
                packInstruction = row[13]
                phone = row[15]

                if not self.validate(orderNumber):
                    continue

                line = ""

                line += "<G_HDR>"

                line += "<HDR_CUSTOMER_PO>" + \
                    self.fmt(orderNumber) + "</HDR_CUSTOMER_PO>"

                line += "<CREATION_DATE>" + \
                    self.fmt(orderDate) + "</CREATION_DATE>"

                line += "<ACCOUNT_NUMBER>27983</ACCOUNT_NUMBER>"

                line += "<CONTACT_NAME>" + \
                    self.fmt(name) + "</CONTACT_NAME>"

                line += "<CONT_PHONE_NUMBER>" + \
                    self.fmt(phone) + "</CONT_PHONE_NUMBER>"

                line += "<HDR_SHIP_ADDRESS1>" + \
                    self.fmt(address1) + "</HDR_SHIP_ADDRESS1>"

                line += "<HDR_SHIP_ADDRESS2>"
                if address2 != "" and address2 != None:
                    line += self.fmt(address2)
                if suite != "" and suite != None:
                    line += ", " + self.fmt(suite)
                line += "</HDR_SHIP_ADDRESS2>"

                line += "<HDR_SHIP_CITY>" + self.fmt(city) + "</HDR_SHIP_CITY>"

                line += "<HDR_SHIP_STATE>" + \
                    self.fmt(state) + "</HDR_SHIP_STATE>"

                line += "<HDR_SHIP_COUNTY></HDR_SHIP_COUNTY>"

                if postal.find('-') != -1:
                    line += "<HDR_SHIP_ZIP>" + \
                        self.fmt(postal[0: postal.find('-')]) + \
                        "</HDR_SHIP_ZIP>"
                else:
                    line += "<HDR_SHIP_ZIP>" + \
                        self.fmt(postal) + "</HDR_SHIP_ZIP>"

                line += "<HDR_SHIP_COUNTRY>" + \
                    self.fmt(country) + "</HDR_SHIP_COUNTRY>"

                line += "<HDR_SHIP_METHOD>" + \
                    self.fmt(shippingMethod) + "</HDR_SHIP_METHOD>"

                if shipInstruction == None:
                    line += "<HDR_SHIP_INSTRUCTIONS></HDR_SHIP_INSTRUCTIONS>"
                else:
                    line += "<HDR_SHIP_INSTRUCTIONS>" + \
                        self.fmt(shipInstruction) + "</HDR_SHIP_INSTRUCTIONS>"

                line += "<HDR_PACK_INSTRUCTIONS>" + \
                    self.fmt(packInstruction) + "</HDR_PACK_INSTRUCTIONS>"

                if type == "Sample":
                    line += "<ACK_EMAIL_ADDRESS>SAMPLES@DECORATORSBEST.COM</ACK_EMAIL_ADDRESS>"
                else:
                    line += "<ACK_EMAIL_ADDRESS>ORDERS@DECORATORSBEST.COM</ACK_EMAIL_ADDRESS>"

                line += "<LIST_G_LINES>" + \
                    self.detail(orderNumber, type) + "</LIST_G_LINES>"

                line += "</G_HDR>"

                f.write(line)

                maxPO = orderNumber

                csr.execute(
                    "SELECT Status FROM Orders WHERE OrderNumber = {}".format(orderNumber))
                extStatus = (csr.fetchone())[0]
                if extStatus == "New":
                    newStatus = "York EDI"
                else:
                    newStatus = extStatus + ", York EDI"
                csr.execute("UPDATE Orders SET Status = {} WHERE OrderNumber = {}".format(
                    sq(newStatus), orderNumber))
                con.commit()

            f.write("</LIST_G_HDR></KFI_ORDER_LINE_XML>")
            f.close()

        except Exception as e:
            debug(
                "York EDI", 2, "York EDI ERROR: Failed generating PO file. Error: {}".format(str(e)))
            return -1

        csr.close()
        con.close()

        try:
            self.upload(filename)
        except:
            debug(
                "York EDI", 2, "York EDI ERROR: File Upload failed: {}".format(filename))

        return maxPO

    def detail(self, orderNumber, type):
        rst = ""

        con = pymysql.connect(host=db_host, port=db_port, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""SELECT P.ManufacturerPartNumber AS Item, CASE WHEN PV.Name LIKE '%Sample%' THEN 'Sample' ELSE REPLACE(PV.Pricing, 'Per ', '') END AS UOM, OS.Quantity, P.SKU
                        FROM Orders O JOIN Orders_ShoppingCart OS ON O.ShopifyOrderID = OS.ShopifyOrderID JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Product P ON P.ProductID = PV.ProductID
                        WHERE PV.SKU IN (SELECT SKU
                        FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                        WHERE M.Brand = 'York')
                        AND O.OrderNumber = {}""".format(orderNumber))
        rows = csr.fetchall()
        cnt = 1

        for row in rows:
            mpn = row[0]
            uom = row[1]
            qty = row[2]
            sku = row[3]
            isSample = False

            if "Sample" == uom:
                isSample = True
                mpn += ".M"
                uom = "EA"
            elif "Yard" == uom:
                uom = "YD"
            elif "Roll" == uom:
                uom = "RL"
            elif "Square Foot" == uom:
                uom = "SQF"
            else:
                uom = "EA"

            if isSample:
                if type != "Sample":
                    continue
            else:
                if type != "Order":
                    continue

            if not isSample and not self.check_stock(mpn, qty):
                msg = "is OUT OF STOCK"
                recipient = 'orders@decoratorsbest.com'

                emailer.send_email_html("York EDI",
                                        recipient,
                                        "PO {} need manual process (York)".format(
                                            orderNumber),
                                        "Hi, \n\nPO# {}, {} {} of {} {}. Please contact the client and process it manually only for this item. \n\nBest, \nmurrell".format(orderNumber, qty, uom, sku, msg))

                csr.execute(
                    "SELECT ReferenceNumber FROM Orders WHERE OrderNumber = {}".format(orderNumber))
                note = (csr.fetchone())[0]
                newNote = "{}\nNote:\n{} {} of {} {}.".format(
                    note, qty, uom, sku, msg)

                csr.execute("UPDATE Orders SET ReferenceNumber = {} WHERE OrderNumber = {}".format(
                    sq(newNote), orderNumber))
                con.commit()

                continue

            rst += "<G_LINES>"

            rst += "<LINE_CUSTOMER_PO>" + \
                self.fmt(orderNumber) + "</LINE_CUSTOMER_PO>"

            rst += "<PO_LINE_NUMBER>" + self.fmt(cnt) + "</PO_LINE_NUMBER>"

            rst += "<ORDERED_ITEM>" + self.fmt(mpn) + "</ORDERED_ITEM>"

            rst += "<ORDER_QUANTITY_UOM>" + \
                self.fmt(uom) + "</ORDER_QUANTITY_UOM>"

            rst += "<ORDERED_QUANTITY>" + self.fmt(qty) + "</ORDERED_QUANTITY>"

            rst += "<LINE_SHIP_ADDRESS1></LINE_SHIP_ADDRESS1>"

            rst += "<LINE_SHIP_ADDRESS2></LINE_SHIP_ADDRESS2>"

            rst += "<LINE_SHIP_CITY></LINE_SHIP_CITY>"

            rst += "<LINE_SHIP_STATE></LINE_SHIP_STATE>"

            rst += "<LINE_SHIP_COUNTY></LINE_SHIP_COUNTY>"

            rst += "<LINE_SHIP_ZIP></LINE_SHIP_ZIP>"

            rst += "<LINE_SHIP_COUNTRY></LINE_SHIP_COUNTRY>"

            rst += "<LINE_SHIP_METHOD></LINE_SHIP_METHOD>"

            rst += "<LINE_SHIP_INSTRUCTIONS></LINE_SHIP_INSTRUCTIONS>"

            rst += "<LINE_PACK_INSTRUCTIONS></LINE_PACK_INSTRUCTIONS>"

            rst += "</G_LINES>"

            cnt += 1

        csr.close()
        con.close()

        return rst

    def validate(self, orderNumber):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        # Check Country
        csr.execute(
            "SELECT ShippingCountry, OrderType FROM Orders WHERE OrderNumber = {}".format(orderNumber))
        line = csr.fetchone()

        country = line[0]
        orderType = line[1]

        if "Sample" in orderType:
            recipient = 'memos@decoratorsbest.com'
        else:
            recipient = 'purchasing@decoratorsbest.com'

        if "US" != country and "United States" != country:
            emailer.send_email_html("York EDI",
                                    recipient,
                                    "PO {} need manual process (York)".format(
                                        orderNumber),
                                    "Hi, <br><br>PO# {} has not been processed by York EDI because it's an international order. \
                                    Please process it manually for ALL York items. <br><br>Best, <br>Murrell".format(orderNumber))

            csr.close()
            con.close()
            return False

        # Check Stock
        # stockStatus = True
        # csr.execute("""SELECT P.ManufacturerPartNumber AS Item, CASE WHEN PV.Name LIKE '%Sample%' THEN 'Sample' ELSE REPLACE(PV.Pricing, 'Per ', '') END AS UOM, OS.Quantity, P.SKU
        #                 FROM Orders O JOIN Orders_ShoppingCart OS ON O.ShopifyOrderID = OS.ShopifyOrderID JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Product P ON P.ProductID = PV.ProductID
        #                 WHERE PV.SKU IN (SELECT SKU
        #                                         FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
        #                                         WHERE M.Brand = 'York')
        #                 AND O.OrderNumber = {}""".format(orderNumber))

        # rows = csr.fetchall()
        # for row in rows:
        #     uom = row[1]
        #     qty = row[2]
        #     sku = row[3]
        #     if "Sample" != uom:
        #         csr.execute(
        #             "SELECT Quantity FROM ProductInventory WHERE SKU = '{}'".format(sku))
        #         stockData = csr.fetchone()
        #         if stockData:
        #             stock = stockData[0]
        #         else:
        #             stock = 0

        #         if stock < qty:
        #             stockStatus = False

        # if stockStatus != True:
        #     emailer.send_email_html("York EDI",
        #                             recipient,
        #                             "PO {} need manual process (York)".format(
        #                                 orderNumber),
        #                             "Hi, <br><br>PO# {} has not been processed by York EDI because ALL York items in it have inventory problem. \
        #                             Please contact the client and process it manually for ALL York items. <br><br>Best, <br>Murrell".format(orderNumber))

        #     csr.close()
        #     con.close()
        #     return False

        csr.close()
        con.close()

        return True

    def upload(self, filename):
        try:
            ftp = FTP("mft.getfoundational.com")
            ftp.login('EDYRKWAL_decbest', 'zE6e-26K')
            ftp.cwd("tofdnl")
        except:
            debug("York EDI", 2, "failed FTP server login. PO: {}".format(filename))

        try:
            f = open(FILEDIR + '/files/EDI/York/' + filename, 'rb')
            ftp.storbinary('STOR ' + filename, f)
            f.close()
            print("uploaded EDI XML successfully")
        except:
            print("Error upload EDI XML")

        ftp.close()

        debug("York EDI", 0, "EDI uploaded {}".format(filename))

    def uploadAll(self):
        try:
            ftp = FTP("mft.getfoundational.com")
            ftp.login('EDYRKWAL_decbest', 'zE6e-26K')
            ftp.cwd("tofdnl")
        except:
            debug("York EDI", 2, "failed FTP server login.")

        # files = os.listdir(FILEDIR + "/files/EDI/York/")
        # print(files)

        # Validate upload
        print(ftp.nlst())

        # for filename in files:
        #     try:
        #         f = open(FILEDIR + '/files/EDI/York/' + filename, 'rb')
        #         ftp.storbinary('STOR ' + filename, f)
        #         f.close()
        #         debug("York EDI", 0, "EDI uploaded {}".format(
        #             FILEDIR + '/files/EDI/York/' + filename))
        #     except Exception as e:
        #         print(e)
        #         print("Error upload EDI XML")
        #         continue

        ftp.close()

    def getRef(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        ftp = FTP("mft.getfoundational.com")
        ftp.login('EDYRKWAL_decbest', 'zE6e-26K')
        ftp.cwd("fromfdnl")
        flist = ftp.nlst()

        for fname in flist:
            if fname in "archive":
                continue

            urllib.request.urlretrieve("ftp://EDYRKWAL_decbest:zE6e-26K@mft.getfoundational.com/fromfdnl/" +
                                       fname, FILEDIR + '/files/EDI/York/' + fname)
            ftp.delete(fname)

            f = open(FILEDIR + '/files/EDI/York/' + fname, "r")
            cr = csv.reader(f)

            for row in cr:
                if "Customer PO Number" == row[0]:
                    continue

                try:
                    PONumber = int(str(row[0]).strip())
                except:
                    continue
                refNumber = str(row[2]).strip()

                print(PONumber)

                try:
                    csr.execute(
                        "SELECT ReferenceNumber FROM Orders WHERE OrderNumber = {}".format(PONumber))
                    ref = str((csr.fetchone())[0])

                    if ref == "None":
                        ref = ""

                    if refNumber not in ref:
                        newRef = "{}\nYork EDI: {}".format(ref, refNumber)

                        csr.execute("UPDATE Orders SET ReferenceNumber = {} WHERE OrderNumber = {}".format(
                            sq(newRef), PONumber))
                        con.commit()

                except Exception as e:
                    debug("York EDI", 2, "failed Get Ref numbers.")
                    debug("York EDI", 2, "{}".format(e))
                    continue

        ftp.close()
        csr.close()
        con.close()

    def fmt(self, x):
        return str(x).replace("~", "").replace("!", "").replace("@", "").replace("#", "").replace("$", "").replace("%", "").replace("^", "").replace("&", "").replace("*", "").replace("(", "").replace(")", "").strip().upper()

    def check_stock(self, mpn, amount):
        s = requests.Session()
        rs = s.get("http://www.yorkwall.com/CGI-BIN/lansaweb?wam=wapiqty&webrtn=getqty&f(ywcitem)={}+&ml=LANSA:XHTML&part=YWP&lang=ENG".format(mpn))
        js = json.loads(rs.text)
        stock = js["webroutine"]["fields"]["WW3TOTAVL"]["value"]

        return stock >= amount
