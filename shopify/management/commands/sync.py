from django.core.management.base import BaseCommand

import os
import pymysql

from library import debug, common, shopify, markup

import environ
env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))

debug = debug.debug

BASEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Command(BaseCommand):
    help = 'Sync Mysql and Shopify'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "main" in options['functions']:
            self.main()

    def main(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        csr.execute(
            "SELECT MAX(ShopifyOrderID) FROM Orders")
        row = csr.fetchone()
        lastOrderId = row[0]

        ordersRes = shopify.getNewOrders(lastOrderId)

        for order in ordersRes['orders']:
            customer = order['customer']
            address = customer['default_address']

            # Import Address
            csr.execute(
                "CALL ImportAddress ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                    address['id'],
                    customer['id'],
                    address['last_name'],
                    address['first_name'],
                    address['company'],
                    address['address1'],
                    address['address2'],
                    address['city'],
                    address['province_code'],
                    address['zip'],
                    address['country'],
                    address['phone']
                )
            )
            con.commit()

            # Import Customer
            csr.execute(
                "CALL ImportCustomer ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                    customer['id'],
                    customer['email'],
                    customer['first_name'],
                    customer['last_name'],
                    customer['phone'],
                    address['id'],
                    customer['orders_count'],
                    customer['total_spent'],
                    customer['state'],
                    customer['note'],
                    customer['tags'],
                    customer['accepts_marketing'],
                    customer['created_at']
                )
            )
            con.commit()

            # Import Order
            orderId = order['id']

            shipping = order['shipping_lines'][0]
            shippingCost = float(shipping['price'])

            shippingMethod = shipping['title']
            if 'UPS Next Day Air' in shippingMethod:
                shippingMethod = 'UPS Next Day Air'
            if 'UPS 2nd Day Air' in shippingMethod:
                shippingMethod = 'UPS 2nd Day Air'

            specialShipping = ''
            if order['shipping_address']['country'] != 'United States' and order['shipping_address']['country'] != "US":
                specialShipping = 'International'
            elif shippingMethod == 'UPS Next Day Air':
                specialShipping = 'Overnight'
            elif shippingMethod == 'UPS 2nd Day Air':
                specialShipping = '2nd Day'
            elif '2nd Day Shipping for Samples' in shippingMethod:
                specialShipping = '2nd Day'
            elif 'Overnight Shipping for Samples' in shippingMethod:
                specialShipping = 'Overnight'

            isFraud = 0
            if 'Fraud' in order['tags']:
                isFraud = 1

            csr.execute(
                "CALL ImportOrder ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                    orderId,
                    order['order_number'],
                    order['email'],
                    order['phone'],
                    customer['id'],
                    order['billing_address']['last_name'],
                    order['billing_address']['first_name'],
                    order['billing_address']['company'],
                    order['billing_address']['address1'],
                    order['billing_address']['address2'],
                    order['billing_address']['city'],
                    order['billing_address']['province_code'],
                    order['billing_address']['zip'],
                    order['billing_address']['country'],
                    order['billing_address']['phone'],
                    order['shipping_address']['last_name'],
                    order['shipping_address']['first_name'],
                    order['shipping_address']['company'],
                    order['shipping_address']['address1'],
                    order['shipping_address']['address2'],
                    order['shipping_address']['city'],
                    order['shipping_address']['province_code'],
                    order['shipping_address']['zip'],
                    order['shipping_address']['country'],
                    order['shipping_address']['phone'],
                    shippingMethod,
                    specialShipping,
                    order['note'],
                    order['total_line_items_price'],
                    order['total_discounts'],
                    order['subtotal_price'],
                    order['total_tax'],
                    shippingCost,
                    order['total_price'],
                    float(order['total_weight']) / 453.592,
                    order['created_at'],
                    isFraud
                )
            )
            con.commit()

            # Import Shopping Cart
            line_items = order['line_items']

            manufacturers = []
            orderTypes = []

            for line_item in line_items:
                weight = float(line_item['grams'])
                if weight == 0:
                    weight = 453.592

                variantTitle = line_item['variant_title'].split('/')[0].strip()
                if 'Sample -' in variantTitle:
                    if 'Sample' not in orderTypes:
                        orderTypes.append('Sample')
                else:
                    if 'Order' not in orderTypes:
                        orderTypes.append('Order')

                manufacturer = line_item['vendor']
                if manufacturer not in manufacturers:
                    manufacturers.append(manufacturer)

                csr.execute(
                    "CALL ImportOrderShoppingCart ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                        orderId,
                        line_item['product_id'],
                        line_item['variant_id'],
                        line_item['quantity'],
                        line_item['title'],
                        variantTitle,
                        line_item['name'],
                        line_item['sku'],
                        manufacturer,
                        line_item['price'],
                        line_item['total_discount'],
                        weight / 453.592,
                        line_item['taxable']
                    )
                )
                con.commit()

            # Update Order Manufacturers and Types
            manufacturers.sort()
            orderTypes.sort()
            manufacturerList = ",".join(manufacturers)
            orderTypeList = "/".join(orderTypes)

            csr.execute(
                "UPDATE Orders SET OrderType = '{}', ManufacturerList = '{}' WHERE ShopifyOrderID = {}".format(
                    orderTypeList,
                    manufacturerList,
                    orderId
                )
            )
            con.commit()

            debug("Order", 0, "Downloaded Order {}".format(orderId))

        csr.close()
        con.close()
