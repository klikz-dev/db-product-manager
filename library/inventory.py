import requests
import requests
import json
import xml.etree.ElementTree as ET
from urllib.parse import quote

from mysql.models import ProductInventory, ProductManufacturer
from shopify.models import Product
from feed.management.commands.phillips import Processor as PhillipsProcessor


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
    #                 quote(product.pattern), quote(product.color)),
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

    elif manufacturer.brand == "Phillips":
        try:
            processor = PhillipsProcessor()
            response = processor.inventory(product.manufacturerPartNumber)

            return {
                "brand": manufacturer.brand,
                "sku": sku,
                "quantity": response['stock'],
                "type": 1,
                "note": response['leadtime']
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
