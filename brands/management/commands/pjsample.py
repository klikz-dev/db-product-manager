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
API_COOKIE = '__utmz=198764782.1676364716.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _gcl_au=1.1.796977913.1676364717; _tt_enable_cookie=1; _ttp=OaImm8shp1H2v6fYNNP8obg1y2E; _fbp=fb.1.1676364718240.2061779072; _pin_unauth=dWlkPU5qTTVPREZqWkRRdFlqazBZeTAwTkRBNUxUazJPRGd0Wm1ZMk5qVm1NRGxqTm1FeQ; hubspotutk=8e23cf84c2f5cdc40931199164511e28; __hs_cookie_cat_pref=1:true,2:true,3:true; _hjSessionUser_1552480=eyJpZCI6IjA5YmUzOTZhLWFiNjQtNTU0NC04ZWJhLTk4ODllOWJlZmE4YyIsImNyZWF0ZWQiOjE2NzYzNjQ3MTg3ODMsImV4aXN0aW5nIjp0cnVlfQ==; 6286=8b37cdf646cc2717d949306576222229; __utma=198764782.1219712163.1676364716.1676472402.1676621186.5; __utmc=198764782; __utmt=1; _gid=GA1.2.1098510028.1676621186; _hjIncludedInSessionSample_1552480=1; _hjSession_1552480=eyJpZCI6IjFiMTgxNDQ0LTg3YTgtNDJhMS1hOTg4LWNiNDczZWI3OTU2NSIsImNyZWF0ZWQiOjE2NzY2MjExODc1MjQsImluU2FtcGxlIjp0cnVlfQ==; _hjAbsoluteSessionInProgress=0; __hstc=105233308.8e23cf84c2f5cdc40931199164511e28.1676364719308.1676473719900.1676621216712.6; __hssrc=1; __hssc=105233308.1.1676621216712; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2FCARD-TW-SILKHALL%2F2312; _ga_KWQMVELYQV=GS1.1.1676621185.5.1.1676621467.60.0.0; _ga=GA1.2.2049969643.1676364717; _gat_UA-123650249-3=1; _phillip_jeffries_session=ei90cHYzK28wWnZNRUlFbVlxYUwydzRnRTVVRUQzeEQwWi8xc2JnZkVVejlTZ0RSMUdaKzNoVkhDR3VyWHRMZ3dXd1dhcnU1akFjNmN6Y2tZK0YraFVMeFhzL1B0YldESWNDZnRQdUhEOGlxb2ZUUFM0b3QyM0xpL0hha2tEcjhnMnZZUmlTUnpaL1poL0ZtaVRNcUpwOTliaysvaVFvcmdBQ0dZWVdGaTZORHZGaE1PWjJvVTlsQ0d5UE4yMFp1Ky9zK3lReXhFck81dWhlcVVObjZtMURLUS9XRXkxeHJHcHFYeDVFSmd4cy84T1JEVVhiRFYwT3IreGd6aGZScnJmOXY3SWJmazY2czVFZWU1QzJ0Q1R4R2xxK09ZNVBsT2EydWVJYWpqeVZ1ZkpzSW9JZVNJd2pxdVBHVkJQVU44UDBTaDBWTHFtMXloeDFsY1F6b1BVOVMzMmwxNStkdTROOEhWWUhYdTFvNllicGs4Q3VhVVA4MTdEbytDZVFEdmcrbGgvVkoyZUxNNXhCaEUwcVpRcDNkZnBqUktpekVpZDFGYnIvVnM2dXA5SGRTbzJucE1UVFQ1eWFCb2NicDlkQ2NqcURHQUkxWEloMW43S29sUXI4amhDWGNjdjNWQklBOVlUNVBwNlNTZkc4ZmdibVpZYTZWSHk3UTRCRVNlaVhNSEdSSkQxN29mUVlKaDZYQ1N6bWwwUkNNaDhIRWlYUFdHbkRjdDJydnBDN1pzUFJESmFYMHIyTGJSMFBnYk5NN2c0SWYxYkpjT1BVM0svU3JxNDZSNEUrcXVFK2VKRE9kbFBpbXp0Q3VXN3V6U3ErN0RFN0xYdEJvWVd1azI0QlVtYVB2NHJvNFliTDZKUFZPY05sVWRsT3doVW44ZUFlQ2puMFFnSk5RQVlDYjFsaUlZTlNJc1NvNTRvYjR2bGxwbHpjZTc1YXRSeDlCUm44M2RaNUtYdklxSWhXY0F0UEFVaWh5RmVFeExVazJGSm83NlFzNlJublNXVTFiNGQyc3QvM0NvSVAyRm5MaGI5THExWUVTNkpEZ1llTk5ZNElSOTYxTmJTcElQck0ydWQ0TXJoa0crSHErdVJ1V245VnExRVBVRS9mSlRCVUg1YWVrb1FqUkxhK0xPdjZNRDJSYWRoTkphbzA9LS1idmdjVEd2UVc4L2FhWmI1K3Z5WTh3PT0%3D--be4fd3dab8f53d55e4eeecfc8d3f1f2d0636d471; __utmb=198764782.4.10.1676621186; _dd_s=logs=1&id=73f956a2-c279-4a88-92bb-beb368e0a8f0&created=1676621187554&expire=1676622383045'
API_TOKEN = '8ALYjNfenYq47KyXkHAsycRv9Y3SiAzqex7D2+2g8wx2D0eCGVlxaAK2gLqZVh0XeffNR4WoAbknArNBJeEcCg=='
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
            API_URL + '/api/orders/complete.json?type=sample&limit=20&offset=0',
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
