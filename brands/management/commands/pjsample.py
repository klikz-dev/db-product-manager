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
API_COOKIE = '__utmz=198764782.1684269090.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _tt_enable_cookie=1; _ttp=dF0LH7odFJQZdOGMVWJtJGKta0k; _fbp=fb.1.1684269091787.1077234717; _pin_unauth=dWlkPVpUUXlaREkwWmprdE16UmtZaTAwWVdRMExUaG1NRFF0WVRoalpXSmlNall6TURSaQ; _hjSessionUser_1552480=eyJpZCI6IjJkNzgzYjRmLTg1NzYtNWRmMy05MDY4LTg2NjUwYTBiNTE1MyIsImNyZWF0ZWQiOjE2ODQyNjkwOTIzNTAsImV4aXN0aW5nIjp0cnVlfQ==; 6286=1474234380cc0cbf695150c200694a0b; hubspotutk=40ea823d88252947a147076251e50b0d; __hs_cookie_cat_pref=1:true,2:true,3:true; _gcl_au=1.1.415455897.1693247617; __utma=198764782.1993795334.1684269090.1693247617.1694615708.9; __utmc=198764782; __utmt=1; _gid=GA1.2.1564849781.1694615713; ln_or=eyIxMDQ2MDk4IjoiZCJ9; _hjIncludedInSessionSample_1552480=1; _hjSession_1552480=eyJpZCI6ImQyNGVhYTQxLTdkNWUtNDQ2OS05ZThkLWUyN2Y3YzQ5YTM1MiIsImNyZWF0ZWQiOjE2OTQ2MTU3MjAwNjYsImluU2FtcGxlIjp0cnVlfQ==; _hjAbsoluteSessionInProgress=1; remember_me_token=YuEBRd4MBV0IuJonqe5Hvg; __hstc=105233308.40ea823d88252947a147076251e50b0d.1685510366927.1693247646916.1694615727872.8; __hssrc=1; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2FCARD-NAT-ARROW2%2F071; _ga_KWQMVELYQV=GS1.1.1694615718.9.1.1694615771.7.0.0; _ga=GA1.1.2036018256.1684269091; _phillip_jeffries_session=aVV6MW1BalZzQjNoYkRGcFdyM1RXQk8zWm9MMm9kN2hLdVRPQTBBN2R1VE9RNjdmVG1oRGNCYUNTcEo4T2xTemhPRDBsRzB2Nnp3WlIwM0h6R3ZmaW9YUWtHSTlibFc4MjRXaFlsT2x2VnBwUE5RZ3JweFZHS3FvVzZUSHNTNnZ1L1gxTGtUam13b0M0V1BhYlI4dnpuRW0wa3AzdlBuUW1iUTFMZVFISTBPa2hsaEEwWElPNzB1Z0ZmSXBockV1dHR1TGdnR3hWMkdQYTNPRXAxY2RPUEdYVTd0NkdWZmNqMURqOEh2clBWOVhQdHBhMjRxNk5hSVg5S0M0RVVFMVJWRUt2QkhtQnUzZE11alNiOTlQMmZ0cWJMQytiK0YxbzY0TUJLVzkyOWVrMlQ1L21xNSt4L0txcjJjREVKMHdGYkI2OFptdmJuMElUZlRxQ0NhUkdPa09BUG0wTEhHK2g1V1J5UzZOcU16MXhqVG82TlJlaW1pc3JLZVdaL2k2YWRpallvQ3NnQzBvSGc4emk5NVl4eGE0bU8yYlR4aEx4YUpNM0pGbjJ2RldWTnFyR25SZUVPSjRVTjhIQndXVnkwaXp0bDlsWk44MGtubTc4SkVZT1BnQTJTN3IwU3NvRHNBZnFjbzkvcnZuVHdSMjNGcXJSdTdGVjBqRDY2RE94dE55aGZuaTlQa1JFNGxnR1RrZ0M2bVBHS1JhcThUR29BbUZQQTB0dmkyQVVmOEsxWXhPOFE5OHBWNjVld0RSNE1EL0tRNUhML1FnWjhXRVhWK1BwOWg1Q1FvbXFFY3ZVRC9GYnozdmFLY2c4WWdyd2lWUGFQeE5zNFBJRk8vbUJpR0FHaWh3aUlwQmNXVGY1cEY2MEhMUXlXRXI4aFhuV3pkeWZjVjVsRjdxdUlRaFlOZlQ3TmpRRjZkcEYrcWRzRitUUzBZbWxpTmZ1RGlyb1lkZmtiaTRNV2VoeTZQTXA1dzJkY1F0dUJyUUFqOGxIR216UVRWZURQZTF4ZmE3YUJGTzVlam1qNnNsWlhQZG92V2hJVmJmbUdsdXBlSmlxM3VrYXZxNEJFeFlLeU8zQ2UyRnpiNXFzQkFVSS9IbzVuNUtjMnNZYXI0b2NxNmhGa3FMc0IyTmUwOFQzMTd4VTh3VitKSWwwVXc9LS1HZUNiQ1hRdTk4T2JDN0xzZ1A0VDh3PT0%3D--dd325b9fc997c4d51acff9f9fee51ce2f1bfd559; __hssc=105233308.4.1694615727872; __utmb=198764782.5.10.1694615708'
API_TOKEN = '5VnpI1WC4+5ae8SW8H7U4eMUzmZIfkqJdga2URbBSO26Z7wJowukFfpY5ECp5DoJX1ts+HDNdYLZ5UpBxp+Mmg=='
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
            orderedProductVariantTitle__icontains='Sample -')

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
