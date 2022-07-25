from library.debug import debug
import os
import requests
import math
import shutil
import datetime
import pytz

import urllib.request

opener = urllib.request.build_opener()
opener.addheaders = [
    ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def picdownload(link, name):
    try:
        f1 = open(DIR + "/images/product/" + name, "wb")
        f1.write(requests.get(link).content)
        f1.close()
    except Exception as e:
        print(e)
        debug("Image", 1, "Image Download Failed. {}".format(link))


def picdownload2(link, name):
    try:
        urllib.request.urlretrieve(link, DIR + "/images/product/" + name)
        debug("Image", 0, "Downloaded thumbnail {}".format(name))
    except Exception as e:
        print(e)
        debug("Image", 1, "Image Download Failed. {}".format(link))


def roomdownload(link, name):
    try:
        urllib.request.urlretrieve(link, DIR + "/images/roomset/" + name)
        debug("Image", 0, "Downloaded roomset {}".format(name))
    except Exception as e:
        print(e)
        debug("Image", 1, "Image Download Failed. {}".format(link))


def formatprice(x, markUp):
    ret = math.ceil(x * markUp * 4) / 4
    if ret == int(ret):
        ret -= 0.01
    return float(ret)


def sq(x):
    return "N'" + x.replace("'", "''") + "'"


def backup():
    try:
        shutil.copyfile(DIR + '/main.sqlite3', DIR + '/backup/main-' + datetime.datetime.now(
            pytz.timezone('US/Eastern')).strftime("%Y-%m-%d") + '.sqlite3')
        shutil.copyfile(DIR + '/monitor.sqlite3', DIR + '/backup/monitor-' +
                        datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%Y-%m-%d") + '.sqlite3')
        debug("Manage", 0, "Database Backup Completed.")
    except Exception as e:
        print(e)
        debug("Manage", 1, "Database Backup Failed. {}".format(e))


def importOrder(order, con):
    csr = con.cursor()

    customer = order['customer']
    address = customer['default_address']

    # Import Address
    csr.execute(
        'CALL ImportAddress (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (
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
        'CALL ImportCustomer (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (
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

    specialShipping = ''
    shippingMethod = ''
    shippingCost = 0

    if len(order['shipping_lines']) > 0:
        shipping = order['shipping_lines'][0]
        shippingCost = float(shipping['price'])

        shippingMethod = shipping['title']
        if 'UPS Next Day Air' in shippingMethod:
            shippingMethod = 'UPS Next Day Air'
        if 'UPS 2nd Day Air' in shippingMethod:
            shippingMethod = 'UPS 2nd Day Air'

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

    shipping_last_name = order['billing_address']['last_name']
    shipping_first_name = order['billing_address']['first_name']
    shipping_company = order['billing_address']['company']
    shipping_address1 = order['billing_address']['address1']
    shipping_address2 = order['billing_address']['address2']
    shipping_city = order['billing_address']['city']
    shipping_province_code = order['billing_address']['province_code']
    shipping_zip = order['billing_address']['zip']
    shipping_country = order['billing_address']['country']
    shipping_phone = order['billing_address']['phone']

    if order.get('shipping_address'):
        shipping_last_name = order['shipping_address']['last_name']
        shipping_first_name = order['shipping_address']['first_name']
        shipping_company = order['shipping_address']['company']
        shipping_address1 = order['shipping_address']['address1']
        shipping_address2 = order['shipping_address']['address2']
        shipping_city = order['shipping_address']['city']
        shipping_province_code = order['shipping_address']['province_code']
        shipping_zip = order['shipping_address']['zip']
        shipping_country = order['shipping_address']['country']
        shipping_phone = order['shipping_address']['phone']

    csr.execute(
        'CALL ImportOrder (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (
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
            shipping_last_name,
            shipping_first_name,
            shipping_company,
            shipping_address1,
            shipping_address2,
            shipping_city,
            shipping_province_code,
            shipping_zip,
            shipping_country,
            shipping_phone,
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

    csr.execute("""DELETE FROM Orders_ShoppingCart
        WHERE ShopifyOrderID = '{}';""".format(orderId))
    con.commit()

    for line_item in line_items:
        try:
            if line_item['variant_title'] == None or line_item['variant_title'] == "" or line_item['vendor'] == None or line_item['vendor'] == "":
                continue

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
                'CALL ImportOrderShoppingCart (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (
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

        except Exception as e:
            print(e)
            debug("Order", 2, "Import Order error: PO {}".format(
                order['order_number']))
            return

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

    # Import Order Attributes
    attrs = order['note_attributes']
    status = ""
    initials = ""
    manufacturerList = ""
    referenceNumber = ""

    for attr in attrs:
        if attr['value'] != "" and attr['value'] != None:
            if attr['name'] == "Status":
                status = attr['value']
                csr.execute(
                    "UPDATE Orders SET Status = '{}' WHERE ShopifyOrderID = {}".format(
                        status,
                        orderId
                    )
                )
                con.commit()
            if attr['name'] == "Initials":
                initials = attr['value']
                csr.execute(
                    "UPDATE Orders SET Initials = '{}' WHERE ShopifyOrderID = {}".format(
                        initials,
                        orderId
                    )
                )
                con.commit()
            if attr['name'] == "ManufacturerList":
                manufacturerList = attr['value']
                csr.execute(
                    "UPDATE Orders SET ManufacturerList = '{}' WHERE ShopifyOrderID = {}".format(
                        manufacturerList,
                        orderId
                    )
                )
                con.commit()
            if attr['name'] == "ReferenceNumber":
                referenceNumber = attr['value']
                csr.execute(
                    "UPDATE Orders SET ReferenceNumber = '{}' WHERE ShopifyOrderID = {}".format(
                        referenceNumber,
                        orderId
                    )
                )
                con.commit()

    debug("Order", 0,
          "Downloaded Order {} / {}".format(order['order_number'], orderId))

    csr.close()
