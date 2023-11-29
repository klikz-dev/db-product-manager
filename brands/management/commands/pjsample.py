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
API_COOKIE = '__utmz=198764782.1699939069.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _gcl_au=1.1.739037927.1699939070; 6286=acc1c94ede758e1e9d88f0f16e8564a9; _pin_unauth=dWlkPU4yWTRZakU1TnpBdE1qWTVZeTAwTWpZMkxUazRObU10TUdJMk1HSmxaR0ppTVRRNA; _hjSessionUser_1552480=eyJpZCI6ImRhMTQ3NWNhLTJjOGMtNTA3OC04NjhjLWQ4MGE5YWQ3ZmFjYSIsImNyZWF0ZWQiOjE2OTk5MzkwNzcxMDUsImV4aXN0aW5nIjp0cnVlfQ==; _fbp=fb.1.1699939078501.483039036; _tt_enable_cookie=1; _ttp=e7hSTLeuiwOtLVxf07g__pVF7au; __hs_cookie_cat_pref=1:true,2:true,3:true; hubspotutk=fa95d840022948cfc30217f4bf7c405c; __utma=198764782.1993769856.1699939069.1700722048.1701240219.3; __utmc=198764782; __utmt=1; _gid=GA1.2.1180530070.1701240221; _gat_UA-123650249-3=1; _hjIncludedInSessionSample_1552480=1; _hjSession_1552480=eyJpZCI6IjllNmM2ODcyLWFjYjktNDZkNi04MTY0LWFhNDMyZWMzMjU0YSIsImNyZWF0ZWQiOjE3MDEyNDAyMjM4NDMsImluU2FtcGxlIjp0cnVlLCJzZXNzaW9uaXplckJldGFFbmFibGVkIjp0cnVlfQ==; _hjAbsoluteSessionInProgress=0; __hstc=105233308.fa95d840022948cfc30217f4bf7c405c.1699939117394.1700722050170.1701240226545.3; __hssrc=1; __hssc=105233308.2.1701240226545; __utmb=198764782.3.10.1701240219; _ga_KWQMVELYQV=GS1.1.1701240219.4.1.1701240237.42.0.0; _ga=GA1.1.1993769856.1699939069; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2Fwallcoverings; _phillip_jeffries_session=OUErY0dpTmdrYVBjOWVIN2I1Qk56M2YzcXBuSGdCZXJRTlg4Unc4SVdvRkY1OFNqZnFWdHZJZGo5Q1hWM3hJdno0TTgxT0lZaVpkZnVsS1FxbE9KYXFXY1R1NU5ibzNqQ0FYVUx4cURLZ3FFM2JzVWRnMVFsSUxzUnh4Z3JFWThUZmkwb05iQnh3SExLc2pzQWVVUVpwejBPUnl3MFBjM1RXMmdYRkJlUHhsWGk0ZWxra3Y3TUgxcXBQVEpEQkZwNkd3dU1zQ3Yxejk4aEladUtZSk4xOThra0dtQ1hEK2t3cnlwUjlVRzhjUGxuQVMxOGF1QUc3ekFKd2w3K3dybXE0bmJDK0pqdE5kMXI0REhLV2lKRW5idFJTSHBVclYxRXdkeHkyTjd5UlFpeTNxdE83YWFxZzZLeXZUTVdISWZpRWU0Y2NSZkh4V2t3WjFrV2c3b0czZkRibFFiY1J1MlhuUVZXeFg4YXZYZy8yYWxac2V1THlON1VDcVhnd3BBMDllUUMrbmJZS1BHWEZURk1wcGRKWkVibWxYbDJ3cHl1UEhNTVIzN3UvL21SV3NocTRZOTJsdjVJakZOTnkzUFVOZE9oUlpBU0VzWFN6N2J2VFpMUStxS3ZPVXRpdk93aXdMSHg2SWNiRkxpTjl1a0tOYjlwSU9DalRvcWo1M3I3SlY1bS9NOGtTSVYrYVJpSEVLWHlDaGxCVm9oSUNtVG1yWit2OWYxdGg5RmtvcFZRaytMTUYwdXJIaUVRdVZUTHM4eU92cy93VUxYb0VHU1E1VmVhQnBHSUVpUTdDM3ZacHJCdzdSOXRZcGNpQjJoVEZvKzM2NXVXWWI3aTREenNCbDV4TUw5S1hzc3J5Y1VMblVGT2tFa25HY1h1NG43WFhlbXN4WjlHaVE2ckU3bnpMbExIMUFSUlpZR21CSW1DMkhhNWJ6YkV3czRrbGdwd3AzUTNORmR1UVp3S0JCbGVrWDZuMWxYQks4RS9FQzU0bGcveURnVFdpakh1eEFUQXZWRjkyQmp6K2JmaUt2REVYOVNqYTZla3EzbXp4cG9LTlY1NEhzeW9UOW9mWWRvUFd0aHgySGp5OEt6N0tlUHVwOVEwMzhBSzQrcHlHUWEyZk1jcllqRDFoUEdST2NCM0dHa0hHUENRUGs9LS1ldGgvUmxkemFtSDhyVXlod2VycVNRPT0%3D--051377b2fe0936ebdf63a822e3b72b123248167a'
API_TOKEN = 'Jtnh4U+kC2Ze89L1dpQ4lhUGI6/12/TNZlk+kJgukS0uQoGM4dgBIxzx0SItK6cdRUiKowgwnqe1dNEEdqWVeQ=='
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
