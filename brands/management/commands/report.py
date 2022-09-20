import csv
from itertools import count
import os
from django.core.management.base import BaseCommand

from library import debug
from shopify.models import Customer, Line_Item, Order

debug = debug.debug

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Check API Status'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "sample_only_customers" in options['functions']:
            self.sample_only_customers()

    def sample_only_customers(self):
        onlySampleCustomers = []
        customers = Customer.objects.all()

        total = len(customers)
        index = 0
        for customer in customers:
            index += 1
            debug("Reporting", 0, "Checking {}th customer out of {} customers".format(
                index, total))

            onlySamples = True

            orders = Order.objects.filter(customer=customer)
            if len(orders) == 0:
                continue

            for order in orders:
                line_items = Line_Item.objects.filter(order=order)
                for line_item in line_items:
                    if "Sample - " not in line_item.orderedProductVariantTitle:
                        onlySamples = False
                        break

                if not onlySamples:
                    break

            if onlySamples:
                onlySampleCustomers.append(customer)

        with open(FILEDIR + '/files/report/sample_only_customers.csv', 'w', newline='') as csvfile:
            fieldnames = [
                "url",
                "name",
                "email",
                "phone",
                "count",
                "total"
            ]
            reportWriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
            reportWriter.writerow({
                "url": "Shopify Admin URL",
                "name": "Name",
                "email": "Email Address",
                "phone": "Phone Number",
                "count": "Total Orders",
                "total": "Total Spent"
            })

            for customer in onlySampleCustomers:
                reportWriter.writerow({
                    "url": "https://decoratorsbest.myshopify.com/admin/customers/{}".format(customer.customerId),
                    "name": "{} {}".format(customer.firstName, customer.lastName),
                    "email": customer.email,
                    "phone": customer.phone,
                    "count": customer.orderCount,
                    "total": customer.totalSpent
                })
