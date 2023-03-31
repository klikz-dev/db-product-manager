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
API_COOKIE = '__utmz=198764782.1676364716.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _gcl_au=1.1.796977913.1676364717; _tt_enable_cookie=1; _ttp=OaImm8shp1H2v6fYNNP8obg1y2E; _fbp=fb.1.1676364718240.2061779072; _pin_unauth=dWlkPU5qTTVPREZqWkRRdFlqazBZeTAwTkRBNUxUazJPRGd0Wm1ZMk5qVm1NRGxqTm1FeQ; hubspotutk=8e23cf84c2f5cdc40931199164511e28; __hs_cookie_cat_pref=1:true,2:true,3:true; _hjSessionUser_1552480=eyJpZCI6IjA5YmUzOTZhLWFiNjQtNTU0NC04ZWJhLTk4ODllOWJlZmE4YyIsImNyZWF0ZWQiOjE2NzYzNjQ3MTg3ODMsImV4aXN0aW5nIjp0cnVlfQ==; 6286=8b37cdf646cc2717d949306576222229; remember_me_token=cMrRDFdmn5JLIbLOtWdc_g; __utma=198764782.1219712163.1676364716.1678686095.1680286559.22; __utmc=198764782; _gid=GA1.2.1853960080.1680286561; ln_or=eyIxMDQ2MDk4IjoiZCJ9; _hjSession_1552480=eyJpZCI6IjA2NjhlYjY2LTk4MjEtNDQyMi1hMGY0LWY3YmNjNmQxZTlmNiIsImNyZWF0ZWQiOjE2ODAyODY1NjM3MzIsImluU2FtcGxlIjp0cnVlfQ==; _hjAbsoluteSessionInProgress=0; __hstc=105233308.8e23cf84c2f5cdc40931199164511e28.1676364719308.1678686101593.1680286568778.23; __hssrc=1; _hjIncludedInSessionSample_1552480=1; _gat_UA-123650249-3=1; __utmt=1; _ga_KWQMVELYQV=GS1.1.1680286560.24.1.1680287260.45.0.0; _ga=GA1.2.2049969643.1676364717; return_to=https%3A%2F%2Fwww.phillipjeffries.com%2Fshop%2Fwallcoverings; _phillip_jeffries_session=YXpZZktRRCtrdjF4dUFsMjNZazhQMjd6WXEyRVFQWDZ6SCtSV1M1Tk1lNXFJMllzTlcreWNkRllRTDJJU0F3RjZXRm5MdVE0RlAxS0VOejZRM3REWldKaHljNUh4VDUzYU9pYi9xZVMrSzJZdTFialVVNUJ6YXA1bS8ra01ZL25GV0ZaaUd6NXRmVUxRdXNOUDhwT2ZyZU9SbHBrR2JDc3RDZ1pFSUNvN1FkcGM4YWhzUDFycHpLVlpHbC9WRVI2K2ZBTm90MFY3TmdsWE1sNTBNVkF0ZXpiMjRLa0V6Y1ZZaTk3dnBpN1NXcHJjM2Q0OStOMGdDaksyV2dnZnpTU1hkWDVoWGx4SjNpUTVoWGFLUDNIblpkQStBRU5WRmJ4S1luQ3p6bCtxYnlQYXFUK2haUzl2V2dYaXFUdjNOV0lNSXN4M3ZsTlEyUjBvZTNCMHA5dkZvZzRhcmh4eU9tSi9mSm0yT1NXeHZrUXRWUDN5NUJQTXRDb3dsZ0FmeXc4MHlMamFSRzBkTzJ2dTJ6c0lVNlN5cC9ua001Z3NNcmVNTEFOUUtlQmNKblovZXd0ZGhlVzk4OXVjdkxuY2FQUC9nNFp2b0pmQkZYcTAwWi9Lai83OWdoNFJXRGdsNktTaVJTTGNqejI4YzJaYkRxL1p5N1VqeHR3YWdkNER2RjhFbVFYWVZVMkZyQW9hYzhqMS9lNkhBbzJXRGhLK25tVWovZ1JhT0FiZVdpWEQ3UU5YV1RBQTFtaVA4amNLQ3YzZ2pWR21WNzdTMVF5MitESFpMWmNzVDRhclNKMWVHYmc3dnFPZWxpQzhoNTlYbDc5SjVMN2VnMG1aN2syQmNKQkxNRC8wblhIUHF0eElrbVdtUkVnbVExaG8rTkx2eWpkUFJ5SmUrREhGb0F5SEJuMkVSR25iUjhzdVFYZzVxTXlXYkxBRXZ5MGVJTUEyeWFLOWZJM1JZcUI3Y3JBSVF0UTJwMmVwQXFXSTV0L0owWHNTc2w4NGR6d2xQT1IvTjkzMnpaMEZod0tNWlFSczN4a2E3MVJTb09HUU9BT1g4amp5d0p1TkFCNzVRZHBHblhpdENxUlBFdTZuZ0E0dTB4djRxcFFwT1BMUWNSbUhYOHkwMmh0SC9DQmhlaWNqS1dmQ0ZaZ3NMUDBtb2s9LS00TjVzbkRUNDNkRCtwblJER0NkR09RPT0%3D--d0cfee19c3257cd7a36b04837d8bb269a44232b0; __hssc=105233308.4.1680286568778; __utmb=198764782.5.10.1680286559'
API_TOKEN = 'AnfaWgmnFeRpWbKYLybCKqjLPo+iTqE2/1Z8UtKYCMZ3cbqg3TVpFPnikSnz6v4loAyvKps9hMoGdJFHbinq/Q=='
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
