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
API_COOKIE = '_gcl_au=1.1.1320949834.1681755148; __utmz=198764782.1681755149.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _fbp=fb.1.1681755150011.462367147; _tt_enable_cookie=1; _ttp=nHxtJKF1h1MfEXdShT1cjcgHcQ6; _pin_unauth=dWlkPU9HVXpZMk14T1RjdE4yVTVNaTAwWVRCbExXSTRPRFF0TVdZNVlUTmhaVFE0TXpCbQ; 6286=0c2536ae7f113b51c2a9bcab1130cc3e; _hjSessionUser_1552480=eyJpZCI6IjMyYTU5NmIzLTc1OTItNTA5OS1iNTIxLTFhZDg0ZmUyMWMzNCIsImNyZWF0ZWQiOjE2ODE3NTUxNTA2ODgsImV4aXN0aW5nIjp0cnVlfQ==; hubspotutk=115e67ff27c658d76334ec95ce7e008d; __hs_cookie_cat_pref=1:true,2:true,3:true; __utma=198764782.1515365840.1681755149.1681755149.1683011405.2; __utmc=198764782; __utmt=1; _gid=GA1.2.602725981.1683011409; ln_or=eyIxMDQ2MDk4IjoiZCJ9; _hjIncludedInSessionSample_1552480=1; _hjSession_1552480=eyJpZCI6ImRjMTIxM2I3LTc5NGMtNGQ5Yi05ZjNiLTJkOGEzYTRjODE2OSIsImNyZWF0ZWQiOjE2ODMwMTE0MTk3NDUsImluU2FtcGxlIjp0cnVlfQ==; _hjAbsoluteSessionInProgress=0; __hstc=105233308.115e67ff27c658d76334ec95ce7e008d.1681755153945.1681755153945.1683011430226.2; __hssrc=1; _gat_UA-123650249-3=1; __utmb=198764782.4.10.1683011405; __hssc=105233308.4.1683011430226; _ga_KWQMVELYQV=GS1.1.1683011416.2.1.1683011484.52.0.0; _ga=GA1.1.1419347136.1681755149; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2Fwallcoverings; _phillip_jeffries_session=NXc1cStITHNpN1ZIMU45VGZGQ1Bya1FjNjBucWd5UjVhRWl2QUkrc1hqMmVvUWFyeFVkcGhJUXFEbjdHcEI2MEtydk13NHI4TURlOTY0VGdxakE5ZGMySzlKNm9BNmhodEY0MHZuWDNjL0VWcDJDYTVjVDRkQjRReGtHU2lBT2kvbldrTThYbjYyYTBXaDFEUDZ1SC9URFArUW9RbVIvYVJaYlFFdC92bUZnZHhiNytWaUs0a3h2blMxeW1qeHUxazcrTjlMOTJhdFJqOXgwNmkxNmxsSFNYaXlqQVQ3YlhRTEFCbXB2SGNURjRPUUN1MXBDTTNTMXhmb2VPQzNkZmJIblIxWmdkMytUWDczOVk4c1lyZXFSYVhXSFh0YllnWTJTQmpMcXR6QUVLbzkyamxvYnptSlRVVU10NlBPZ1FaMStFRkJhaXlHM09oVExTRW92UE1VYmxYZ2FycEplV0hObWJNU2Z3TXEwY0w3WUlnKzVUWW9veUlwYmRUUUxOTzFSWEEzM2RNUTI2clk4b21DbjVVbW1VS3ZVQkh0ellDQkJFYVBDTmV1V2NQYUZZSStvM3ZjeDZSN1NJa2NiclY5UE1LZVhRU3dscXNod1pLbkJwV3ZpNnRtS3lsc2dMNmxqeU04d21OY25GTTBBOXBNdENSeTlaUVZLT0lSeFIwZ0wxeUM0U2krT3RrS0ZadHV1WVlzbk1kZkQzcUgxRVRDQWw3Rmx1YzJHUXFKMnpGYk8rWU50dFV6SU9lRlJkM0NyeUVQaGVZN1RWcjNFVTlESXJhRkllRXZSdEQ1RTNmQUp6WkdNeXozRmJJbCtESUE1L052SnlHclFzd1ZWSXAyd2ZTUExObHVYc0RjVW1Mb3NHa3M3STFKbzFYbjdJOFFmWDl4Ri9sNUsxbjRNUHBrdkxvN0FaR2N6eXlPeFU3c0wzRDBoNW1zYnY0RUd0b3hXcFJYSVpPUDBudmlMZEZxRjAwNnpka2hFQ1FKZGlBeXE4MlRwcUV0a1oraHkzaDNiZWw5M2o1d0hCaTJWdWhXdEsxNkpPTjlKRCtUVlZVZDRVdE5adFRUWVZIVDhtckZyN2lQYWNYZlRFK2N3SGkxTzVVQ2hsN29rY01XWXY2OTYyaXo0US9jWDhjKzYzWVB0Y1ltTGljUWM9LS02RFFjV2xXbkNFay8zT2dQZ3pFekFRPT0%3D--4427c1a6d19bd87e9b5f81d3934094d16e51a9a8'
API_TOKEN = 'd5C27pjl4zehpM03VsOzGTJsYptfax26UR5ECWcrfrsSRlQNK7vuQ7STgqHHg5PyXhMCUhD0W0W40hzUp7DNeg=='
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
