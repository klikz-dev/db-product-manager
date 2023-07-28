from django.core.management.base import BaseCommand
from django.db.models import Q

import os
import environ
import pymysql
import csv

from library import database, debug
from shopify.models import Product, ProductImage
from mysql.models import ProductTag, Tag, ProductSubtype, Type

from feed.models import KravetDecor, Kravet, York

FILEDIR = "{}/files/".format(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))


class Command(BaseCommand):
    help = "Build Reports"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "roomvo" in options['functions']:
            processor = Processor()
            processor.roomvo()


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)
        self.csr = self.con.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.csr.close()
        self.con.close()

    def roomvo(self):
        ### Get High Res Image SKUs ###
        wallpaperSkus = []

        # Kravet
        fnames = os.listdir(f"{FILEDIR}/images/kravet/")
        for fname in fnames:
            mpn = f"{fname.replace('_', '.').replace('.jpg', '').replace('.png', '')}.0".upper(
            )

            try:
                product = Kravet.objects.get(mpn=mpn)
                wallpaperSkus.append(product.sku)
            except Kravet.DoesNotExist:
                continue

        # York
        fnames = os.listdir(f"{FILEDIR}/images/york/")
        for fname in fnames:
            try:
                if "_" not in fname:
                    mpn = fname.split(".")[0]

                    try:
                        product = York.objects.get(mpn=mpn)
                        wallpaperSkus.append(product.sku)
                    except York.DoesNotExist:
                        continue
            except:
                continue

        ###############################

        products = Product.objects.filter(Q(published=True) & Q(deleted=False))
        products = products.exclude(Q(productId=None) | Q(productId="") | Q(
            manufacturerPartNumber=None) | Q(manufacturerPartNumber=""))
        products = products.filter(Q(productTypeId=2) | Q(
            productTypeId=4) | Q(productTypeId=41))

        with open(FILEDIR + 'roomvo.csv', 'w', newline='') as roomvoFile:
            roomvoWriter = csv.DictWriter(roomvoFile, fieldnames=[
                'availability',
                'sku',
                'name',
                'width',
                'length',
                'height',
                'horizontal_repeat',
                'vertical_repeat',
                'image',
                'layout',
                'type',
                'link',
                'category',
                'style',
                'color',
                'subtype',
                'v1',
                'v2',
                'v3',
                'v4'
            ])

            roomvoWriter.writerow({
                'availability': 'Aavailability',
                'sku': 'SKU',
                'name': 'Name',
                'width': 'Width',
                'length': 'Length',
                'height': 'Thickness',
                'horizontal_repeat': 'Horizontal Repeat',
                'vertical_repeat': 'Vertical Repeat',
                'image': 'Image File Path',
                'layout': 'Tile / Plank Layout',
                'type': 'Product Subtype',
                'link': 'Link',
                'category': 'Category (Filter)',
                'style': 'Style (Filter)',
                'color': 'Color (Filter)',
                'subtype': 'Subtype (Filter)',
                'v1': 'Add to Cart',
                'v2': 'Add to Cart (Trade)',
                'v3': 'Order Sample',
                'v4': 'Order Sample (Trade)'
            })

            wallpaperAdded = 0
            rugAdded = 0
            wallArtAdded = 0

            for product in products:
                if product.productTypeId == 2 and product.sku not in wallpaperSkus:
                    continue

                if (product.productTypeId == 2 and wallpaperAdded > 99) or (product.productTypeId == 4 and rugAdded > 49) or (product.productTypeId == 41 and wallArtAdded > 49):
                    continue

                if "Rug Pad" in product.title or (product.productTypeId == 4 and "SR" not in product.sku):
                    continue

                productId = product.productId

                # SKU, Name, and Handle
                sku = product.sku
                name = product.title
                handle = product.handle

                # Type
                if product.productTypeId == 2:
                    type = "Wallpaper"
                elif product.productTypeId == 4:
                    type = "Area Rug"
                elif product.productTypeId == 41:
                    type = "Wall Art"
                else:
                    continue

                # Collection, Width, Length, and Layout
                width = ""
                length = ""
                height = ""
                depth = ""
                hr = ""
                vr = ""
                layout = ""
                body = product.bodyHTML.replace(
                    "<br/>", "<br>").replace("<br />", "<br>").split("<br>")
                for line in body:
                    if "Width:" in line:
                        width = line.replace("Width:", "").strip()
                    if "Length:" in line and "Roll Length:" not in line:
                        length = line.replace("Length:", "").strip()
                    if "Height:" in line:
                        height = line.replace("Height:", "").strip()
                    if "Depth:" in line:
                        depth = line.replace("Depth:", "").strip()
                    if "Horizontal Repeat:" in line:
                        hr = line.replace("Horizontal Repeat:", "").strip()
                    if "Vertical Repeat:" in line:
                        vr = line.replace("Vertical Repeat:", "").strip()
                    if "Repeat:" in line or "Horizontal Repeat:" in line or "Vertical Repeat:" in line:
                        layout = "Repeat"
                    if "Match:" in line:
                        match = line.replace("Match:", "").strip()
                        layout = ", ".join((layout, match))

                x = width
                y = ""
                z = ""

                if product.productTypeId == 4 or product.productTypeId == 41:
                    if depth:
                        z = depth
                        y = height or length
                    else:
                        z = height
                        y = length

                    if product.productTypeId == 41 and not z:
                        continue
                else:
                    y = height or length

                # Image
                images = ProductImage.objects.filter(
                    Q(productId=productId) & Q(imageIndex=1))
                if len(images) == 0:
                    continue
                image = images[0].imageURL
                if image == "":
                    continue

                # Variants
                v1 = ""
                v2 = ""
                v3 = ""
                v4 = ""
                variants = product.variants.all()

                for variant in variants:
                    if variant.isDefault == True:
                        v1 = variant.variantId
                    elif "Trade - " in variant.name:
                        v2 = variant.variantId
                    elif "Free Sample - " in variant.name:
                        v4 = variant.variantId
                    elif "Sample - " in variant.name:
                        v3 = variant.variantId

                # Filters
                categories = []
                styles = []
                colors = []
                subtypes = []

                productTags = ProductTag.objects.filter(sku=sku)
                for productTag in productTags:
                    try:
                        tag = Tag.objects.get(tagId=productTag.tagId)
                    except Tag.DoesNotExist:
                        continue
                    if tag.parentTagId == 0:
                        continue

                    if tag.description == "Category":
                        categories.append(tag.name)

                    if tag.description == "Style":
                        styles.append(tag.name)

                    if tag.description == "Color":
                        colors.append(tag.name)

                productSubtypes = ProductSubtype.objects.filter(sku=sku)
                for productSubtype in productSubtypes:
                    try:
                        subtype = Type.objects.get(
                            typeId=productSubtype.subtypeId)
                    except Type.DoesNotExist:
                        continue
                    if subtype.parentTypeId == 0:
                        continue

                    subtypes.append(subtype.name)

                categories = ", ".join(categories)
                styles = ", ".join(styles)
                colors = ", ".join(colors)
                subtypes = ", ".join(subtypes)

                debug.debug(
                    "Report", 0, f"Wallpaper: {wallpaperAdded}, Rug: {rugAdded}, Wall Art: {wallArtAdded} -- SKU: {sku}, Name: {name}")

                roomvoWriter.writerow({
                    'availability': 'Yes',
                    'sku': sku,
                    'name': name,
                    'width': x,
                    'length': y,
                    'height': z,
                    'horizontal_repeat': hr,
                    'vertical_repeat': vr,
                    'image': image,
                    'layout': layout,
                    'type': type,
                    'link': 'https://www.decoratorsbest.com/products/{}'.format(handle),
                    'category': categories,
                    'style': styles,
                    'color': colors,
                    'subtype': subtypes,
                    'v1': v1,
                    'v2': v2,
                    'v3': v3,
                    'v4': v4
                })

                if product.productTypeId == 2:
                    wallpaperAdded = wallpaperAdded + 1

                if product.productTypeId == 4:
                    rugAdded = rugAdded + 1

                if product.productTypeId == 41:
                    wallArtAdded = wallArtAdded + 1
