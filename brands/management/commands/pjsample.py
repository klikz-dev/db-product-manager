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
API_COOKIE = '_gcl_au=1.1.1320949834.1681755148; __utma=198764782.1515365840.1681755149.1681755149.1681755149.1; __utmc=198764782; __utmz=198764782.1681755149.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmt=1; _gid=GA1.2.1855612002.1681755149; _fbp=fb.1.1681755150011.462367147; _tt_enable_cookie=1; _ttp=nHxtJKF1h1MfEXdShT1cjcgHcQ6; _pin_unauth=dWlkPU9HVXpZMk14T1RjdE4yVTVNaTAwWVRCbExXSTRPRFF0TVdZNVlUTmhaVFE0TXpCbQ; ln_or=eyIxMDQ2MDk4IjoiZCJ9; _hjFirstSeen=1; _hjIncludedInSessionSample_1552480=1; _hjSession_1552480=eyJpZCI6IjhkZmM0MDE2LTg2YTAtNGZmMS1hMzI1LTY4ZDBkMTZmYWQxNyIsImNyZWF0ZWQiOjE2ODE3NTUxNTA3MDIsImluU2FtcGxlIjp0cnVlfQ==; _hjAbsoluteSessionInProgress=0; 6286=0c2536ae7f113b51c2a9bcab1130cc3e; _hjSessionUser_1552480=eyJpZCI6IjMyYTU5NmIzLTc1OTItNTA5OS1iNTIxLTFhZDg0ZmUyMWMzNCIsImNyZWF0ZWQiOjE2ODE3NTUxNTA2ODgsImV4aXN0aW5nIjp0cnVlfQ==; __hstc=105233308.115e67ff27c658d76334ec95ce7e008d.1681755153945.1681755153945.1681755153945.1; hubspotutk=115e67ff27c658d76334ec95ce7e008d; __hssrc=1; __hs_cookie_cat_pref=1:true,2:true,3:true; _gat_UA-123650249-3=1; _ga=GA1.1.1419347136.1681755149; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2Fwallcoverings; _phillip_jeffries_session=aTg1ZGc2Ym1Ca0I0LzF1M0M2WGpNSFAzVTVOMy9mVlJZZCtqNkFISVRxMXZSNEp6TVRqeDFhN3poejdtWnkwK3J2Rk0zdDg3d2dwK3ZSNWJFUCtMOTQ0WjF3SzlQU2hyMmFXMHFHdS9lWTZ5SFRYcDdKdEFBL2Q2OHFvWWx5WmhMaThPMkdTZjlaL0kvMk9oaHNnM1k5cVBJMm1yRlVNdXlPcE9RSGU0bEtyWE4rT1RNdUFUdVpTeVdqOCt5UVgzUzVhaXNYT2lQTExXSVgvYS9yMGR3emFUcVMrMHdIcXVQVG5DRHZoNE5PYlFkTlEySWk5LzhJRW5TZGcxYWhyN25vZW1rK1ZSdVdOV01qUlV4ZUNabUNTVlVpcFBsbDZOUWI5dnZFeDJ1UTYvKzhJSTFlbWg1NHpjdllRRjZQWXJKdmcyckpLNGRTeU1jT2kyeGtuSDJ4VUk5cHNkdXdlckZLaWNHakxsWDUwcDJTdm0ya3VrUHladXhlM1UwZHdwb2FqNW55Wlc4Q3pxUkJCTW1KUmFKWFBzYndjKy9MYnpQY3RBYTk5Mk12S0wzd3VTZlZ0RjdENXlrcmpESy9oUGp2OVlSYWdTMGJLMTBhRjAxRlFlL0ZWVjdYa2UybHVnd2I0enJPUFZETHlLZHJWMzlBUGJ0U1QrOGhSWjAzQTl1SnJES0dPbUUxdUxkMGUvUkZISGkvTFdZaGpaa2pvNlpqL0txa2ZSZUVxUVNwTG9ObVhydTg2RllmVjhHQlBIOWgwUSt1bGJVdzZIQ2gva2VXaW5lZE8wN1JNS3BvV0drdjNQc0l3STVLWWR3RnRwVnQ4NE43eURFaWV0NHZuWjA4dzhyd2JMVkwyM0xEck9TSWUxd2tRZkM1eFl3TGJZdVBOVko5bElWOVAzNEpDK2dDajArUzdyMlEzVUVMWEpOV2djWTFiWlBOQ0ZnUzU2K0QzSXMxeXJwaXVzVjAxV0hhdFJrdGRHS2tpbUlhYjRFbEkya0pwZnlTRTJLNENTd2lScEdYSUJtZmtTczdvaUlhcXZnaWo4WFdqWnlNOVc4RFF4bzYvam4wWXpaM2J2RVZKTGpHZFI2L2dycnhrK3RHQVJTQUZJTlBNZHZXaVlybWtZZkVsZHJEOFBtajY4RS8vOXYrMlN0N1E9LS1NV2lldzBCbWJDWFliWU5COXl3a1N3PT0%3D--913091633e9c71900cca35ff3d31dd306328a6ef; __hssc=105233308.3.1681755153947; _ga_KWQMVELYQV=GS1.1.1681755148.1.1.1681755230.39.0.0; __utmb=198764782.4.10.1681755149'
API_TOKEN = 'LVAulVLmvnL/4nZ7mQ7urIaAIDwJ13uOpof0va+BhHHtUaWSsicHp8mkJX2ib0yiw7Nnl2Zl8K3XGTZfnD+DPg=='
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
