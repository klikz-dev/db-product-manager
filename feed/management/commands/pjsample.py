from django.core.management.base import BaseCommand
from mysql.models import PORecord
from shopify.models import Order, Line_Item
from django.db.models import Q

import requests
import json
import os
import time
import itertools
import pymysql
import urllib3

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

# API credentials
API_URL = 'https://www.phillipjeffries.com'
API_COOKIE = '__utmz=198764782.1707771577.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _gcl_au=1.1.564349727.1707771577; 6286=44fb69b26a81b1539023e8f87ba0bb4d; _pin_unauth=dWlkPU5qWXdObU0zWm1VdE1qQmtaaTAwWWpjMExUZ3pOREl0WlRCaE0yUXhNV05sT0RRMw; _fbp=fb.1.1707771580366.862636777; _tt_enable_cookie=1; _ttp=o8T7rwnfUzJ2UN83WvNgmY3d2Gf; _hjSessionUser_1552480=eyJpZCI6IjM5MDljM2YyLTk0NjUtNTU2Ny05NTZhLTI3YTUyNTVkYWUzMSIsImNyZWF0ZWQiOjE3MDc3NzE1ODA3NzQsImV4aXN0aW5nIjp0cnVlfQ==; __utma=198764782.280550139.1707771577.1707771577.1709018356.2; __utmc=198764782; __utmt=1; _gid=GA1.2.1932891153.1709018356; _gat_UA-123650249-3=1; _hjSession_1552480=eyJpZCI6ImQ0YTg5ZDRjLWQwZjQtNDNmNS1hOTBlLTMxOTJmN2I5Njk5NyIsImMiOjE3MDkwMTgzNjA1ODIsInMiOjEsInIiOjEsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; __utmb=198764782.2.10.1709018356; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2FCARD-AG-ABSTRAC%2FGV100; _ga=GA1.1.1983051082.1707771578; _ga_KWQMVELYQV=GS1.1.1709018355.2.1.1709018383.32.0.0; _phillip_jeffries_session=K0VwN0dsWDF3Y0VHM2dTd3pCN21pVmZWWndBc2xZRzFhZGxJaEcvZzdVcmVJVlgxbVZjZ21PczlBRnlya2hJUmJVMUdXcmJwMzdCa3lZcitQbTQybmNzZDRjblFkdFFmUTI1VDUxcTRjcTFrcmFTWm5reFRsUFZoYnhId3dRanhJVitSR3AxempDTlVRbTRrd1I2WFBhOTBZQWR0T2tBNGo1TzFsZ3hoRzhEZG9hdFBxUGgzSGIzTGx4V1UxZDdLUnZyd3U4Rm9kb2RwUHUwaFBEbkdMcUhLVXg3NnVGbGJ4ZzlBTWI0TmtGWExxTWtTRGJDL25mT254MThaTDUyb0R3RjkzUzBFenpLYXkrK0R3SEptUDZJOVpKdTY3VkRaSUNPeXZZTXZkN2h3cG45SFdBU1FVNEZuRmJXbnRVLzVETUtZYjFaUjZSZVYvc0F6N0VidkoyOHdWMnM1c0d3eG9qY09lNUs5aWdLSnJGdWFJdVlSVDBZZ25CQWN3eUN3RGZnc0xvUFBIbS9lMUNKclp2cHdaUWQwd2hEVXlrTjlxdWdqNTNwN05BZkQzYXYzMEhqa0ZKbmZpd01aSGNHU3pESlRONXRZRDQ0Q2xSMnpPNWxXWXByOG1qQlgxU3lGdW0zbkxyU3BBZ1pqd1R6U25kUjNnNDR2T3AwM0s5cTc0WFRWZmdTRlRPdlMxb3VKWm9SenAybU5YbXJzZkh3WEdmYlU1M2RzeFhuc3hyTHVnL0o3d0hCQ1ErZHVpNy94QlNudmlUY1VxNEptMEZRUlhMOURXV25QVG5qcVNZUXA4WWd4V1c0eW14TXhrY1Nuc1JkZWN3WW5YcHhIeSsxaUpTZ0JaK0NGeDlCSklsbkp3VGtNSHFkMlRHcEx4WUZvSzNFN3RhVjNkcWQvSExKblc0ZzFvdEZ4VW5SVGxqcE1lbmR5NEZsaEJTOFM2NkRWSWVFOWZ0MUVMT2p6TVE1ME5rOHRjQU5ZeUlsa3B6aG9oZ1ZSeEw0WDBPR2ZUanF2eEhDazZORGJaNyswVHYwRnhQTEQ3QlpCSmd2eFdaRzRORmxwRWMrSzc4YnE0MTY3bjc5RWtEUE8rVFpXY2duYkJPa1JTWThtUXZQS1BWTHhmREd5MkJyU3dzLzVlZmZTV0VNeUFEV2szb1U9LS1HdnJmbGFUenIvRloxRi9SZnRJYUl3PT0%3D--1072f412c8e522860796127ec7e2005c4318f48e'
API_TOKEN = 'lJkMc8S8v8xSEjQnFqp2lqR1TPPRgJaJRKvuoKamGdeLI/wp5K9v+0UcPPnpRKX2vkfvsfSqjL4C4WUHCDk7eQ=='
API_CONTENT_TYPE = 'application/json;charset=UTF-8'
API_ACCEPT_TYPE = 'application/json, text/javascript'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Command(BaseCommand):
    help = 'Process Phillip Jeffries Sample Orders'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "process" in options['functions']:
            self.process()

        if "reference" in options['functions']:
            self.reference()

    def process(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        lineItems = Line_Item.objects.all().order_by('order')

        lineItems = lineItems.filter(
            orderedProductManufacturer="Phillip Jeffries Wallpaper")

        lineItems = lineItems.filter(
            orderedProductVariantTitle__icontains='Sample')

        lineItems = lineItems.exclude(
            Q(order__status__icontains='Processed') |
            Q(order__status__icontains='Cancel') |
            Q(order__status__icontains='Hold') |
            Q(order__status__icontains='Call') |
            Q(order__status__icontains='Return') |
            Q(order__status__icontains='Discontinued') |
            Q(order__status__icontains='Back') |
            Q(order__status__icontains='B/O') |
            Q(order__status__icontains='Manually') |
            Q(order__status__icontains='CFA')
        )

        poRecord = PORecord.objects.values()
        lastPO = (poRecord[0]['PhillipJeffriesSample'])
        lastPO = int(lastPO) + 1

        lineItems = lineItems.filter(order__orderNumber__gte=lastPO)

        lineItemsByOrderNumber = []

        for key, group in itertools.groupby(lineItems, lambda lineItem: lineItem.order):
            group_list = list(group)
            lineItemsByOrderNumber.append(group_list)

        for lineItems in lineItemsByOrderNumber:
            orderNumber = lineItems[0].order.orderNumber
            print("PO: {}".format(orderNumber))

            order = Order.objects.get(orderNumber=orderNumber)

            for lineItem in lineItems:
                try:
                    mpn = lineItem.orderedProductSKU.replace('PJ ', 'S-')

                    # Add To Cart
                    r = requests.post(
                        API_URL + '/api/cart',
                        headers={
                            'cookie': API_COOKIE,
                            'x-csrf-token': API_TOKEN,
                            'content-type': API_CONTENT_TYPE,
                            'accept': API_ACCEPT_TYPE,
                            'origin': API_URL
                        },
                        data=json.dumps({
                            "product": {
                                "type": "sample",
                                "id": mpn
                            },
                            "quantity": 1
                        }),
                        verify=False
                    )
                    if r.status_code == 401:
                        debug("PJ EDI", 2, "PJ Token expired. Please refresh!".format(
                            mpn, orderNumber))
                        return

                    j = json.loads(r.text)
                    print(j)
                    time.sleep(3)
                except Exception as e:
                    print(e)
                    debug("PJ EDI", 2, "Adding Item {} to Cart has been failed. PO: {}".format(
                        mpn, orderNumber))
                    continue

            try:
                # Update Billing
                print("Billing Address")
                r = requests.put(
                    API_URL + '/api/cart/samples_billing',
                    headers={
                        'cookie': API_COOKIE,
                        'x-csrf-token': API_TOKEN,
                        'content-type': API_CONTENT_TYPE,
                        'accept': API_ACCEPT_TYPE
                    },
                    data=json.dumps({
                        "customer": {
                            "id": "46986",
                            "company": "AllDecor dba Decorators Best"
                        },
                        "address": {
                            "company": "AllDecor dba Decorators Best",
                            "attention": "",
                            "address1": "1040 First Ave",
                            "address2": "#316",
                            "zip": "10022",
                            "country": "US",
                            "city": "New York",
                            "state": "NY",
                            "phone": ""
                        },
                        "fullname": "Alldecor,LLC",
                        "email": "orders@decoratorsbest.com",
                        "second_email": "",
                        "is_direct": "D"
                    }),
                    verify=False
                )
                if r.status_code == 401:
                    debug("PJ EDI", 2, "PJ Token expired. Please refresh!".format(
                        mpn, orderNumber))
                    return

                j = json.loads(r.text)
                print(j)

                # Update Shipping
                print("Shipping Address")
                r = requests.put(
                    API_URL + '/api/cart/samples_shipping',
                    headers={
                        'cookie': API_COOKIE,
                        'x-csrf-token': API_TOKEN,
                        'content-type': API_CONTENT_TYPE,
                        'accept': API_ACCEPT_TYPE
                    },
                    data=json.dumps({
                        "samples": {
                            "address": {
                                "company": "Alldecor dba Decorators Best",
                                "attention": "{} {}".format(order.shippingFirstName, order.shippingLastName),
                                "address1": order.shippingAddress1,
                                "address2": order.shippingAddress2,
                                "zip": order.shippingZip,
                                "country": 'US',
                                "city": order.shippingCity,
                                "state": order.shippingState,
                                "phone": order.shippingPhone
                            },
                            "address_type": "new",
                            "method": {
                                "id": "1105",
                                "name": "Preferred Method - ETA: 1 Day(s) via UPS Ground",
                                "account_number": "",
                                "po_number": orderNumber,
                                "sidemark": "Decorbest/{}".format(order.shippingLastName)
                            },
                            "type": "samples",
                            "label": "Sample",
                            "sidemark_library_update": False,
                            "sidemark_project_name": True,
                            "shipping_account": False,
                            "time_sensitive": False,
                            "shipping_type": "commercial",
                            "replenishment": False
                        }
                    }),
                    verify=False
                )
                if r.status_code == 401:
                    debug("PJ EDI", 2, "PJ Token expired. Please refresh!".format(
                        mpn, orderNumber))
                    return

                j = json.loads(r.text)
                print(j)

                # Order Submit
                print("Order Submit")
                r = requests.put(
                    API_URL + '/api/cart/samples_submit',
                    headers={
                        'cookie': API_COOKIE,
                        'x-csrf-token': API_TOKEN,
                        'content-type': API_CONTENT_TYPE,
                        'accept': API_ACCEPT_TYPE
                    },
                    verify=False
                )
                j = json.loads(r.text)
                print(j)

                time.sleep(3)
            except Exception as e:
                print(e)
                debug("PJ EDI", 2,
                      "Processing PO {} has been failed.".format(orderNumber))
                continue

            csr.execute(
                "SELECT Status FROM Orders WHERE OrderNumber = {}".format(orderNumber))
            extStatus = (csr.fetchone())[0]
            if extStatus == "New" or extStatus == None or extStatus == "":
                newStatus = "Reference# Needed"
            else:
                newStatus = extStatus + ", Reference# Needed"
            csr.execute("UPDATE Orders SET Status = {} WHERE OrderNumber = {}".format(
                sq(newStatus), orderNumber))
            con.commit()

            lastPO = orderNumber

            csr.execute(
                "UPDATE PORecord SET PhillipJeffriesSample = {}".format(lastPO))
            con.commit()

    def reference(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        # Order Confirmation
        print("Order Confirmation")
        r = requests.get(
            API_URL + '/api/orders/complete.json?type=sample&limit=100&offset=0',
            headers={
                'cookie': API_COOKIE,
                'accept-encoding': 'gzip, deflate, br',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
            },
            data={},
            verify=False
        )
        j = json.loads(r.text)

        items = j['items']

        for item in items:
            try:
                ref = str(item['url']).replace('/order/', '')
                po_number = int(item['details']['po_number'])
                print(po_number, ref)
            except Exception as e:
                print(e)
                continue

            try:
                csr.execute(
                    "SELECT ReferenceNumber FROM Orders WHERE OrderNumber = {}".format(po_number))
                currentRef = str((csr.fetchone())[0])

                if currentRef == "None":
                    currentRef = ""
                if ref not in currentRef:
                    newRef = "{}\nPJ: {}".format(
                        currentRef, ref)

                    csr.execute("UPDATE Orders SET ReferenceNumber = {} WHERE OrderNumber = {}".format(
                        sq(newRef), po_number))
                    con.commit()
            except Exception as e:
                print(e)
                continue
