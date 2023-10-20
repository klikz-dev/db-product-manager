from django.core.management.base import BaseCommand

import os
import environ
import pymysql
import csv

from library import debug, common
from shopify.models import Customer, Address
from feed.models import Roomvo

FILEDIR = f"{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/files"

PROCESS = "Report"


class Command(BaseCommand):
    help = "Build Reports"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "roomvo" in options['functions']:
            processor = Processor()
            processor.roomvo()

        if "customers" in options['functions']:
            processor = Processor()
            processor.customers()


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
        self.csr.execute(f"""
            SELECT P.ProductID, P.SKU, P.Handle, P.Title, P.BodyHTML, P.ProductTypeId, M.Brand, PI.imageURL, T.Name
            FROM ProductImage PI
            LEFT JOIN Product P ON PI.ProductID = P.ProductID 
            LEFT JOIN Type T ON P.ProductTypeId = T.TypeId
            LEFT JOIN ProductManufacturer PM ON P.SKU = PM.SKU 
            LEFT JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID 
            WHERE PI.ImageIndex = 20 AND P.Published = 1
        """)
        rows = self.csr.fetchall()

        for row in rows:
            productId = row[0]
            sku = row[1]
            handle = row[2]
            title = row[3]
            bodyHTML = row[4]
            productTypeId = row[5]
            brand = row[6]
            imageURL = row[7]
            type = row[8]

            # Type
            types = [
                "Wallpaper",
                "Rug",
                "Wall Art",
                "Wall Mirrors",
                "Wall Hangings",
                "Wall Accent",
                "Mirrors"
            ]

            if type not in types:
                continue

            if type == "Rug":
                type = "Area Rug"
            elif "Mirror" in type or "Wall " in type:
                type = "Wall Art"

            if "Rug Pad" in title:
                continue

            # Collection, Width, Length, and Layout
            width = ""
            length = ""
            height = ""
            depth = ""
            rollLength = ""
            size = ""
            dim = ""
            sizeDisplay = ""
            hr = ""
            vr = ""
            repeat = ""
            layout = ""
            body = bodyHTML.replace(
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
                if "Roll Length:" in line:
                    rollLength = line.replace("Roll Length:", "").strip()
                if "Size:" in line:
                    size = line.replace("Size:", "").strip()
                if "Dimension:" in line:
                    dim = line.replace("Dimension:", "").replace(
                        "Roll", "").strip()
                    if "," in dim:
                        dim = dim.split(",")[0]
                if "Horizontal Repeat:" in line:
                    hr = line.replace("Horizontal Repeat:", "").strip()
                    layout = "Repeat"
                if "Vertical Repeat:" in line:
                    vr = line.replace("Vertical Repeat:", "").strip()
                    layout = "Repeat"
                if "Repeat:" in line and "Horizontal" not in line and "Vertical" not in line:
                    repeat = line.replace("Repeat:", "").strip()
                    layout = "Repeat"
                if "Match:" in line:
                    match = line.replace("Match:", "").strip()
                    layout = ", ".join((layout, match))

            x = width.replace("Each Pre-Cut Roll",
                              "").replace("Inches.", "in").strip()
            y = length or height
            z = ""

            if type == "Area Rug" or type == "Wall Art":
                if depth:
                    y = length or height
                    z = depth
                else:
                    y = length
                    z = height

                if z and not y:
                    y = z
                    z = ""

            if not y and rollLength:
                y = round(float(rollLength.replace(
                    "yards", "").replace("yds", "").strip()) * 36, 2)
                y = f"{y} in"

            if "ft" in y:
                y = round(float(y.replace("ft", "").strip()) * 12, 2)
                y = f"{y} in"

            if not x and "x" in size:
                x = size.split("x")[0].replace(
                    "sold as a single", "").replace("wide", "").strip()

            if not x and dim:
                if "/" in dim:
                    dim = dim.split("/")[0]
                if "x" in dim:
                    x = dim.split("x")[0].strip()
                    y = dim.split("x")[1].strip()
                    if "yards" in y or "yds" in y:
                        y = round(float(y.replace("yards", "").replace(
                            "yds", "").strip()) * 36, 2)
                        y = f"{y} in"

            # Repeat
            if "x" in repeat:
                repeat = repeat.split("/")[0]
                if "in" in repeat:
                    hr = repeat.split("x")[0].strip()
                    vr = repeat.split("x")[1].strip()
                else:
                    hr = round(float(repeat.split("x")[0].replace(
                        "cm", "").replace("W", "").replace("m", "").strip()) / 2.54, 2)
                    vr = round(float(repeat.split("x")[1].replace(
                        "cm", "").replace("L", "").replace("m", "").strip()) / 2.54, 2)
                    hr = f"{hr} in"
                    vr = f"{vr} in"
            elif "/" in repeat:
                repeat = repeat.split("/")[0]
                if "in" in repeat:
                    vr = repeat.strip()
                else:
                    vr = round(float(repeat.replace(
                        "cm", "").strip()) / 2.54, 2)
                    vr = f"{vr} in"

            if brand == "Brewster" and repeat:
                try:
                    if float(repeat.replace("in", "")) > 0:
                        vr = repeat
                        if "in" not in repeat:
                            vr = f"{repeat} in"
                except:
                    pass

            x = x.replace('"', ' in').replace("W", "").replace(
                "H", "").replace(",", "")
            y = y.replace('"', ' in').replace("W", "").replace(
                "H", "").replace(",", "")
            hr = hr.replace('"', ' in')
            vr = vr.replace('"', ' in')

            if x == "0 in":
                x = ""
            if y == "0 in":
                y = ""
            if vr == "0 in":
                vr = ""
            if hr == "0 in":
                hr = ""

            if not x or not y:
                continue

            # Width bug
            x = f"{common.formatFloat(x)} in"

            # Size display
            if type == "Area Rug":
                if brand == "Surya":
                    if dim:
                        sizeDisplay = dim
                    elif size:
                        sizeDisplay = size
                elif brand == "Jaipur Living":
                    if "(" in title and ")" in title:
                        sizeDisplay = title.split("(")[1].split(")")[0]
                    else:
                        sizeDisplay = f"{round(common.formatFloat(x) / 12, 2)}' X {round(common.formatFloat(y) / 12, 2)}'"

            if type == "Wallpaper":
                sizeDisplay = f"{x} X {round(common.formatFloat(y) / 36, 2)} yds"

            # Variants
            v1 = ""
            v2 = ""
            v3 = ""
            v4 = ""

            # self.csr.execute(f"""
            #     SELECT PV.Name, PV.VariantId, PV.IsDefault
            #     FROM ProductVariant PV
            #     WHERE PV.ProductId='{productId}'
            # """)
            # rows = self.csr.fetchall()

            # for row in rows:
            #     if row[2] == 1:
            #         v1 = row[1]
            #     elif "Trade - " in row[0]:
            #         v2 = row[1]
            #     elif "Free Sample - " in row[0]:
            #         v4 = row[1]
            #     elif "Sample - " in row[0]:
            #         v3 = row[1]

            # Filters
            categories = []
            styles = []
            colors = []
            subtypes = []

            # self.csr.execute(f"""
            #     SELECT T.Name, T.Description, T.ParentTagId
            #     FROM ProductTag PT
            #     LEFT JOIN Tag T ON PT.TagId = T.TagId
            #     WHERE PT.SKU='{sku}'
            # """)
            # rows = self.csr.fetchall()

            # for row in rows:
            #     if row[2] == 0:
            #         continue

            #     if row[1] == "Category":
            #         categories.append(row[0])

            #     if row[1] == "Style":
            #         styles.append(row[0])

            #     if row[1] == "Color":
            #         colors.append(row[0])

            # self.csr.execute(f"""
            #     SELECT T.Name, T.ParentTypeId
            #     FROM ProductSubtype PT
            #     LEFT JOIN Type T ON PT.SubTypeId = T.TypeId
            #     WHERE PT.SKU='{sku}'
            # """)
            # rows = self.csr.fetchall()

            # for row in rows:
            #     if row[1] != 0:
            #         subtypes.append(row[0])

            # categories = ", ".join(categories)
            # styles = ", ".join(styles)
            # colors = ", ".join(colors)
            # subtypes = ", ".join(subtypes)

            Roomvo.objects.create(
                sku=sku,
                availability='Yes',
                name=title,
                width=x,
                length=y,
                thickness=z,
                dimension_display=sizeDisplay,
                horizontal_repeat=hr,
                vertical_repeat=vr,
                image=imageURL,
                layout=layout,
                product_type=type,
                link=f'https://www.decoratorsbest.com/products/{handle}',
                filter_category=categories,
                filter_style=styles,
                filter_color=colors,
                filter_subtype=subtypes,
                cart_id=v1,
                cart_id_trade=v2,
                cart_id_sample=v3,
                cart_id_free_sample=v4,
            )

            debug.debug(
                PROCESS, 0, f"SKU: {sku}, Name: {title}")

    def customers(self):
        with open(FILEDIR + 'customers.csv', 'w', newline='') as customersFile:
            csvWriter = csv.DictWriter(customersFile, fieldnames=[
                'email',
                'fname',
                'lname',
                'phone',
                'address1',
                'address2',
                'company',
                'city',
                'state',
                'zip',
                'country',
                'total',
            ])

            csvWriter.writerow({
                'email': 'Email',
                'fname': 'First Name',
                'lname': 'Last Name',
                'phone': 'Phone Number',
                'address1': 'Address 1',
                'address2': 'Address 2',
                'company': 'Company',
                'city': 'City',
                'state': 'State',
                'zip': 'Zip Code',
                'country': 'Country',
                'total': 'Total Spent',
            })

            customers = Customer.objects.all()

            total = len(customers)
            for index, customer in enumerate(customers):
                try:
                    address = Address.objects.get(
                        addressId=customer.defaultAddressId)
                except Address.DoesNotExist:
                    continue

                csvWriter.writerow({
                    'email': customer.email,
                    'fname': customer.firstName,
                    'lname': customer.lastName,
                    'phone': customer.phone,
                    'address1': address.address1,
                    'address2': address.address2,
                    'company': address.company,
                    'city': address.city,
                    'state': address.state,
                    'zip': address.zip,
                    'country': address.country,
                    'total': customer.totalSpent,
                })

                debug.debug(PROCESS, 0, f"{index+1}/{total}: {customer.email}")
