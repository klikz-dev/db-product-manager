from django.core.management.base import BaseCommand
from monitor.models import Order

import os
import pymysql
import pytz

from library import config, debug, common, shopify, markup

db_host = config.db_endpoint
db_username = config.db_username
db_password = config.db_password
db_name = config.db_name
db_port = config.db_port

debug = debug.debug
sq = common.sq

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Pull Order Information from Shopify'

    def handle(self, *args, **options):
        # Order.objects.all().delete()

        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute("""
            Select *
            From Orders
            Where ShopifyOrderID Is Not NULL And OrderNumber Is Not NULL;
        """)
        orders = csr.fetchall()
        for order in orders:
            try:
                Order.objects.get(shopifyOrderId=order[0])
                continue
            except Order.DoesNotExist:
                pass

            try:
                Order.objects.create(
                    shopifyOrderId=order[0],
                    order_number=order[1],
                    email=order[2],
                    phone=order[3],
                    customer_id=order[4],
                    billing_first_name=order[6],
                    billing_last_name=order[5],
                    billing_company=order[7],
                    billing_address_1=order[8],
                    billing_address_2=order[9],
                    billing_city=order[10],
                    billing_state=order[11],
                    billing_zip=order[12],
                    billing_country=order[13],
                    billing_phone=order[14],
                    shipping_first_name=order[16],
                    shipping_last_name=order[15],
                    shipping_company=order[17],
                    shipping_address_1=order[18],
                    shipping_address_2=order[19],
                    shipping_city=order[20],
                    shipping_state=order[21],
                    shipping_zip=order[22],
                    shipping_country=order[23],
                    shipping_phone=order[24],
                    shipping_method=order[25],
                    order_note=order[26],
                    total_items=float(order[27]),
                    total_discounts=float(order[28]),
                    order_subtotal=float(order[29]),
                    order_tax=float(order[30]),
                    order_shipping_cost=float(order[31]),
                    order_total=float(order[32]),
                    weight=float(order[33]),
                    order_date=pytz.utc.localize(order[34]).astimezone(
                        pytz.timezone("America/New_York")),
                    initials=order[35],
                    status=order[36],
                    order_type=order[37],
                    manufacturer_list=order[38],
                    reference_number=order[39],
                    customer_emailed=order[40],
                    customer_called=order[41],
                    customer_chatted=order[42],
                    special_shipping=order[43],
                    customer_order_status=order[44],
                    note=order[45],
                    old_po=order[46],
                    is_fraud=order[47],
                )
                ooo = Order.objects.get(shopifyOrderId=order[0])
                debug("Order", 0,
                      "Success pulling Order Data. PO {}".format(order[1]))
            except:
                debug("Order", 2,
                      "Failed pulling Order Data. PO {}".format(order[1]))

            csr.execute("""
                Select *
                From Orders_ShoppingCart OS
                Left Join Orders O On O.ShopifyOrderID = OS.ShopifyOrderID
                Where O.ShopifyOrderID = '{}';
            """.format(ooo.shopifyOrderId))
            line_items = csr.fetchall()
            for line_item in line_items:
                try:
                    ooo.line_item_set.create(
                        shopifyOrderId=line_item[0],
                        product_id=line_item[1],
                        variant_id=line_item[2],
                        quantity=line_item[3],
                        ordered_product_title=line_item[4],
                        ordered_product_variant_title=line_item[5],
                        ordered_product_variant_name=line_item[6],
                        ordered_product_sku=line_item[7],
                        ordered_product_manufacturer=line_item[8],
                        ordered_product_unit_price=line_item[9],
                        ordered_product_line_discount=line_item[10],
                        ordered_product_unit_weight=line_item[11],
                        taxable=line_item[12],
                    )
                    debug(
                        "Order", 0, "Success adding Line Item to Order - PO {}. ProductID: {}".format(order[1], line_item[1]))
                except:
                    debug(
                        "Order", 2, "Failed adding Line Item to Order - PO {}. ProductID: {}".format(order[1], line_item[1]))
