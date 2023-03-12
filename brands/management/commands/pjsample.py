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
API_COOKIE = '__utmz=198764782.1676364716.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _gcl_au=1.1.796977913.1676364717; _tt_enable_cookie=1; _ttp=OaImm8shp1H2v6fYNNP8obg1y2E; _fbp=fb.1.1676364718240.2061779072; _pin_unauth=dWlkPU5qTTVPREZqWkRRdFlqazBZeTAwTkRBNUxUazJPRGd0Wm1ZMk5qVm1NRGxqTm1FeQ; hubspotutk=8e23cf84c2f5cdc40931199164511e28; __hs_cookie_cat_pref=1:true,2:true,3:true; _hjSessionUser_1552480=eyJpZCI6IjA5YmUzOTZhLWFiNjQtNTU0NC04ZWJhLTk4ODllOWJlZmE4YyIsImNyZWF0ZWQiOjE2NzYzNjQ3MTg3ODMsImV4aXN0aW5nIjp0cnVlfQ==; 6286=8b37cdf646cc2717d949306576222229; remember_me_token=cMrRDFdmn5JLIbLOtWdc_g; __utma=198764782.1219712163.1676364716.1678310072.1678648187.20; __utmc=198764782; __utmt=1; _gid=GA1.2.1288574999.1678648189; ln_or=eyIxMDQ2MDk4IjoiZCJ9; _hjIncludedInSessionSample_1552480=1; _hjSession_1552480=eyJpZCI6Ijc5MTAwNTlmLWJmYTktNGEzMy1hNDAzLTMzMzEwOTJmYWI4NyIsImNyZWF0ZWQiOjE2Nzg2NDgxOTM5NDUsImluU2FtcGxlIjp0cnVlfQ==; _hjAbsoluteSessionInProgress=0; __hstc=105233308.8e23cf84c2f5cdc40931199164511e28.1676364719308.1678310077678.1678648197653.21; __hssrc=1; _gat=1; __utmb=198764782.5.10.1678648187; _dd_s=logs=1&id=dc6a2fa5-957e-474c-928f-632638a65280&created=1678648193412&expire=1678649296314; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2FCARD-NAT-ARROW2%2F071; _ga_KWQMVELYQV=GS1.1.1678648187.21.1.1678648398.59.0.0; _ga=GA1.2.2049969643.1676364717; _gat_UA-123650249-3=1; _phillip_jeffries_session=SUJrZHdrc0l1S3pTMTUwVnZsYm1tMnBpRzFvNytNa2dUemU4S3lrU2ZRdm02Wlc4U2lNb0kvSVdsd1YzSjFXSnVDMXAvZDBwN0Y5OUVEMjYxUG5xVmR0NzlkU3FwTGN5eHpWTDRuWVNQZU1jM0kvREhoTWh4UnF3YVFVVGJ5bDBMTkVCa1hqNzNCUHJjSmUrYnNCc1R6bWU4alVOUmR4d05VRnE1YTY1Z2g1bE5Yb3BxcytGY2RLWE0rQWs2QUN4S0JWSCt0bFEzK3YvS283aUw4cDcwbjR0RFhJT29idTdvUFZnR1o5K1lzU3FrQ0ExVy9OazgwWWZQSXVBRUkvMkVjdVNFdmJPdkVtMk5YRGZxdjlqcTEzcWZZZXZuUDE2eVNrUmp3SGF6aUlFY0RFNWh2TFBEOTAxelJKV1B2MkdaNTc5U1kwQjlxWnJQVzRCZG5YNXZvek5sTDhiNWIzMXc3VXI3MHZiUGtYakhWYXlRc1dmU0hIK21MY1Q3QjFCYXN1MFhBSFVhRVVSN1YrN21tZTkvT0JOYjQrNzM0UFlJdUhob2g2Szc0TTdTZmpwMHorNnlEUnJ5allCUjNWMWhIcWpJaHozUWtUUy95WkNXTExRcWJrQkxwTVl1SW1RQjE5TmJOSFpDaHgwWVgza1JVWVY0K2Y5alc2ZjhlUC8yQWp1ZUl1bW5TNVZudjM1TzB2VVVERWE1aVlKY3J1U3pSalNJSFNLMmJIeWV1V2t3NEs3SWtKWEJzTVVCU0dTZHM1NkNhRHJCbk9BN25tbWNVbEg4eDRFVkxMRFo1TkNmdGJHcW11TVhzcWErRS93WmNGb1BhcngrK2NvdU4wUHV4cXhuTTRtczZ3SExxR2tHTjkvRnZiblFndUxTOW1ybGFsaGRjMUloQytEbjE2LzUyUUlUenQzeHNDV1ZMMEZwcUcrTWRGNUM3a1JVQ1dEdWVJbGNKSmZZNWExTzR2M1dIV002cmlOMnM4Y3JNZGlnbkFrQWFWd3NKSGMyV2FzdENxMWErNHpRUmJnUTduNGc5Vi9mck0xMHhVYzd6emk4aEhHUjBCa1U2WEZGSDRlK3crWU5MamQ0MjJrRk1yWjhrUUlTYjZQSGNLY2ZEaTlGZXlSRk92VU53YjBybjhkL1ZsQVF1VmduYzg9LS0zZEt4QWRMUkE2bGVCekJGOGhzbkNBPT0%3D--6bc7646e2495d5c3699b46758b67f1cfdda26279; __hssc=105233308.6.1678648197653'
API_TOKEN = 'Mop4Jz/Y4d150mm+ZCkMX1fjIqS9mhMS2IHGGfeXHabEbPUPmi9ilITIe9G6faSyKRQGcKnhy2jWceOKbh/1Ww=='
API_CONTENT_TYPE = 'application/json;charset=UTF-8'
API_ACCEPT_TYPE = 'application/json, text/javascript'


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
                            'accept': API_ACCEPT_TYPE
                        },
                        data=json.dumps({
                            "product": {
                                "type": "sample",
                                "id": mpn
                            },
                            "quantity": 1
                        })
                    )
                    j = json.loads(r.text)
                    print(j)
                    time.sleep(3)
                except Exception as e:
                    print(e)
                    debug("PJ EDI", 2, "Adding Item {} to Cart has been failed. PO: {}".format(
                        mpn, orderNumber))
                    return

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
                    })
                )
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
                    })
                )
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
                    }
                )
                j = json.loads(r.text)
                print(j)

                time.sleep(3)
            except Exception as e:
                print(e)
                debug("PJ EDI", 2,
                      "Processing PO {} has been failed.".format(orderNumber))
                return

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
            data={}
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
