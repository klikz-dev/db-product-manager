from django.core.management.base import BaseCommand
from brands.models import Scalamandre
from shopify.models import Product as ShopifyProduct

import requests
import json
import pymysql
import os
import time

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

markup_price = markup.scalamandre
markup_pillow = markup.scalamandre_pillow
markup_trade = markup.scalamandre_trade

debug = debug.debug
sq = common.sq


FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# API credentials
API_ADDRESS = 'http://scala-api.scalamandre.com/api'
API_USERNAME = 'Decoratorsbest'
API_PASSWORD = 'EuEc9MNAvDqvrwjgRaf55HCLr8c5B2^Ly%C578Mj*=CUBZ-Y4Q5&Sc_BZE?n+eR^gZzywWphXsU*LNn!'


# Get API token
r = requests.post("{}/Auth/authenticate".format(API_ADDRESS), headers={'Content-Type': 'application/json'},
                  data=json.dumps({"Username": API_USERNAME, "Password": API_PASSWORD}))
j = json.loads(r.text)
API_TOKEN = j['Token']


class Command(BaseCommand):
    help = 'Build Scalamandre Database'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "getProducts" in options['functions']:
            self.getProducts()