from django.core.management.base import BaseCommand
from django.db.models import Q

import environ
import json
import requests
import pymysql
import time
import environ
from datetime import datetime, timedelta
from django.utils.timezone import make_aware

from library import debug

from shopify.models import Order, Product, ProductImage, Variant

env = environ.Env()


class Command(BaseCommand):
    help = "Send Klaviyo Email"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "sample-reminder" in options['functions']:
            with Processor() as processor:
                processor.sampleReminder()


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

        self.key = env('klaviyo_key')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def sampleReminder(self):
        debug.debug("Klaviyo", 0, "Sending Sample reminder emails")

        date_fourteen_days_ago = (datetime.now() - timedelta(days=14)).date()

        start_of_day = make_aware(datetime.combine(
            date_fourteen_days_ago, datetime.min.time()))
        end_of_day = make_aware(datetime.combine(
            date_fourteen_days_ago, datetime.max.time()))

        orders = Order.objects.exclude(
            orderType="Order"
        ).filter(
            status="Processed",
            orderDate__range=(start_of_day, end_of_day)
        )

        for order in orders:
            email = order.email
            firstName = order.shippingFirstName
            lastName = order.shippingLastName
            lineItems = order.line_items.all()

            item = None
            for lineItem in lineItems:
                if "Sample" in lineItem.orderedProductVariantTitle and not "Free Sample" in lineItem.orderedProductVariantTitle:
                    item = lineItem

            if not item:
                continue

            sku = item.orderedProductSKU
            title = item.orderedProductVariantTitle

            try:
                product = Product.objects.get(sku=sku)
                productImage = ProductImage.objects.get(
                    productId=product.productId, imageIndex=1)
            except Exception as e:
                continue

            variant = None
            try:
                variants = Variant.objects.filter(productId=product.productId).exclude(
                    Q(name__startswith='Sample') |
                    Q(name__startswith='Trade') |
                    Q(name__startswith='Free Sample')
                )
                if len(variants) > 0:
                    variant = variants[0]
            except Exception as e:
                continue

            if not variant:
                continue

            print(variant.price, variant.pricing)

            data = {
                "dp": {
                    "actual_oid": order.orderNumber,
                    "t": title,
                    "img": productImage.imageURL,
                    "sku": sku,
                    "u": f"https://www.decoratorsbest.com/products/{product.handle}",
                    "unitprice": f"{variant.price}",
                    "pricetype": f"{variant.pricing}"
                }
            }

            self.send(
                templateId="UKA5M2",
                subject="Have You Received Your Samples?",
                data=data,
                customer=f"{firstName} {lastName}",
                email=email
            )

    def send(self, templateId, subject, data, customer, email):
        TOKEN = 'pk_6018d42538bc1a647c4b4c4f2670db76dc'

        payload = {
            'api_key': TOKEN,
            'from_email': 'orders@decoratorsbest.com',
            'from_name': 'DecoratorsBest',
            'subject': subject,
            'to': json.dumps([
                {'email': email, "name": customer}
            ]),
            'context': json.dumps(data)
        }

        response = requests.post(
            f'https://a.klaviyo.com/api/v1/email-template/{templateId}/send',
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data=payload)

        print(response.text)
