from library import debug, emailer
import environ
from library.debug import debug
import os
import requests
import math
import shutil
import datetime
import pytz

import urllib.request

from shopify.models import Address, Customer, Line_Item, Order, Variant
from mysql.models import Manufacturer

opener = urllib.request.build_opener()
opener.addheaders = [
    ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()

db_host = env('MYSQL_HOST')
db_username = env('MYSQL_USER')
db_password = env('MYSQL_PASSWORD')
db_name = env('MYSQL_DATABASE')
db_port = int(env('MYSQL_PORT'))


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


def importOrder(shopifyOrder):
    shopifyCustomer = shopifyOrder['customer']
    try:
        shopifyAddress = shopifyCustomer['default_address']
    except:
        shopifyAddress = shopifyOrder['shipping_address']

    # Import Customer
    try:
        customer = Customer.objects.get(customerId=shopifyCustomer['id'])
    except Customer.DoesNotExist:
        customer = Customer(customerId=shopifyCustomer['id'])

    customer.email = shopifyCustomer['email']
    customer.firstName = shopifyCustomer['first_name']
    customer.lastName = shopifyCustomer['last_name']
    customer.phone = shopifyCustomer['phone']
    try:
        customer.defaultAddressId = shopifyAddress['id']
    except:
        customer.defaultAddressId = ''
    customer.orderCount = shopifyCustomer['orders_count']
    customer.totalSpent = shopifyCustomer['total_spent']
    customer.state = shopifyCustomer['state']
    customer.note = shopifyCustomer['note']
    customer.tags = shopifyCustomer['tags']
    customer.acceptsMarketing = shopifyCustomer['accepts_marketing']
    customer.createdAt = shopifyCustomer['created_at']

    customer.save()

    # Import Address
    if customer.defaultAddressId:
        try:
            address = Address.objects.get(addressId=customer.defaultAddressId)
        except Address.DoesNotExist:
            address = Address(addressId=customer.defaultAddressId)

        address.customer = customer
        address.firstName = shopifyAddress['first_name']
        address.lastName = shopifyAddress['last_name']
        address.phone = shopifyAddress['phone']
        address.address1 = shopifyAddress['address1']
        address.address2 = shopifyAddress['address2']
        address.company = shopifyAddress['company']
        address.city = shopifyAddress['city']
        address.state = shopifyAddress['province_code']
        address.zip = shopifyAddress['zip']
        address.country = shopifyAddress['country']

        address.save()

    # Import Order

    specialShipping = ''
    shippingMethod = ''
    shippingCost = 0

    if len(shopifyOrder['shipping_lines']) > 0:
        shipping = shopifyOrder['shipping_lines'][0]
        shippingCost = float(shipping['price'])

        shippingMethod = shipping['title']
        if 'UPS Next Day Air' in shippingMethod:
            shippingMethod = 'UPS Next Day Air'
        if 'UPS 2nd Day Air' in shippingMethod:
            shippingMethod = 'UPS 2nd Day Air'

        if shopifyOrder['shipping_address']['country'] != 'United States' and shopifyOrder['shipping_address']['country'] != "US":
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
    if 'Fraud' in shopifyOrder['tags']:
        isFraud = 1

    if shopifyOrder.get('billing_address'):
        billing_last_name = shopifyOrder['billing_address']['last_name']
        billing_first_name = shopifyOrder['billing_address']['first_name']
        billing_company = shopifyOrder['billing_address']['company']
        billing_address1 = shopifyOrder['billing_address']['address1']
        billing_address2 = shopifyOrder['billing_address']['address2']
        billing_city = shopifyOrder['billing_address']['city']
        billing_province_code = shopifyOrder['billing_address']['province_code']
        billing_zip = shopifyOrder['billing_address']['zip']
        billing_country = shopifyOrder['billing_address']['country']
        billing_phone = shopifyOrder['billing_address']['phone']
    else:
        billing_last_name = ""
        billing_first_name = ""
        billing_company = ""
        billing_address1 = ""
        billing_address2 = ""
        billing_city = ""
        billing_province_code = ""
        billing_zip = ""
        billing_country = ""
        billing_phone = ""

    if shopifyOrder.get('shipping_address'):
        shipping_last_name = shopifyOrder['shipping_address']['last_name']
        shipping_first_name = shopifyOrder['shipping_address']['first_name']
        shipping_company = shopifyOrder['shipping_address']['company']
        shipping_address1 = shopifyOrder['shipping_address']['address1']
        shipping_address2 = shopifyOrder['shipping_address']['address2']
        shipping_city = shopifyOrder['shipping_address']['city']
        shipping_province_code = shopifyOrder['shipping_address']['province_code']
        shipping_zip = shopifyOrder['shipping_address']['zip']
        shipping_country = shopifyOrder['shipping_address']['country']
        shipping_phone = shopifyOrder['shipping_address']['phone']
    else:
        shipping_last_name = billing_last_name
        shipping_first_name = billing_first_name
        shipping_company = billing_company
        shipping_address1 = billing_address1
        shipping_address2 = billing_address2
        shipping_city = billing_city
        shipping_province_code = billing_province_code
        shipping_zip = billing_zip
        shipping_country = billing_country
        shipping_phone = billing_phone

    try:
        order = Order.objects.get(shopifyOrderId=shopifyOrder['id'])
    except Order.DoesNotExist:
        order = Order(shopifyOrderId=shopifyOrder['id'])

    order.orderNumber = shopifyOrder['order_number']
    order.email = shopifyOrder['email']
    order.phone = shopifyOrder['phone']
    order.customer = customer

    order.billingFirstName = billing_first_name
    order.billingLastName = billing_last_name
    order.billingCompany = billing_company
    order.billingAddress1 = billing_address1
    order.billingAddress2 = billing_address2
    order.billingCity = billing_city
    order.billingState = billing_province_code
    order.billingZip = billing_zip
    order.billingCountry = billing_country
    order.billingPhone = billing_phone

    order.shippingFirstName = shipping_first_name
    order.shippingLastName = shipping_last_name
    order.shippingCompany = shipping_company
    order.shippingAddress1 = shipping_address1
    order.shippingAddress2 = shipping_address2
    order.shippingCity = shipping_city
    order.shippingState = shipping_province_code
    order.shippingZip = shipping_zip
    order.shippingCountry = shipping_country
    order.shippingPhone = shipping_phone

    order.shippingMethod = shippingMethod
    order.specialShipping = specialShipping
    order.orderNote = shopifyOrder['note']

    order.totalItems = shopifyOrder['total_line_items_price']
    order.totalDiscounts = shopifyOrder['total_discounts']
    order.orderSubtotal = shopifyOrder['subtotal_price']
    order.orderTax = shopifyOrder['total_tax']
    order.orderShippingCost = shippingCost
    order.orderTotal = shopifyOrder['total_price']

    order.weight = float(shopifyOrder['total_weight']) / 453.592
    order.orderDate = shopifyOrder['created_at']
    order.isFraud = isFraud

    order.save()

    # Import Shopping Cart
    line_items = shopifyOrder['line_items']

    manufacturers = []
    orderTypes = []

    Line_Item.objects.filter(order=order).delete()

    orderHold = False
    holdBrand = ""

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

            try:
                brandData = Manufacturer.objects.get(name=manufacturer)
                brand = brandData.brand

                if int(line_item['quantity']) * float(line_item['price']) > 2000:
                    if brand == 'Kravet' or brand == 'York' or brand == 'Kasmir':
                        orderHold = True
                        holdBrand = brand
            except:
                pass

            if line_item['variant_id'] == None or line_item['variant_id'] == 'None' or line_item['variant_id'] == '' or line_item['variant_id'] == 0:
                variant = None
            else:
                try:
                    variant = Variant.objects.get(
                        variantId=line_item['variant_id'])
                except Variant.DoesNotExist:
                    variant = None

            shoppingCart = Line_Item()

            shoppingCart.order = order
            shoppingCart.variant = variant
            shoppingCart.quantity = line_item['quantity']
            shoppingCart.orderedProductTitle = line_item['title']
            shoppingCart.orderedProductVariantTitle = variantTitle
            shoppingCart.orderedProductVariantName = line_item['name']
            shoppingCart.orderedProductSKU = line_item['sku']
            shoppingCart.orderedProductManufacturer = manufacturer
            shoppingCart.orderedProductUnitPrice = line_item['price']
            shoppingCart.orderedProductLineDiscount = line_item['total_discount']
            shoppingCart.orderedProductUnitWeight = weight / 453.592
            shoppingCart.taxable = line_item['taxable']

            shoppingCart.save()

        except Exception as e:
            debug("Order", 2, "Import Order error: PO {}. Error: {}".format(
                shopifyOrder['order_number']), e)
            return

    # Update Order Manufacturers and Types
    manufacturers.sort()
    orderTypes.sort()
    manufacturerList = ",".join(manufacturers)
    orderTypeList = "/".join(orderTypes)

    order.orderType = orderTypeList
    order.manufacturerList = manufacturerList

    # Import Order Attributes
    # attrs = shopifyOrder['note_attributes']

    # for attr in attrs:
    #     if attr['value'] != "" and attr['value'] != None:
    #         if attr['name'] == "Status":
    #             order.status = attr['value']

    #         if attr['name'] == "Initials":
    #             order.initials = attr['value']

    #         if attr['name'] == "ManufacturerList":
    #             order.manufacturerList = attr['value']

    #         if attr['name'] == "ReferenceNumber":
    #             order.referenceNumber = attr['value']

    #         if attr['name'] == "CSNote":
    #             order.note = attr['value']

    #         if attr['name'] == "SpecialShipping":
    #             order.specialShipping = attr['value']

    order.save()

    if orderHold:
        if order.status == 'New' or order.status == None:
            order.status = "Hold"
            order.save()

            emailer.send_email_html("Brewster EDI",
                                    "murrell@decoratorsbest.com,bk@decoratorsbest.com",
                                    "PO #{} has been set to hold".format(
                                        order.orderNumber),
                                    "Hi, <br><br>PO# {} has been set to hold because it's a {} large order. \
                Please process it manually. <br><br>Best, <br>OM Backend".format(order.orderNumber, holdBrand))

    debug("Order", 0,
          "Downloaded Order {} / {}".format(order.orderNumber, order.shopifyOrderId))
