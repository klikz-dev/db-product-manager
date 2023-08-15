from django.core.management.base import BaseCommand

import os
import pymysql
import datetime
import pytz
from ftplib import FTP
import urllib.request
import requests
import csv

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

    def main(self):
        s = requests.Session()

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
                    CONCAT('DecoratorsBest/', O.ShippingLastName) AS PackInstruction,
                    O.ShopifyOrderID,
                    O.ShippingPhone

                    FROM Orders_ShoppingCart OS JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Orders O ON OS.ShopifyOrderID = O.ShopifyOrderID

                    WHERE PV.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Kravet')
                        AND O.OrderNumber > (SELECT KravetEDI FROM PORecord)
                        AND O.Status NOT LIKE '%Hold%'
                        AND O.Status NOT LIKE '%Back Order%'
                        AND O.Status NOT LIKE '%Cancel%'
                        AND O.Status NOT LIKE '%Processed%'
                        AND O.Status NOT LIKE '%CFA%'
                        AND O.Status NOT LIKE '%Call Manufacturer%'
                        AND O.Status NOT LIKE '%Kravet EDI%'

                    ORDER BY O.OrderNumber ASC""")

            rows = csr.fetchall()
            maxPO = -1

            now = datetime.datetime.now(pytz.timezone("America/New_York"))
            date = now.strftime("%Y%m%d")
            ctime = now.strftime("%H%M%S")
            filename = "KravetEDI_{}_{}.xml".format(date, ctime)

            f = open(FILEDIR + '/files/EDI/Kravet/' + filename, 'w')
            f.write("<KFI_ORDER_LINE_XML><LIST_G_HDR>")

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
                county = row[8]
                postal = str(row[9])
                country = row[10]
                shippingMethod = row[11]
                shipInstruction = str(row[12]).replace("\n", " ")
                packInstruction = str(row[13]).replace("\n", " ")
                phone = str(row[15]).replace(
                    "+1", "").replace("-", "").replace(" ", "")

                instructions = ""
                if shipInstruction != "" and shipInstruction != None:
                    instructions = "Ship Instruction: {}".format(
                        shipInstruction)
                if packInstruction != "" and packInstruction != None:
                    instructions += "Pack Instruction: {}".format(
                        packInstruction)

                # Full Address
                fullAddress = address1
                if address2:
                    fullAddress = f"{fullAddress}, {address2}"
                if suite:
                    fullAddress = f"{fullAddress}, {suite}"

                # Generate XML Content
                content = "<G_HDR>"
                content += "<HDR_CUSTOMER_PO>" + \
                    common.fmt(orderNumber) + "</HDR_CUSTOMER_PO>"
                content += "<CREATION_DATE>" + \
                    common.fmt(orderDate) + "</CREATION_DATE>"
                content += "<ACCOUNT_NUMBER>10180317</ACCOUNT_NUMBER>"
                content += "<CONTACT_NAME>""</CONTACT_NAME>"
                content += "<CONT_PHONE_NUMBER>" + \
                    common.fmt(phone) + "</CONT_PHONE_NUMBER>"

                content += "<HDR_SHIP_ADDRESS1>" + \
                    common.fmt(name) + "</HDR_SHIP_ADDRESS1>"
                content += "<HDR_SHIP_ADDRESS2>" + \
                    common.fmt(fullAddress) + "</HDR_SHIP_ADDRESS2>"

                content += "<HDR_SHIP_CITY>" + \
                    common.fmt(city) + "</HDR_SHIP_CITY>"
                content += "<HDR_SHIP_STATE>" + \
                    common.fmt(state) + "</HDR_SHIP_STATE>"
                content += "<HDR_SHIP_COUNTY>" + county + "</HDR_SHIP_COUNTY>"

                if postal.find('-') != -1:
                    content += "<HDR_SHIP_ZIP>" + \
                        common.fmt(postal[0: postal.find('-')]
                                   ) + "</HDR_SHIP_ZIP>"
                else:
                    content += "<HDR_SHIP_ZIP>" + \
                        common.fmt(postal) + "</HDR_SHIP_ZIP>"

                content += "<HDR_SHIP_COUNTRY>" + \
                    common.fmt(country) + "</HDR_SHIP_COUNTRY>"

                content += "<HDR_SHIP_METHOD>" + \
                    common.fmt(shippingMethod) + "</HDR_SHIP_METHOD>"

                if shipInstruction == None:
                    content += "<HDR_SHIP_INSTRUCTIONS></HDR_SHIP_INSTRUCTIONS>"
                else:
                    content += "<HDR_SHIP_INSTRUCTIONS>" + \
                        common.fmt(shipInstruction) + \
                        "</HDR_SHIP_INSTRUCTIONS>"

                content += "<HDR_PACK_INSTRUCTIONS>" + \
                    common.fmt(packInstruction) + "</HDR_PACK_INSTRUCTIONS>"

                content += "<ACK_EMAIL_ADDRESS>ORDERS@DECORATORSBEST.COM</ACK_EMAIL_ADDRESS>"

                content += "<LIST_G_LINES>"

                # Line Items
                csr.execute("""SELECT P.ManufacturerPartNumber AS Item, CASE WHEN PV.Name LIKE '%Sample - %' THEN 'Sample' ELSE REPLACE(PV.Pricing, 'Per ', '') END AS UOM, OS.Quantity, P.SKU
                            FROM Orders O JOIN Orders_ShoppingCart OS ON O.ShopifyOrderID = OS.ShopifyOrderID JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Product P ON P.ProductID = PV.ProductID
                            WHERE PV.SKU IN (SELECT SKU
                                                FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                                                WHERE M.Brand = 'Kravet')
                            AND O.OrderNumber = {}""".format(orderNumber))
                items = csr.fetchall()

                lineNumber = 0
                for item in items:
                    mpn = item[0]
                    uom = item[1]
                    qty = item[2]
                    sku = item[3]

                    ack_email_address = 'purchasing@decoratorsbest.com'

                    if "Sample" == uom:
                        mpn = mpn[0: -2] + ".M"
                        uom = "EA"
                        ack_email_address = 'memos@decoratorsbest.com'
                    elif "Yard" == uom:
                        uom = "YD"
                    elif "Roll" == uom:
                        uom = "RL"
                    elif "Square Foot" == uom:
                        uom = "SQF"
                    else:
                        uom = "EA"

                    tmp = mpn.split(".")
                    r = s.get("http://www.e-designtrade.com/api/stock_check.asp?user=DBEST767&password=b1028H47kkr&pattern={}&color={}&identifier={}&quantity={}".format(
                        tmp[0], tmp[1], tmp[2], qty))

                    if uom != "Sample" and "<INVENTORY_STATUS>M</INVENTORY_STATUS>" in r.text or "<INVENTORY_STATUS>N</INVENTORY_STATUS>" in r.text or "<TRANSACTION_STATUS>Invalid Item</TRANSACTION_STATUS>" in r.text:
                        if "<INVENTORY_STATUS>M</INVENTORY_STATUS>" in r.text:
                            msg = "will be IN MULTIPLE PIECES"
                        elif "<INVENTORY_STATUS>N</INVENTORY_STATUS>" in r.text:
                            msg = "is OUT OF STOCK"
                        elif "<TRANSACTION_STATUS>Invalid Item</TRANSACTION_STATUS>" in r.text:
                            msg = "is discontinued"

                        debug("Kravet EDI", 1,
                              "PO #{} - {} {}".format(orderNumber, mpn, msg))

                        emailer.send_email_html("Kravet EDI",
                                                ack_email_address,
                                                "PO #{} needs manual process (Kravet)".format(
                                                    orderNumber),
                                                "Hi, <br><br>PO #{} - {} {} {}. \
                                                Please process it manually. <br><br>Best, <br>Murrell".format(orderNumber, qty, uom, msg))

                        csr.execute(
                            "SELECT ReferenceNumber FROM Orders WHERE OrderNumber = {}".format(orderNumber))
                        note = (csr.fetchone())[0]
                        if note == "None" or note == None:
                            note = ""
                        newNote = "{}\nNote:\n{} {} of {} {}.".format(
                            note, qty, uom, sku, msg)

                        csr.execute("UPDATE Orders SET ReferenceNumber = {} WHERE OrderNumber = {}".format(
                            sq(newNote), orderNumber))
                        con.commit()

                        continue

                    lineNumber += 1

                    content += "<G_LINES>"
                    content += "<LINE_CUSTOMER_PO>" + \
                        common.fmt(orderNumber) + "</LINE_CUSTOMER_PO>"
                    content += "<PO_LINE_NUMBER>" + \
                        common.fmt(lineNumber) + "</PO_LINE_NUMBER>"
                    content += "<ORDERED_ITEM>" + \
                        common.fmt(mpn) + "</ORDERED_ITEM>"
                    content += "<ORDER_QUANTITY_UOM>" + \
                        common.fmt(uom) + "</ORDER_QUANTITY_UOM>"
                    content += "<ORDERED_QUANTITY>" + \
                        common.fmt(qty) + "</ORDERED_QUANTITY>"
                    content += "<LINE_SHIP_ADDRESS1></LINE_SHIP_ADDRESS1>"
                    content += "<LINE_SHIP_ADDRESS2></LINE_SHIP_ADDRESS2>"
                    content += "<LINE_SHIP_CITY></LINE_SHIP_CITY>"
                    content += "<LINE_SHIP_STATE></LINE_SHIP_STATE>"
                    content += "<LINE_SHIP_COUNTY></LINE_SHIP_COUNTY>"
                    content += "<LINE_SHIP_ZIP></LINE_SHIP_ZIP>"
                    content += "<LINE_SHIP_COUNTRY></LINE_SHIP_COUNTRY>"
                    content += "<LINE_SHIP_METHOD></LINE_SHIP_METHOD>"
                    content += "<LINE_SHIP_INSTRUCTIONS></LINE_SHIP_INSTRUCTIONS>"
                    content += "<LINE_PACK_INSTRUCTIONS></LINE_PACK_INSTRUCTIONS>"
                    content += "</G_LINES>"

                content += "</LIST_G_LINES></G_HDR>"

                f.write(content)

                csr.execute(
                    "SELECT Status FROM Orders WHERE OrderNumber = {}".format(orderNumber))
                extStatus = (csr.fetchone())[0]
                if extStatus == "New" or extStatus == None or extStatus == "":
                    newStatus = "Kravet EDI"
                else:
                    newStatus = extStatus + ", Kravet EDI"
                csr.execute("UPDATE Orders SET Status = {} WHERE OrderNumber = {}".format(
                    sq(newStatus), orderNumber))
                con.commit()

                maxPO = orderNumber

            f.write("</LIST_G_HDR></KFI_ORDER_LINE_XML>")
            f.close()

            if maxPO != -1:
                csr.execute(
                    "UPDATE PORecord SET KravetEDI = {}".format(maxPO))
                con.commit()

            csr.close()
            con.close()

            self.upload(filename)
        except Exception as e:
            debug("Kravet EDI", 2,
                  "Kravet EDI ERROR: {}".format(str(e)))

    def upload(self, filename):
        now = datetime.datetime.now(pytz.timezone("America/New_York"))
        date = now.strftime("%Y%m%d")
        ctime = now.strftime("%H%M%S")

        ftp = FTP("file.kravet.com")
        ftp.login('decbest', 'mArker999')
        ftp.cwd("EDI FROM ALL DECOR/Live")

        try:
            f = open(FILEDIR + '/files/EDI/Kravet/' + filename, 'rb')
            ftp.storbinary('STOR KravetEDI_{}_{}.xml'.format(date, ctime), f)
            f.close()
        except Exception as e:
            print(e)
            debug("Kravet EDI", 2, "Error uploading Kravet PO {}".format(filename))

        ftp.close()

        debug("Kravet EDI", 0, "EDI uploaded {}".format(filename))

    def getRef(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        ftp = FTP("file.kravet.com")
        ftp.login('decbest', 'mArker999')
        ftp.cwd("EDI TO ALL DECOR/ACK")

        todayMark = datetime.date.today().strftime("%d%b%Y").upper()

        files = ftp.nlst()
        for file in files:
            if "Kravet_AckExt_" + todayMark in file:
                urllib.request.urlretrieve("ftp://decbest:mArker999@file.kravet.com/EDI TO ALL DECOR/ACK/" +
                                           file, FILEDIR + '/files/EDI/Kravet/' + file)

                f = open(FILEDIR + '/files/EDI/Kravet/' + file, "r")
                cr = csv.reader(f)
                for row in cr:
                    if "Customer PO Number" == row[0]:
                        continue

                    po = str(row[0]).strip()
                    ref = str(row[2]).strip()
                    print(po, ref)

                    try:
                        csr.execute(
                            "SELECT ReferenceNumber FROM Orders WHERE OrderNumber = {}".format(po))
                        currentRef = str((csr.fetchone())[0])

                        if currentRef == "None":
                            currentRef = ""
                        if ref not in currentRef:
                            newRef = "{}\nKravet EDI: {}".format(
                                currentRef, ref)

                            csr.execute("UPDATE Orders SET ReferenceNumber = {} WHERE OrderNumber = {}".format(
                                sq(newRef), po))
                            con.commit()
                    except Exception as e:
                        print(e)
                        continue

        ftp.close()

        csr.close()
        con.close()
