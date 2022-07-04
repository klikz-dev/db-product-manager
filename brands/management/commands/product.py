from django.core.management.base import BaseCommand
from shopify.models import Product

import os
import pymysql
import pytz

from library import debug, common

import environ
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Build Product Database'

    def handle(self, *args, **options):
        # Product.objects.all().delete()

        con = pymysql.connect(host="db-rds1.cgldygmzacqd.us-east-1.rds.amazonaws.com", user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""
            Select *
            From Product
            Where ProductID Is Not NULL;
        """)
        products = csr.fetchall()
        for product in products:
            try:
                Product.objects.get(productId=product[0])
                continue
            except Product.DoesNotExist:
                pass

            try:
                Product.objects.create(
                    productId=product[1],
                    sku=product[0],
                    manufacturerPartNumber=product[3],
                    pattern=product[9],
                    color=product[10],
                    name=product[2],
                    bodyHTML=product[4],
                    title=product[5],
                    description=product[6],
                    handle=product[7],
                    collection=product[11],
                    productTypeID=product[8],
                    isOutlet=product[13],
                    published=product[15],
                    deleted=product[16],
                )
                ppp = Product.objects.get(productId=product[1])
                debug("Product", 0,
                      "Success pulling Product Data. ProductId {}".format(product[1]))
            except:
                debug("Product", 2,
                      "Failed pulling Product Data. ProductId {}".format(product[1]))
                continue

            csr.execute("""
                Select *
                From ProductVariant PV
                Left Join Product P On P.ProductID = PV.ProductID
                Where P.ProductID = '{}';
            """.format(ppp.productId))
            variants = csr.fetchall()
            for variant in variants:
                # try:
                if 1 == 1:
                    ppp.variant_set.create(
                        variantId=variant[0],
                        isDefault=variant[1],
                        name=variant[2],
                        position=variant[3],
                        sku=variant[4],
                        manufacturerPartNumber=variant[5],
                        productId=variant[6],
                        price=variant[7],
                        weight=variant[8],
                        cost=variant[9],
                        pricing=variant[10],
                        minimumQuantity=variant[11],
                        restrictedQuantities=variant[12],
                        gtin=variant[13],
                        published=variant[14],
                        backOrderStatus=variant[18],
                    )
                    debug(
                        "Product", 0, "Success adding Variant to Product - VariantId {}. ProductID: {}".format(variant[0], product[1]))
                # except:
                #     debug(
                #         "Product", 2, "Failed adding Variant to Product - VariantId {}. ProductID: {}".format(variant[0], product[1]))
