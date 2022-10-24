import os
import datetime
import time
import pytz
from django.core.management.base import BaseCommand
from django.db.models import Q

from library import debug
from monitor.models import NoOrderCustomers, Profit
from shopify.models import Customer, Line_Item, Order

debug = debug.debug
utc = pytz.UTC


FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Check API Status'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "noOrder" in options['functions']:
            self.noOrder()

        if "profit" in options['functions']:
            self.profit()

        if "main" in options['functions']:
            while True:
                self.noOrder()
                self.profit()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def noOrder(self):
        lastCustomer = NoOrderCustomers.objects.last()
        if lastCustomer:
            fromCustomer = lastCustomer.customerId
        else:
            fromCustomer = 0

        customers = Customer.objects.filter(
            Q(createdAt__gte=utc.localize(datetime.datetime(2022, 1, 1))) & Q(customerId__gte=fromCustomer))

        for customer in customers:
            onlySamples = True
            orders = Order.objects.filter(customer=customer)
            if len(orders) == 0:
                continue

            for order in orders:
                line_items = Line_Item.objects.filter(Q(order=order) & ~Q(
                    orderedProductVariantTitle__icontains='Sample - '))

                if len(line_items) > 0:
                    onlySamples = False
                    break

            if onlySamples:
                if customer.acceptsMarketing:
                    marketing = "Yes"
                else:
                    marketing = "No"

                debug("Reporting", 0, "Importing customer #{}".format(
                    customer.customerId))

                NoOrderCustomers.objects.create(
                    customerId=customer.customerId,
                    firstName=customer.firstName,
                    lastName=customer.lastName,
                    email=customer.email,
                    marketing=marketing,
                    date=customer.createdAt
                )

    def profit(self):
        lastProfit = Profit.objects.last()
        if lastProfit:
            fromPO = lastProfit.po
        else:
            fromPO = 0

        orders = Order.objects.filter(Q(createdAt__gte=utc.localize(
            datetime.datetime(2022, 1, 1))) & Q(orderNumber__gt=fromPO))

        for order in orders:
            lineItems = Line_Item.objects.filter(order=order)

            cost = 0
            for lineItem in lineItems:
                try:
                    cost += lineItem.variant.cost * lineItem.quantity
                except Exception as e:
                    print(e)
                    continue

            debug("Reporting", 0, "Importing PO #{}".format(order.orderNumber))

            Profit.objects.create(
                po=order.orderNumber,
                type=order.orderType,
                cost=cost,
                price=order.orderTotal,
                date=order.orderDate
            )
