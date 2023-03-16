from library import debug, emailer
import environ
from library.debug import debug
import os
import requests
import math
import shutil
import datetime
import pytz
import requests
import json
import xml.etree.ElementTree as ET

import urllib.request

from mysql.models import ProductInventory, ProductManufacturer
from shopify.models import Address, Customer, Line_Item, Order, Variant, Product
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


def fmt(x):
    return str(x).replace("~", "").replace("!", "").replace("@", "").replace("#", "").replace("$", "").replace("%", "").replace("^", "").replace("&", "").replace("*", "").replace("(", "").replace(")", "").strip().upper()


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
    print(shopifyCustomer)
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
    try:
        customer.orderCount = shopifyCustomer['orders_count']
    except:
        pass
    try:
        customer.totalSpent = shopifyCustomer['total_spent']
    except:
        pass
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

    isNewOrder = True
    try:
        order = Order.objects.get(shopifyOrderId=shopifyOrder['id'])
        isNewOrder = False
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
    # holdBrand = ""

    # Set hold the orders with customer note
    if order.orderNote:
        orderHold = True

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

                # if int(line_item['quantity']) * float(line_item['price']) > 2000:
                #     if brand == 'Kravet' or brand == 'York' or brand == 'Kasmir':
                #         orderHold = True
                #         holdBrand = brand

                #         if isNewOrder:
                #             emailer.send_email_html("DB Order Manager",
                #                                 [
                #                                     "purchasing@decoratorsbest.com",
                #                                     "bk@decoratorsbest.com"
                #                                 ],
                #                                 "PO #{} has been set to hold".format(
                #                                     order.orderNumber),
                #                                 "Hi, <br><br>PO# {} has been set to hold because it's a {} large order. \
                #             Please process it manually. <br><br>Best, <br>OM Backend".format(order.orderNumber, holdBrand))

            except Exception as e:
                print(e)
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

    order.save()

    if orderHold:
        if order.status == 'New' or order.status == None:
            order.status = "Hold"
            order.save()

    debug("Order", 0,
          "Downloaded Order {} / {}".format(order.orderNumber, order.shopifyOrderId))


def inventory(sku):
    noStock = {"sku": sku, "quantity": 0, "type": 2}

    try:
        product = Product.objects.get(sku=sku)
        productManufacturer = ProductManufacturer.objects.get(sku=sku)
        manufacturer = productManufacturer.manufacturer
    except Exception as e:
        noStock["error"] = str(e)
        return noStock

    # if manufacturer.brand == "Kravet" and manufacturer.name != "Kravet Pillow":
    #     try:
    #         response = requests.request(
    #             "GET",
    #             "https://www.e-designtrade.com/api/stock_onhand.asp?user=DBEST767&password=b1028H47kkr&pattern={}&color={}".format(
    #                 product.pattern, product.color),
    #             headers={
    #                 'Authorization': 'Token d71bcdc1b60d358e01182da499fd16664a27877a',
    #                 'Cookie': 'ASPSESSIONIDAURDSCBS=MECPGHNBKCFFKBBBKKAEJOGO'
    #             }
    #         )
    #         data = ET.fromstring(response.content)
    #         onhand_qty = data.find('ONHAND_QTY').text
    #         lead_time = data.find('LEAD_TIME').text

    #         return {
    #             "brand": manufacturer.brand,
    #             "sku": sku,
    #             "quantity": int(float(onhand_qty)),
    #             "type": 1,
    #             "note": "{} days".format(lead_time)
    #         }
    #     except Exception as e:
    #         noStock["error"] = str(e)
    #         noStock["data"] = str(response.content)
    #         return noStock

    if manufacturer.brand == "Maxwell":
        try:
            response = requests.request(
                "GET",
                "https://distribution.pdfsystems.com/api/simple/item/lookup?sku={}".format(
                    product.manufacturerPartNumber),
                headers={
                    'x-api-key': '286d17936503cc7c82de30e4c4721a67'
                }
            )
            data = json.loads(response.text)
            onhand_qty = data["inventory"]["on_hand"]

            return {
                "brand": manufacturer.brand,
                "sku": sku,
                "quantity": int(float(onhand_qty)),
                "type": 1,
                "note": ""
            }
        except Exception as e:
            noStock["error"] = str(e)
            return noStock

    elif manufacturer.brand == "Seabrook":
        try:
            response = requests.request(
                "GET",
                "https://stock.wallcovering.info/v1/api/item/{}".format(
                    product.manufacturerPartNumber),
                headers={
                    'x-api-key': 'Z0ELIAGuzd3poCHVVngGD7iS44qMuXfM51NWqLyC'
                }
            )
            data = json.loads(response.text)
            onhand_qty = data["stock"]["units"]

            return {
                "brand": manufacturer.brand,
                "sku": sku,
                "quantity": int(float(onhand_qty)),
                "type": 1,
                "note": ""
            }
        except Exception as e:
            noStock["error"] = str(e)
            return noStock

    elif manufacturer.brand == "York":
        try:
            response = requests.request(
                "GET",
                "http://yorkapi.yorkwall.com:10090/pcsiapi/stock.php/{}".format(
                    product.manufacturerPartNumber)
            )
            data = json.loads(response.text)
            onhand_qty = data["results"][0]["amount"]

            return {
                "brand": manufacturer.brand,
                "sku": sku,
                "quantity": int(float(onhand_qty)),
                "type": 1,
                "note": ""
            }
        except Exception as e:
            noStock["error"] = str(e)
            return noStock

    elif manufacturer.brand == "Stout":
        try:
            response = requests.request(
                "GET",
                "https://www.estout.com/api/search.vbhtml?key=aeba0d7a-9518-4299-b06d-46ab828e3288&id={}".format(
                    product.manufacturerPartNumber)
            )
            data = json.loads(response.text)
            onhand_qty = data["result"][0]["avail"]

            return {
                "brand": manufacturer.brand,
                "sku": sku,
                "quantity": int(float(onhand_qty)),
                "type": 1,
                "note": ""
            }
        except Exception as e:
            noStock["error"] = str(e)
            return noStock

    elif manufacturer.brand == "Pindler":
        try:
            response = requests.request(
                "GET",
                "https://trade.pindler.com/cgi-bin/fccgi.exe?w3exec=checkstock&w3serverpool=checkstock&token=683150AbX72VWZ312910tB5259532c&yards=10&item={}".format(
                    product.sku.replace("PDL", "").strip())
            )
            if "INSTOCK" in response.text.upper():
                onhand_qty = "10"
            else:
                onhand_qty = "0"

            return {
                "brand": manufacturer.brand,
                "sku": sku,
                "quantity": int(float(onhand_qty)),
                "type": 3,
                "note": ""
            }
        except Exception as e:
            noStock["error"] = str(e)
            return noStock

    elif manufacturer.brand == "Phillip Jeffries":
        try:
            response = requests.request(
                "GET",
                "https://www.phillipjeffries.com/api/products/skews/{}.json".format(
                    product.manufacturerPartNumber)
            )
            data = json.loads(response.text)

            onhand_qty = 0
            for lot in data["stock"]["sales"]["lots"]:
                onhand_qty += int(float(lot["avail"]))

            return {
                "brand": manufacturer.brand,
                "sku": sku,
                "quantity": onhand_qty,
                "type": 1,
                "note": ""
            }
        except Exception as e:
            noStock["error"] = str(e)
            return noStock

    else:
        try:
            inventory = ProductInventory.objects.get(sku=sku)
            return {
                "brand": inventory.brand,
                "sku": inventory.sku,
                "quantity": inventory.quantity,
                "type": inventory.type,
                "note": inventory.note,
                "updatedAt": inventory.updatedAt
            }
        except ProductInventory.DoesNotExist:
            noStock["error"] = "SKU Doesn't exist in our database."
            return noStock
        except Exception as e:
            noStock["error"] = str(e)
            return noStock
