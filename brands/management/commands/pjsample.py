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
API_COOKIE = '__utma=198764782.280550139.1707771577.1707771577.1707771577.1; __utmc=198764782; __utmz=198764782.1707771577.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; _gcl_au=1.1.564349727.1707771577; 6286=44fb69b26a81b1539023e8f87ba0bb4d; _gid=GA1.2.2094705783.1707771579; _gat_UA-123650249-3=1; _pin_unauth=dWlkPU5qWXdObU0zWm1VdE1qQmtaaTAwWWpjMExUZ3pOREl0WlRCaE0yUXhNV05sT0RRMw; _fbp=fb.1.1707771580366.862636777; _tt_enable_cookie=1; _ttp=o8T7rwnfUzJ2UN83WvNgmY3d2Gf; _hjSessionUser_1552480=eyJpZCI6IjM5MDljM2YyLTk0NjUtNTU2Ny05NTZhLTI3YTUyNTVkYWUzMSIsImNyZWF0ZWQiOjE3MDc3NzE1ODA3NzQsImV4aXN0aW5nIjp0cnVlfQ==; _hjSession_1552480=eyJpZCI6IjQxNGRkZTBiLTgyM2UtNDBlMi1hMzQyLTcwNDM3N2I5YThjMyIsImMiOjE3MDc3NzE1ODA3NzUsInMiOjEsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=; __utmb=198764782.2.10.1707771577; _ga=GA1.2.1983051082.1707771578; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2Fwallcoverings; _ga_KWQMVELYQV=GS1.1.1707771578.1.1.1707771595.43.0.0; _phillip_jeffries_session=WWN0V0lKRFl0dkZ1SkdtS0ZKVC80OWF0OHZMclh3Y0NXUjV3cWhDMmRKTkxQNDYzTHpNcENDTEN0bUxiMkZJc28rUllaRE1uWWY3M2l5bytyMnlSbVprU0h0M2ZxdmdDdVdpQlBweFRlRDZIK2IvNkorWDlBR2lxVzhaUitkc3VlNldYMXRETXl1M1Z3M3ZXWVBxSzBNOCtaSjNVdFVRK0xUU3ZoV3pNLzEyTjZmKzhaeFl4c01PdERYMWJ1b1F2SysybklRdUVkMm5NTVpUSjhsTkxRck9uUURUQXlONmJoT0ZJckdHYmJDN2I2cHo2WldVTUFOQXY1bDFhMndLSDZ1SFhYeUxFaFNabExYZEd3SUFyc05xMkRWc29CaVNPVG4zUmwyc0J0Q25xNkVTdFlqbWtnMDNIZDVCcEc5RXRWUXhmMUE2MGxhcGhMZHJ0OGg5Y0tUVHVmNzRjd2tyQXNHVXk2VW5SMm5IbE9FcC93SGtQa1BBMGhGOVppNjFhZWFVSXZ1aXNuRWt1YldOSnlrV3hXZ3ljTzloZnJWeURTTHRVV1dvN1JLRm53cWRkZUJXbDFtcmhrTUtMT0lHTkFBdHFyUTgwS0RVNU1VeEU3WGtsZ0RkUWlyZDIyZ0wzVUtwTFl5czU5ZTZtem05Z3hGZjRxOVdIck1uVjlTWVFqZEhHWjRyNnZSanlTOC9XejB5cGRZY1lHWUZTNVBTaGhkdk44TThaejdlWmZ5bVFmS21RVHBJdStuU0JRZjRFTHVaQ0xpZkk3YkZYVHBVYWFyZUkwZTVWNWozdWhiS0NBUW51ZUtRbDcrSi9JeC9aOFJuZEV2OVQ2bS81VzFQTW84dDY3UC9FNXhzeGs5Nmx6cDY4aGFaZ3crNXZ0Uzc0Vlkxd1ZSSFEreW9OZjVlN3ZxTU5oekprSS9iNS9zRXE4RGx4RWVnMTdGM0VhaXV1RjNYLzZWNDlrVVFnaFJxK0l6NmpxN0xnekxwaVRBY0lyNHZnZDdReDZJalVZR3NpZGxkRFV3cFZzaGJwVFUvV1lmK1FCSmJTeXhCMnpTcFMwUU9vVlBwUXlTQVNWTU5ueXlLcDlnRCtsRHduVzN4MnFERjFyMzI4Nm4yQ1NZblp6M2Z1S0hUT2RFQXFMczlnL0JtWlN6MjMyb2c9LS1SVmZQRktYVkpLUHVNaFh4OWNxRTRnPT0%3D--eb819cd987821753f7225164ece7923d77766928'
API_TOKEN = 'Ny+vtleZvv/D9MmMJBZIHE9se8Rk3lbGhSKt3kyMHmmsoMj+s+MrlayASt394bBqeD7fgffCUmnLdaWGXsV18Q=='
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
