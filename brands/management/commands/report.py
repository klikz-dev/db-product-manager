import csv
import os
import datetime
import time
import pytz
from django.core.management.base import BaseCommand
from django.db.models import Q

from library import debug
from monitor.models import Profit
from shopify.models import Customer, Line_Item, Order

debug = debug.debug
utc = pytz.UTC


FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Check API Status'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "sample_only_customers" in options['functions']:
            self.sample_only_customers()

        if "profit" in options['functions']:
            while True:
                self.profit()
                time.sleep(86400)

    def profit(self):
        lastProfit = Profit.objects.last()
        if lastProfit:
            fromPO = lastProfit.po
        else:
            fromPO = 0

        orders = Order.objects.filter(orderNumber__gt=fromPO)

        for order in orders:
            lineItems = Line_Item.objects.filter(order=order)

            cost = 0
            for lineItem in lineItems:
                try:
                    cost += lineItem.variant.cost * lineItem.quantity
                except Exception as e:
                    print(e)
                    continue

            print(order.orderNumber, cost, order.orderTotal,
                  order.orderTotal - cost, order.orderDate)

            Profit.objects.create(
                po=order.orderNumber,
                type=order.orderType,
                cost=cost,
                price=order.orderTotal,
                date=order.orderDate
            )

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
                if order.orderDate < utc.localize(datetime.datetime(2022, 6, 1)) or order.orderDate > utc.localize(datetime.datetime(2022, 7, 31)):
                    continue

                line_items = Line_Item.objects.filter(Q(order=order) & ~Q(
                    orderedProductVariantTitle__icontains='Sample - '))

                if len(line_items) > 0:
                    onlySamples = False
                    break

            if onlySamples:
                onlySampleCustomers.append(customer)

        with open(FILEDIR + '/files/report/sample_only_customers.csv', 'w', newline='') as csvfile:
            fieldnames = [
                "firstName",
                "lastName",
                "email",
                "marketing"
            ]
            reportWriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
            reportWriter.writerow({
                "firstName": "First Name",
                "lastName": "Last Name",
                "email": "Email Address",
                "marketing": "Accept Marketing"
            })

            for customer in onlySampleCustomers:
                if customer.acceptsMarketing:
                    marketing = "Yes"
                else:
                    marketing = "No"

                reportWriter.writerow({
                    "firstName": customer.firstName,
                    "lastName": customer.lastName,
                    "email": customer.email,
                    "marketing": marketing
                })
