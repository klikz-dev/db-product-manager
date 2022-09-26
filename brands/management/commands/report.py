import csv
import os
import datetime
import pytz
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db.models import Count

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

    def sample_only_customers(self):
        until = utc.localize(datetime.datetime(2022, 5, 31))
        customers = Customer.objects.annotate(
            num_samples=Count(~Q(orders__line_items__orderedProductVariantTitle__icontains='Sample - '))).filter(
                Q(num_samples=0) &
                Q(orders__orderDate__lte=until))

        with open(FILEDIR + '/files/report/sample_only_customers.csv', 'w', newline='') as csvfile:
            fieldnames = [
                "firstName",
                "lastName",
                "email",
                "phone",
                "orderCount",
                "totalSpent",
                "marketing"
            ]
            reportWriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
            reportWriter.writerow({
                "firstName": "First Name",
                "lastName": "Last Name",
                "email": "Email Address",
                "phone": "Phone Number",
                "orderCount": "Order Count",
                "totalSpent": "Order Total",
                "marketing": "Accept Marketing"
            })

            for customer in customers:
                if customer.acceptsMarketing:
                    marketing = "Yes"
                else:
                    marketing = "No"

                reportWriter.writerow({
                    "firstName": customer.firstName,
                    "lastName": customer.lastName,
                    "email": customer.email,
                    "phone": customer.phone,
                    "orderCount": customer.orderCount,
                    "totalSpent": customer.totalSpent,
                    "marketing": marketing
                })
