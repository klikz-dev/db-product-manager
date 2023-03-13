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
API_COOKIE = '__utmz=198764782.1676364716.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _gcl_au=1.1.796977913.1676364717; _tt_enable_cookie=1; _ttp=OaImm8shp1H2v6fYNNP8obg1y2E; _fbp=fb.1.1676364718240.2061779072; _pin_unauth=dWlkPU5qTTVPREZqWkRRdFlqazBZeTAwTkRBNUxUazJPRGd0Wm1ZMk5qVm1NRGxqTm1FeQ; hubspotutk=8e23cf84c2f5cdc40931199164511e28; __hs_cookie_cat_pref=1:true,2:true,3:true; _hjSessionUser_1552480=eyJpZCI6IjA5YmUzOTZhLWFiNjQtNTU0NC04ZWJhLTk4ODllOWJlZmE4YyIsImNyZWF0ZWQiOjE2NzYzNjQ3MTg3ODMsImV4aXN0aW5nIjp0cnVlfQ==; 6286=8b37cdf646cc2717d949306576222229; remember_me_token=cMrRDFdmn5JLIbLOtWdc_g; _gid=GA1.2.1288574999.1678648189; ln_or=eyIxMDQ2MDk4IjoiZCJ9; _gat_UA-123650249-3=1; __utma=198764782.1219712163.1676364716.1678648187.1678686095.21; __utmc=198764782; __utmt=1; _hjIncludedInSessionSample_1552480=1; _hjSession_1552480=eyJpZCI6IjFjNjc4ZTA3LTkxYTEtNDY1MS05NzRiLWUzYmYzMmJlMjU1ZiIsImNyZWF0ZWQiOjE2Nzg2ODYwOTY5MzgsImluU2FtcGxlIjp0cnVlfQ==; _hjAbsoluteSessionInProgress=1; __hstc=105233308.8e23cf84c2f5cdc40931199164511e28.1676364719308.1678648197653.1678686101593.22; __hssrc=1; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2FCARD-NAT-ARROW2%2F071; __utmb=198764782.4.10.1678686095; _ga_KWQMVELYQV=GS1.1.1678686094.22.1.1678686133.21.0.0; _ga=GA1.2.2049969643.1676364717; _phillip_jeffries_session=TmxkanY5QzVvaXhHdGZEVVBpd20xbWtPQVVsQzRrYW8rN2U0dWdvOUh5N0c4VHBWVWwxYm8xNTFaMDdGN1JjVUFaNVZyR0VWd2RZQXlQMjAyenJhTGN4ejhFTzNEZndhL2F0YU5sb1BSUGNkdWZiSnVvcUttZi9xSG9xcFI2TW9qVC9Wa0ZjQVVRV2RGTmZPanlyZEtpZlhrVS9IUFNnaEV6U2E3ZmdKb1JsS1pJR2xEZHFvU1ZqYkR6Vlh3SG1qdWZJS1dPeFhEZWRuNWlMaEVMY282bmYyMzlxZzNIeEhaZC9DYTZtOVdicEhwcXRwenNINVl6LzdNVG1PUk1rRi8zQ2psZ1Y4ZVhWSzFkbEhDQ2ZZK2lSVjJTSjdvenZGK0JGMW5SdnkySFpOVXBFaUswVmQ4TnNoNGxOMktZYXphMFYxR1kwNnJUcGNKNVcrMHRtNjF3Z1JURE1PKzVWb1NwWWRSTnplb2FsMjN3azh0VjJ2VjNya1JneDFpVGJzZWlFR2RTN05zZWVyVWVKdTE5anhSTzR6Z012YzczWFJhYVc0VTRQU3RFQmtrMTdRdnVwZDJCWGlMc2l5UTVicGNHK2NSSW01N3EyYXNXaUxGZ1pkejRkMTlRcy94T2Z5SG5jUTlQMWVnQnNrdVRXRlorNXY1aEpuYmdqRzgvT3hzSmpjMVQ3blAzbjlMUHNYcE5Fa0ZPdzB2SXFkdWVuSnJBM3BiMnlVYXhra3c2UXhqSkhGMzZQNmN0cG1qVUJ4UU5TZHFDcHc3M25ULzVjNGJyWTFpVHU2ME1JTVlkbCtoQzVUTVBvcWcyeE9RWmN2SFVFOW9tVG5YQ3U2bml0VHFXeERJbE5VTXB2YWlYRnlnRG5VQk81Yk1ZZFo1ZnJ4QkxTbVRhSUxUYkN6dmZXWXBCWVdxZmpOcDZ6UmNOZ3dFYjkrUFJEOXJuSEhBZEZsTzRXdDhFTWhkQ1hjcFlqZG00VmRXZjlaR3R6RGZZYmprWGRNNU52aG9rZmduTkZZa1RGV2ZzV2tJVmd4K2krNVBQQ2NkZG4rT3YyelVPa2NVaGw4Q2I0L2dzcFZQcnhCUDBiSnoyeFBleVVSZ0JDVWRabXR0L1lpeUJuMDR1c2NSZ1ZSRlJRd3lWTmtIRWwzdVhrR2E3ZkMvWFU9LS1waTNjbWZoRVhlRFplS2Q3YzdIUXBRPT0%3D--b55c684ceda36babc8b7708065ceca41338f8897; __hssc=105233308.3.1678686101593; _dd_s=logs=1&id=333202fb-ebc1-43ef-8a61-af61883a6f28&created=1678686097620&expire=1678687039345'
API_TOKEN = '4cNIV8F24n9mX5pPu+oTVPXLhK1iU0lKvH0VfmluY3eVO3yR0rxQx8D529qCOzY3yPq/1SJkLnfDLEIxG7eRAg=='
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
                    }),
                    verify=False
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
                    }),
                    verify=False
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
