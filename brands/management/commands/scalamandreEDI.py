import requests
import json
from django.core.management.base import BaseCommand

import os
import pymysql

from library import debug, common

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
        # Generate Token
        token = ''
        try:
            authUrl = "http://scala-api.scalamandre.com/api/Auth/authenticate"
            authPayload = json.dumps({
                "Username": "Decoratorsbest",
                "Password": "EuEc9MNAvDqvrwjgRaf55HCLr8c5B2^Ly%C578Mj*=CUBZ-Y4Q5&Sc_BZE?n+eR^gZzywWphXsU*LNn!"
            })
            authHeaders = {
                'Content-Type': 'application/json'
            }

            response = requests.request(
                "POST", authUrl, headers=authHeaders, data=authPayload)

            print(response.text)

            data = json.loads(response.text)
            token = data['token']

            if token == '' or token == None:
                debug("Scalamandre EDI", 2,
                      "Token generation has been failed. Blank token returned.")
                return

        except Exception as e:
            print(e)
            debug("Scalamandre EDI", 2, "Token generation has been failed")
            return

        print(token)

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
                        WHEN O.ShippingMethod LIKE '%2nd Day%' THEN 'UPS2'
                        WHEN O.ShippingMethod LIKE '%2-day%' THEN 'UPS2'
                        WHEN O.ShippingMethod LIKE '%Overnight%' THEN 'UPSN'
                        WHEN O.ShippingMethod LIKE '%Next Day%' THEN 'UPSN'
                    ELSE 'UPSG'
                    END AS ShippingMethod,

                    O.OrderNote AS ShipInstruction,
                    CONCAT('DecoratorsBest/', O.ShippingLastName) AS PackInstruction/*,
                    CAST(O.PaymentMethod AS nvarchar(max)) AS PaymentMethod,
                    CAST(O.Notes AS nvarchar(max)) AS Notes*/,
                    O.ShopifyOrderID

                    FROM Orders_ShoppingCart OS JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Orders O ON OS.ShopifyOrderID = O.ShopifyOrderID

                    WHERE PV.SKU IN (SELECT SKU FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID WHERE M.Brand = 'Scalamandre')
                        AND O.OrderNumber > (SELECT ScalamandreEDI FROM PORecord)
                        AND O.Status NOT LIKE '%Hold%'
                        AND O.Status NOT LIKE '%Back Order%'
                        AND O.Status NOT LIKE '%Cancel%'
                        AND O.Status NOT LIKE '%Processed%'
                        AND O.Status NOT LIKE '%CFA%'
                        AND O.Status NOT LIKE '%Call Manufacturer%'
                        AND O.Status NOT LIKE '%Scalamandre EDI%'

                    ORDER BY O.OrderNumber ASC""")

            rows = csr.fetchall()
            maxPO = -1

            for row in rows:
                orderNumber = row[0]
                orderDate = row[1]
                name = row[2]

                address1 = str(row[3]).replace("\n", "").strip()
                address2 = str(row[4]).strip()
                if "," in address1:
                    address2 = str(address1).split(",")[1].strip()
                    address1 = str(address1).split(",")[0].strip()
                if address2 == None or address2 == '':
                    address2 = 'None'

                print("--" + address2 + "--")

                city = row[6]
                state = row[7]
                postal = str(row[9])
                country = row[10]
                shippingMethod = row[11]

                shipInstruction = str(row[12]).replace("\n", " ")
                packInstruction = str(row[13]).replace("\n", " ")

                instructions = ""
                if shipInstruction != "" and shipInstruction != None:
                    instructions = "Ship Instruction: {} \n\r".format(
                        shipInstruction)
                if packInstruction != "" and packInstruction != None:
                    instructions += "Pack Instruction: {}".format(
                        packInstruction)

                # Order Details
                csr.execute("""SELECT P.ManufacturerPartNumber AS Item, CASE WHEN PV.Name LIKE '%Sample - %' THEN 'Sample' ELSE REPLACE(PV.Pricing, 'Per ', '') END AS UOM, OS.Quantity, P.SKU, PV.Cost
                                FROM Orders O JOIN Orders_ShoppingCart OS ON O.ShopifyOrderID = OS.ShopifyOrderID JOIN ProductVariant PV ON OS.VariantID = PV.VariantID JOIN Product P ON P.ProductID = PV.ProductID
                                WHERE PV.SKU IN (SELECT SKU
                                                    FROM ProductManufacturer PM JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                                                    WHERE M.Brand = 'Scalamandre')
                                AND O.OrderNumber = {}""".format(orderNumber))
                items = csr.fetchall()

                print(orderNumber, orderDate)

                samples = []
                orders = []
                for item in items:
                    mpn = item[0]
                    uom = item[1]
                    qty = item[2]
                    cost = item[4]

                    ack_email_address = 'purchasing@decoratorsbest.com'

                    if "Sample" == uom:
                        ack_email_address = 'memos@decoratorsbest.com'
                    elif "Yard" == uom:
                        uom = "YD"
                    elif "Roll" == uom:
                        uom = "RL"
                    elif "Square Foot" == uom:
                        uom = "SQF"
                    else:
                        uom = "EA"

                    if "Sample" == uom:
                        samples.append(
                            {
                                "ORDER_NO": orderNumber,
                                "ORDER_DATE": orderDate,
                                "SHIP_VIA_NO": shippingMethod,
                                "S_AND_H": 0,
                                "CUST_NO": "591267",
                                "SKU_REF1": mpn,
                                "SALES_PRICE": 0,
                                "QTY": 1,
                                "SIZE_NAME": "STANDARD",
                                "USER_REF1": mpn,
                                "STNAME": name,
                                "STADDR_1": address1,
                                "STADDR_2": address2,
                                "STCITY": city,
                                "STSTATE": state,
                                "STCOUNTRY": country,
                                "STPOSTAL": postal,
                                "E_MAIL": ack_email_address,
                                "ORDERNOTES": instructions,
                                "BRANCH": "NY",
                                "REQUIRESMGROK": False,
                                "COMPANY": 5,
                                "ORDERTYPE": "SCLL",
                                "SIDEMARK": "Decoratorsbest"
                            }
                        )
                    else:
                        orders.append(
                            {
                                "ITEMID": mpn,
                                "LENGTHININCHES": "{}".format(qty),
                                "CARPETCOST": "{}".format(cost),
                                "NOTES": [
                                    {
                                        "MSGTYPE": "DELIVERY",
                                        "MESSAGESTR": instructions
                                    }
                                ]
                            },
                        )

                if len(samples) > 0:
                    url = "http://scala-api.scalamandre.com/api/ScalaFeedAPI/SubmitSampleOrder"
                    headers = {
                        'Authorization': 'Bearer {}'.format(token),
                        'Content-Type': 'application/json'
                    }

                    payload = json.dumps({
                        "SampleOrderJson": {
                            "USERNAME": "Decoratorsbest",
                            "SAMPLEORDER": samples
                        }
                    })

                    print(payload)

                    response = requests.request(
                        "POST", url, headers=headers, data=payload)
                    print(response.text)

                    try:
                        data = json.loads(response.text)
                    except Exception as e:
                        debug("Scalamandre EDI", 2,
                              "Scalamandre EDI ERROR: PO: {} <br/>Payload: {}".format(orderNumber, json.dumps(payload)))
                        continue

                    self.getRef(orderNumber, data[0]['ORDER_NO'])

                    debug("Scalamandre EDI", 0, "Successfully Submit the Scalamandre Samples. PO: {}, REF: {}".format(
                        orderNumber, data[0]['ORDER_NO']))

                if len(orders) > 0:
                    url = "http://scala-api.scalamandre.com/api/ScalaFeedAPI/SubmitOrder"
                    headers = {
                        'Authorization': 'Bearer {}'.format(token),
                        'Content-Type': 'application/json'
                    }

                    payload = json.dumps({
                        "MType": 1,
                        "MQuoteID": orderNumber,
                        "AccountID": "591267",
                        "QuoteJson": {
                            "ITEMDETAILS": orders,
                            "SHIPTO": [
                                {
                                    "NAME": name,
                                    "ADDRESS1": address1,
                                    "ADDRESS2": address2,
                                    "CITY": city,
                                    "STATE": state,
                                    "ZIP": postal,
                                    "countrycode": country,
                                    "phoneNumber1": "None"
                                }
                            ],
                            "CO_ACCTNUM": "591267",
                            "COMPANY": "5",
                            "SUBMITTYPE": 1,
                            "UserEmail": ack_email_address,
                            "FinalDest": {
                                "Name": name,
                                "Address1": address1,
                                "Address2": address2,
                                "City": city,
                                "State": state,
                                "zipcode5": postal,
                                "ZipCode": postal,
                                "SideMark": "Decoratorsbest",
                                "SideMark2": "Decoratorsbest",
                                "Contact": "",
                                "Notes": instructions,
                                "countrycode": country
                            }
                        },
                        "UserName": "Decoratorsbest",
                        "UserEmail": ack_email_address
                    })

                    print(payload)

                    response = requests.request(
                        "POST", url, headers=headers, data=payload)
                    print(response.text)

                    try:
                        data = json.loads(response.text)
                    except Exception as e:
                        debug("Scalamandre EDI", 2,
                              "Scalamandre EDI ERROR: PO: {} <br/>Payload: {}".format(orderNumber, json.dumps(payload)))
                        continue

                    self.getRef(orderNumber, data[0]['WEBQUOTEID'])

                    debug("Scalamandre EDI", 0, "Successfully Submit the Scalamandre Orders. PO: {}, REF: {}".format(
                        orderNumber, data[0]['WEBQUOTEID']))

                csr.execute(
                    "SELECT Status FROM Orders WHERE OrderNumber = {}".format(orderNumber))
                extStatus = (csr.fetchone())[0]
                if extStatus == "New":
                    newStatus = "Scalamandre EDI"
                else:
                    newStatus = extStatus + ", Scalamandre EDI"
                csr.execute("UPDATE Orders SET Status = {} WHERE OrderNumber = {}".format(
                    sq(newStatus), orderNumber))
                con.commit()

                maxPO = orderNumber

            if maxPO != -1:
                csr.execute(
                    "UPDATE PORecord SET ScalamandreEDI = {}".format(maxPO))
                con.commit()

            csr.close()
            con.close()

        except Exception as e:
            debug("Scalamandre EDI", 2,
                  "Scalamandre EDI ERROR: {}".format(str(e)))

    def getRef(self, PONumber, refNumber):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        if PONumber != None and PONumber != "":
            csr.execute(
                "SELECT ReferenceNumber FROM Orders WHERE OrderNumber = '{}'".format(PONumber))

            try:
                ref = str((csr.fetchone())[0])
                if ref == "None":
                    ref = ""
                if refNumber not in ref:
                    newRef = "{}\nScalamandre EDI: {}".format(ref, refNumber)

                    csr.execute("UPDATE Orders SET ReferenceNumber = {} WHERE OrderNumber = {}".format(
                        sq(newRef), PONumber))
                    con.commit()
            except Exception as e:
                print(e)

        csr.close()
        con.close()
