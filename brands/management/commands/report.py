import os
import datetime
import time
import pytz
from django.core.management.base import BaseCommand
from django.db.models import Q
import csv

from library import debug
from monitor.models import NoOrderCustomers, Profit
from shopify.models import Customer, Line_Item, Order, Address

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

        if "exportCustomers" in options['functions']:
            self.exportCustomers()

        if "main" in options['functions']:
            while True:
                self.noOrder()
                self.profit()
                print("Completed process. Waiting for next run.")
                time.sleep(86400)

    def fm(self, string):
        if string == None:
            return ""
        return str(string).replace("None", "").strip()

    def exportCustomers(self):
        customers = Customer.objects.all()

        with open(FILEDIR + '/files/customers.csv', 'w', newline='') as csvfile:
            poWriter = csv.DictWriter(csvfile, fieldnames=[
                'fname',
                'lname',
                'email',
                'phone',
                'street1',
                'street2',
                'city',
                'state',
                'zip',
                'country',
                'company',
            ])

            poWriter.writerow({
                'fname': 'First Name',
                'lname': 'Last Name',
                'email': 'Email',
                'phone': 'Phone Number',
                'street1': 'Street 1',
                'street2': 'Street 2',
                'city': 'City',
                'state': 'State',
                'zip': 'Zip',
                'country': 'Country',
                'company': 'Company'
            })

            for customer in customers:
                address = Address.objects.get(
                    addressId=customer.defaultAddressId)

                fname = self.fm(customer.firstName).title()
                lname = self.fm(customer.lastName).title()
                email = self.fm(customer.email).lower()
                phone = self.fm(address.phone)
                street1 = self.fm(address.address1).title()
                street2 = self.fm(address.address2).capitalize()
                city = self.fm(address.city).title()
                state = self.fm(address.state).upper()
                zip = self.fm(address.zip).upper()
                country = self.fm(address.country).title()
                company = self.fm(address.company).title()

                if fname == "" or email == "":
                    continue

                poWriter.writerow({
                    'fname': fname,
                    'lname': lname,
                    'email': email,
                    'phone': phone,
                    'street1': street1,
                    'street2': street2,
                    'city': city,
                    'state': state,
                    'zip': zip,
                    'country': country,
                    'company': company
                })

                print("{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}".format(
                    fname, lname, email, phone, street1, street2, city, state, zip, country, company))

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
