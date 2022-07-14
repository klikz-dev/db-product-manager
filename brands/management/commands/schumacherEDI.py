from django.core.management.base import BaseCommand

import os
import pymysql
import datetime
import pytz
import csv
import pysftp
import paramiko

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
                        WHEN O.ShippingMethod = 'UPS 2nd Day Air' THEN '2nd Day'
                        WHEN O.ShippingMethod = 'UPS Next Day Air' THEN 'Overnight'
                    ELSE 'Ground'
                    END AS ShippingMethod,

                    O.OrderNote AS ShipInstruction,
                    CONCAT('DecoratorsBest/', O.ShippingLastName) AS PackInstruction/*,
                    CAST(O.PaymentMethod AS nvarchar(max)) AS PaymentMethod,
                    CAST(O.Notes AS nvarchar(max)) AS Notes*/,
                    O.ShopifyOrderID

                    FROM Orders_ShoppingCart OS JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Orders O ON OS.ShopifyOrderID = O.ShopifyOrderID

                    WHERE PV.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Schumacher')
                        AND O.OrderNumber > (SELECT SchumacherEDI FROM PORecord)
                        AND O.Status NOT LIKE '%Hold%'
                        AND O.Status NOT LIKE '%Back Order%'
                        AND O.Status NOT LIKE '%Cancel%'
                        AND O.Status NOT LIKE '%Processed%'
                        AND O.Status NOT LIKE '%CFA%'
                        AND O.Status NOT LIKE '%Call Manufacturer%'
                        AND O.Status NOT LIKE '%Reference#%'
                        AND O.Status NOT LIKE '%Schumacher EDI%'

                    ORDER BY O.OrderNumber ASC""")

            rows = csr.fetchall()
            maxPO = -1

            now = datetime.datetime.now(pytz.timezone("America/New_York"))
            date = now.strftime("%Y%m%d")
            ctime = now.strftime("%H%M%S")
            filename = "PO_{}_{}.csv".format(date, ctime)

            with open(FILEDIR + '/files/EDI/Schumacher/' + filename, 'w', newline='') as csvfile:
                fieldnames = ['PO_Number',
                              'PO_LINE_NUMBER',
                              'ORDERED_ITEM',
                              'ORDER_QUANTITY_UOM',
                              'ORDERED_QUANTITY',
                              'ORDER_DATE',
                              'ACCOUNT_NUMBER',
                              'CONTACT_NAME',
                              'CONT_PHONE_NUMBER',
                              'CUSTOMER_NAME',
                              'HDR_SHIP_ADDRESS1',
                              'HDR_SHIP_ADDRESS2',
                              'HDR_SHIP_SUITE',
                              'HDR_SHIP_CITY',
                              'HDR_SHIP_STATE',
                              'HDR_SHIP_COUNTY',
                              'HDR_SHIP_ZIP',
                              'HDR_SHIP_COUNTRY',
                              'HDR_SHIP_METHOD',
                              'HDR_SHIP_INSTRUCTIONS',
                              'HDR_PACK_INSTRUCTIONS',
                              'ACK_EMAIL_ADDRESS',
                              ]
                poWriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
                # Header
                poWriter.writerow({
                    'PO_Number': 'PO_Number',
                    'PO_LINE_NUMBER': 'PO_LINE_NUMBER',
                    'ORDERED_ITEM': 'ORDERED_ITEM',
                    'ORDER_QUANTITY_UOM': 'ORDER_QUANTITY_UOM',
                    'ORDERED_QUANTITY': 'ORDERED_QUANTITY',
                    'ORDER_DATE': 'ORDER_DATE',
                    'ACCOUNT_NUMBER': 'ACCOUNT_NUMBER',
                    'CONTACT_NAME': 'CONTACT_NAME',
                    'CONT_PHONE_NUMBER': 'CONT_PHONE_NUMBER',
                    'CUSTOMER_NAME': 'CUSTOMER_NAME',
                    'HDR_SHIP_ADDRESS1': 'HDR_SHIP_ADDRESS1',
                    'HDR_SHIP_ADDRESS2': 'HDR_SHIP_ADDRESS2',
                    'HDR_SHIP_SUITE': 'HDR_SHIP_SUITE',
                    'HDR_SHIP_CITY': 'HDR_SHIP_CITY',
                    'HDR_SHIP_STATE': 'HDR_SHIP_STATE',
                    'HDR_SHIP_COUNTY': 'HDR_SHIP_COUNTY',
                    'HDR_SHIP_ZIP': 'HDR_SHIP_ZIP',
                    'HDR_SHIP_COUNTRY': 'HDR_SHIP_COUNTRY',
                    'HDR_SHIP_METHOD': 'HDR_SHIP_METHOD',
                    'HDR_SHIP_INSTRUCTIONS': 'HDR_SHIP_INSTRUCTIONS',
                    'HDR_PACK_INSTRUCTIONS': 'HDR_PACK_INSTRUCTIONS',
                    'ACK_EMAIL_ADDRESS': 'ACK_EMAIL_ADDRESS',

                })

                for row in rows:
                    orderNumber = row[0]
                    orderDate = row[1]
                    name = row[2]
                    address1 = row[3]
                    address2 = row[4]
                    suite = row[5]
                    city = row[6]
                    state = row[7]
                    county = row[8]
                    postal = str(row[9])
                    country = row[10]
                    shippingMethod = row[11]
                    shipInstruction = str(row[12]).replace("\n", " ")
                    packInstruction = str(row[13]).replace("\n", " ")

                    print(orderNumber)

                    instructions = ""
                    if shipInstruction != "" and shipInstruction != None:
                        instructions = "Ship Instruction: {}".format(
                            shipInstruction)
                    if packInstruction != "" and packInstruction != None:
                        instructions += "Pack Instruction: {}".format(
                            packInstruction)

                    # try:
                    #     if not self.validate(orderNumber):
                    #         debug("Schumacher EDI", 1,
                    #             "Status False. {}".format(orderNumber))
                    #         continue
                    # except:
                    #     debug("Schumacher EDI", 1,
                    #             "Status False. {}".format(orderNumber))
                    #     continue

                    # Order Details
                    csr.execute("""SELECT P.ManufacturerPartNumber AS Item, CASE WHEN PV.Name LIKE '%Sample - %' THEN 'Sample' ELSE REPLACE(PV.Pricing, 'Per ', '') END AS UOM, OS.Quantity, P.SKU
                                FROM Orders O JOIN Orders_ShoppingCart OS ON O.ShopifyOrderID = OS.ShopifyOrderID JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Product P ON P.ProductID = PV.ProductID
                                WHERE PV.SKU IN (SELECT SKU
                                                    FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                                                    WHERE M.Brand = 'Schumacher')
                                AND O.OrderNumber = {}""".format(orderNumber))
                    items = csr.fetchall()

                    lineNumber = 1
                    for item in items:
                        mpn = item[0]
                        uom = item[1]
                        qty = item[2]

                        ack_email_address = 'purchasing@decoratorsbest.com'

                        if "Sample" == uom:
                            uom = "MM (Sample)"
                            ack_email_address = 'memos@decoratorsbest.com'
                        elif "Yard" == uom:
                            uom = "YD"
                        elif "Roll" == uom:
                            uom = "RL"
                        elif "Square Foot" == uom:
                            uom = "SQF"
                        else:
                            uom = "EA"

                        poWriter.writerow({
                            'PO_Number': orderNumber,
                            'PO_LINE_NUMBER': lineNumber,
                            'ORDERED_ITEM': mpn,
                            'ORDER_QUANTITY_UOM': uom,
                            'ORDERED_QUANTITY': qty,
                            'ORDER_DATE': orderDate,
                            'ACCOUNT_NUMBER': '106449',
                            'CONTACT_NAME': 'BARBARA KARPF',
                            'CONT_PHONE_NUMBER': '1-212-7226449',
                            'CUSTOMER_NAME': name,
                            'HDR_SHIP_ADDRESS1': address1,
                            'HDR_SHIP_ADDRESS2': address2,
                            'HDR_SHIP_SUITE': suite,
                            'HDR_SHIP_CITY': city,
                            'HDR_SHIP_STATE': state,
                            'HDR_SHIP_COUNTY': county,
                            'HDR_SHIP_ZIP': postal,
                            'HDR_SHIP_COUNTRY': country,
                            'HDR_SHIP_METHOD': shippingMethod,
                            'HDR_SHIP_INSTRUCTIONS': shipInstruction,
                            'HDR_PACK_INSTRUCTIONS': '',
                            'ACK_EMAIL_ADDRESS': ack_email_address,
                        })

                        lineNumber += 1

                    csr.execute(
                        "SELECT Status FROM Orders WHERE OrderNumber = {}".format(orderNumber))
                    extStatus = (csr.fetchone())[0]
                    if extStatus == "New":
                        newStatus = "Schumacher EDI"
                    else:
                        newStatus = extStatus + ", Schumacher EDI"
                    csr.execute("UPDATE Orders SET Status = {} WHERE OrderNumber = {}".format(
                        sq(newStatus), orderNumber))
                    con.commit()

                    maxPO = orderNumber

            if maxPO != -1:
                csr.execute(
                    "UPDATE PORecord SET SchumacherEDI = {}".format(maxPO))
                con.commit()

            csr.close()
            con.close()

            self.upload(filename)
        except Exception as e:
            debug("Schumacher EDI", 2,
                  "Schumacher EDI ERROR: {}".format(str(e)))

    def validate(self, orderNumber):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        # Check Country
        csr.execute(
            "SELECT ShippingCountry, OrderType FROM Orders WHERE OrderNumber = {}".format(orderNumber))
        tmp = csr.fetchone()

        country = tmp[0]
        orderType = tmp[1]

        if "Sample" in orderType:
            recipient = 'memos@decoratorsbest.com'
        else:
            recipient = 'purchasing@decoratorsbest.com'

        if "US" != country and "United States" != country:
            emailer.send_email_html("Schumacher EDI",
                                    recipient,
                                    "PO {} need manual process (Schumacher)".format(
                                        orderNumber),
                                    "Hi, <br><br>PO# {} has not been processed by Schumacher EDI because it's an international order. \
                                    Please process it manually for ALL Schumacher items. <br><br>Best, <br>Murrell".format(orderNumber))

            csr.close()
            con.close()
            return False

        # Check Stock
        stockStatus = True
        csr.execute("""SELECT P.ManufacturerPartNumber AS Item, CASE WHEN PV.Name LIKE '%Sample - %' THEN 'Sample' ELSE REPLACE(PV.Pricing, 'Per ', '') END AS UOM, OS.Quantity, P.SKU
                        FROM Orders O JOIN Orders_ShoppingCart OS ON O.ShopifyOrderID = OS.ShopifyOrderID JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Product P ON P.ProductID = PV.ProductID
                        WHERE PV.SKU IN (SELECT SKU
                                                FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                                                WHERE M.Brand = 'Schumacher')
                        AND O.OrderNumber = {}""".format(orderNumber))

        rows = csr.fetchall()
        for row in rows:
            uom = row[1]
            qty = row[2]
            sku = row[3]
            if "Sample" != uom:
                csr.execute(
                    "SELECT Quantity FROM ProductInventory WHERE SKU = '{}'".format(sku))
                stock = csr.fetchone()[0]

                if stock < qty:
                    stockStatus = False

        if stockStatus != True:
            emailer.send_email_html("Schumacher EDI",
                                    recipient,
                                    "PO {} need manual process (Schumacher)".format(
                                        orderNumber),
                                    "Hi, <br><br>PO# {} has not been processed by Schumacher EDI because ALL Schumacher items in it have inventory problem. \
                                    Please contact the client and process it manually for ALL Schumacher items. <br><br>Best, <br>Murrell".format(orderNumber))

            csr.close()
            con.close()
            return False

        csr.close()
        con.close()
        return True

    def upload(self, filename):
        class My_Connection(pysftp.Connection):
            def __init__(self, *args, **kwargs):
                try:
                    if kwargs.get('cnopts') is None:
                        kwargs['cnopts'] = pysftp.CnOpts()
                except pysftp.HostKeysException as e:
                    self._init_error = True
                    raise paramiko.ssh_exception.SSHException(str(e))
                else:
                    self._init_error = False

                self._sftp_live = False
                self._transport = None
                super().__init__(*args, **kwargs)

            def __del__(self):
                if not self._init_error:
                    self.close()

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        srv = My_Connection(
            host="34.203.121.151",
            port=22,
            username="schumacher",
            password="Sch123Decbest!",
            cnopts=cnopts
        )

        with srv.cd('../EDI/EDI_from_DB'):
            srv.put(FILEDIR + '/files/EDI/Schumacher/' + filename)

        srv.close()

        debug("EDI", 0, "EDI uploaded {}".format(filename))

    def getRef(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

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
            if "POA" in file:
                sftp.get("../EDI/EDI_to_DB/{}".format(file),
                         FILEDIR + '/files/EDI/Schumacher/{}'.format(file))
                sftp.remove("../EDI/EDI_to_DB/{}".format(file))

        sftp.close()

        for file in files:
            if "POA" not in file:
                continue

            f = open(FILEDIR + "/files/EDI/Schumacher/{}".format(file), "rt")
            cr = csv.reader(f)

            for row in cr:
                if str(row[0]).strip() == "Customer PO Number":
                    continue

                PONumber = str(row[0]).strip()
                refNumber = str(row[2]).strip()

                print(PONumber, refNumber)

                if PONumber != None and PONumber != "":
                    csr.execute(
                        "SELECT ReferenceNumber FROM Orders WHERE OrderNumber = '{}'".format(PONumber))

                    try:
                        ref = str((csr.fetchone())[0])
                        if ref == "None":
                            ref = ""

                        print(ref)

                        if refNumber not in ref:
                            newRef = "{}\,Schumacher EDI: {}".format(
                                ref, refNumber)

                            csr.execute("UPDATE Orders SET ReferenceNumber = {} WHERE OrderNumber = {}".format(
                                sq(newRef), PONumber))
                            con.commit()
                    except Exception as e:
                        print(e)
                        continue

        csr.close()
        con.close()
