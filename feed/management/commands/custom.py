from django.core.management.base import BaseCommand
from django.db.models import Q

import os
import environ
import pymysql
import requests
import environ


from library import debug

from shopify.models import Variant, Product
from mysql.models import ProductSubtype, Type
from feed.models import Schumacher

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

env = environ.Env()
SHOPIFY_API_URL = f"https://decoratorsbest.myshopify.com/admin/api/{env('shopify_api_version')}"
SHOPIFY_PRODUCT_API_HEADER = {
    'X-Shopify-Access-Token': env('shopify_product_token'),
    'Content-Type': 'application/json'
}


class Command(BaseCommand):
    help = "Custom Commands"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        processor = Processor()

        if "samplePrice" in options['functions']:
            processor.updateSamplePrices()

        if "deleteSubtypeTags" in options['functions']:
            processor.deleteSubtypeTags()

        if "getTypeList" in options['functions']:
            processor.getTypeList()

        if "refreshPrices" in options['functions']:
            processor.refreshPrices()


class Processor:
    def __init__(self):
        env = environ.Env()
        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

    def __del__(self):
        self.con.close()

    def updateSamplePrices(self):
        samples = Variant.objects.filter(
            name__icontains='Sample - ').exclude(name__icontains='Free Sample -').filter(price=5)

        total = len(samples)
        for index, sample in enumerate(samples):
            try:
                typeId = sample.product.productTypeId

                if typeId == 1 or typeId == 2 or typeId == 5:
                    newPrice = 7
                elif typeId == 4:
                    newPrice = 15
                else:
                    continue

                sample.price = newPrice
                sample.save()

                requests.put(f"{SHOPIFY_API_URL}/variants/{sample.variantId}.json", headers=SHOPIFY_PRODUCT_API_HEADER,
                             json={"variant": {'id': sample.variantId, 'price': sample.price}})

                debug.debug(
                    "Custom", 0, f"{index}/{total} -- updated '{sample.name}' price to ${sample.price}")

            except Exception as e:
                debug.debug("Custom", 1, str(e))
                continue

    def deleteSubtypeTags(self):
        csr = self.con.cursor()

        subtypeId = 65
        products = Schumacher.objects.filter(
            Q(type="Wallpaper") | Q(type="Fabric"))

        for product in products:
            sku = product.sku
            productId = product.productId

            if not sku or not productId:
                continue

            try:
                productSubtype = ProductSubtype.objects.get(
                    sku=sku, subtypeId=subtypeId)
                productSubtype.delete()

                csr.execute(
                    f"CALL AddToPendingUpdateTagBodyHTML ({productId})")
                self.con.commit()

                debug.debug(
                    "Custom", 0, f"Deleted Subtype {subtypeId} for SKU: {sku}, ProductId: {productId}")

            except ProductSubtype.DoesNotExist:
                continue

        csr.close()

    def getTypeList(self):
        types = Type.objects.filter(Q(parentTypeId=6) | Q(parentTypeId=7) | Q(
            parentTypeId=8) | Q(parentTypeId=40) | Q(parentTypeId=41))
        for type in types:
            print(type.name)
        print(len(types))

    def refreshPrices(self):
        csr = self.con.cursor()

        brandsRefreshed = ["Surya", "Kravet", "Brewster",
                           "Phillip Jeffries", "Scalamandre", "Pindler"]
        brandsToRefresh = ["Kravet", "Brewster",
                           "Phillip Jeffries", "Scalamandre", "Pindler"]

        for brand in brandsToRefresh:
            if brand in brandsRefreshed:
                continue

            csr.execute(f"""
                SELECT P.ProductId
                FROM Product P
                LEFT JOIN ProductManufacturer PM ON PM.SKU = P.SKU
                LEFT JOIN Manufacturer M ON M.ManufacturerID = PM.ManufacturerID
                WHERE M.BRAND = "{brand}" AND P.ProductId IS NOT NULL
            """)
            products = csr.fetchall()

            for product in products:
                productId = product[0]
                csr.execute(
                    "CALL AddToPendingUpdatePrice ({})".format(productId))
                self.con.commit()

                debug.debug(
                    "Custom", 0, f"Updated {brand} prices. Product {productId}")

        csr.close()
