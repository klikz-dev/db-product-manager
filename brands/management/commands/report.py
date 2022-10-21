import csv
import os
import datetime
import pytz
from django.core.management.base import BaseCommand
from django.db.models import Q

from library import debug
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
            self.profit()

    def profit(self):
        with open(FILEDIR + '/files/report/cost_of_goods.csv', 'w', newline='') as csvfile:
            fieldnames = [
                "po",
                "type",
                "cost",
                "price",
                "profit",
                "date"
            ]
            reportWriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
            reportWriter.writerow({
                "po": "#PO",
                "type": "Order Type",
                "cost": "Cost of Goods",
                "price": "Order Total",
                "profit": "Profit",
                "date": "Order Date"
            })

            orders = Order.objects.filter(
                Q(orderDate__gte=utc.localize(datetime.datetime(2022, 1, 1))) & Q(orderDate__lte=utc.localize(datetime.datetime(2022, 9, 30))))

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

                reportWriter.writerow({
                    "po": order.orderNumber,
                    "type": order.orderType,
                    "cost": cost,
                    "price": order.orderTotal,
                    "profit": order.orderTotal - cost,
                    "date": order.orderDate
                })

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
