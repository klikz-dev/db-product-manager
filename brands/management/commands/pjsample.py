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
API_COOKIE = '__utmz=198764782.1699939069.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _gcl_au=1.1.739037927.1699939070; 6286=acc1c94ede758e1e9d88f0f16e8564a9; _pin_unauth=dWlkPU4yWTRZakU1TnpBdE1qWTVZeTAwTWpZMkxUazRObU10TUdJMk1HSmxaR0ppTVRRNA; _hjSessionUser_1552480=eyJpZCI6ImRhMTQ3NWNhLTJjOGMtNTA3OC04NjhjLWQ4MGE5YWQ3ZmFjYSIsImNyZWF0ZWQiOjE2OTk5MzkwNzcxMDUsImV4aXN0aW5nIjp0cnVlfQ==; _fbp=fb.1.1699939078501.483039036; _tt_enable_cookie=1; _ttp=e7hSTLeuiwOtLVxf07g__pVF7au; __hs_cookie_cat_pref=1:true,2:true,3:true; hubspotutk=fa95d840022948cfc30217f4bf7c405c; remember_me_token=Rf0dzwohuEyh7jZRHGjtig; __utma=198764782.1993769856.1699939069.1705305713.1706545586.7; __utmc=198764782; __utmt=1; _gid=GA1.2.270494123.1706545588; _hjSession_1552480=eyJpZCI6IjAxZDkwMDVhLWQwMmMtNDNlNC1iMjUxLWJhNzVlNjkyOTQ3NiIsImMiOjE3MDY1NDU1OTE2MzQsInMiOjEsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; __hstc=105233308.fa95d840022948cfc30217f4bf7c405c.1699939117394.1705305720552.1706545594230.7; __hssrc=1; _gat_UA-123650249-3=1; _ga_KWQMVELYQV=GS1.1.1706545587.8.1.1706545653.59.0.0; _ga=GA1.1.1993769856.1699939069; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2Fwallcoverings; __hssc=105233308.4.1706545594230; __utmb=198764782.4.10.1706545586; _phillip_jeffries_session=QUszU1ZVbmprV2NSNTFXSWlva2hUZkUrVTAyYzlEM2JpSHl5VnJuVkl4Ym9XK1NNRFlXQ3RyaE4venZyd0ZqZGRldG01SnRmYy9NbmM4MnN3VzE2V28yWTh4VkhFUzNGSEdIT2tMTDF5WGNmd055QytFTzgzbmNhSy9ZelhEWGhpekhYWi9tOVQ3R3U2ZWlEdGJzeGNhaThrOE5FVEp3WWlWSUFVQmNCV0wyTGRBblNDUGdUN2hsV0JpZEs5KzA5RXBNUWZNc3BHNUNQdDFvT2pNMVFLdyt3Z3BiMlhqbzZXcHpFdW9icHNDazNDZCs3V0VGZWY0bjRZelByNDBhdDNRUEhMdndOWjRuYVBiZWg4L25IMUJkbGVBYjlqc2R3M25hb3lka0xmQ1dJcDc4cXBoV0R3Uy9HYkJMSXU0NzdrQmFpTDdNSWp2NlUzeW51a0c2Nm44OFBiMlpvODBKV1VEenJKckhudE8vK3N0K21qWSs1RUxxdHZYTzJkQi9VS3Vza25sQ1lWWlNHanUxVGtzaFo2R3NrR09xcCtZVjdlbkxtZE1KUU1rL1RMSWxqcEtkS1VyWUZiWHB6N1RzNWp6SS8wUlZUdDdWMlVnMG1kc2hYbFlvdzRHUG8vZWZYa0wzcnJia1lxVHZCa0VPRzc5VGhxM2NTcUMycGQyVEdrU1A0TnBaTVhnZGlFRXhzejM1QVl6U1h3T29HU2g2TXMwaVZIVEJ5UVdkdkVQak1KZkRyU0JmeldHRHg2MXpEdGFjNHhvVS9pKzQ2Q3ppYmdMbUsxeDljdzZRTEhwTmJKbDdnR0Y1a2tyUEQ1Qzh4bFBRcndvVE54WTY1Y1lkSUswYm1wSElRRCtleVlGdUd0Qzh4Vk5tRmlJS0w4WVNiaVpCZFUwUW4vS2hBYzBvMXllbXJOZ2RrenVYcVc4YmpmaW56WXc1dnFVanF0ZXQ0NFcyZ2pLS1BVMXRvQW5oS0J5ZTZGaW9VVXRSdWFua3VNZXBjbG5GYXZjY3FkK2QvQWNPMzZkam9MY2VQaVdzdjJrdUJ2eWg4WnMrNGRTL3ZyR2VIaW5SSE9ZRFVtWTJrZ0I5N1Vua2xpdUpSa0s2SUVBTGQ1dWdyRjVUdmJDa2FOaHRmc1BOeUwzeGpoM2tUcXF3VWhiRkR6eEk9LS15K0REbWdxTlR3TGN0dUNiVlh4QUlBPT0%3D--4784bedc48b8faa08343656b352eff49cd9a8921'
API_TOKEN = 'MXhOPPDjhIVHfyZXU4kwM9cCPVxXkrLIAbWRD4hC7LRv7Nb6ufNGTRH6ex34+Fh3UUY4cNLPR0Z0jzrvkm93ZQ=='
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
