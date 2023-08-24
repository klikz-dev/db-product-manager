from django.core.management.base import BaseCommand

import environ
import pymysql
import time
import re

from library import const, common

PROCESS = "Pending"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.color()
                    processor.category()
                    processor.style()
                    processor.subtype()
                    processor.size()
                    processor.collection()

                print("Finished process. Waiting for next run. {}:{}".format(
                    PROCESS, options['functions']))
                time.sleep(3600)


class Processor:
    def __init__(self):
        env = environ.Env()

        self.con = pymysql.connect(host=env('MYSQL_HOST'), user=env('MYSQL_USER'), passwd=env(
            'MYSQL_PASSWORD'), db=env('MYSQL_DATABASE'), connect_timeout=5)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.con.close()

    def color(self):
        csr = self.con.cursor()

        csr.execute(
            "DELETE FROM EditColor WHERE SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        self.con.commit()

        csr.execute("SELECT SKU, Color FROM EditColor WHERE IsManual = 0")
        for row in csr.fetchall():
            sku = row[0]
            color = row[1].lower()
            for key in const.colorDict.keys():
                if key in color:
                    csr.execute("CALL AddToProductTag ({}, {})".format(
                        common.sq(sku), common.sq(const.colorDict[key])))
                    self.con.commit()

                    print(f"Color: {const.colorDict[key]} - Product: {sku}")

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditColor)
                                                            AND SKU IN (SELECT SKU FROM ProductTag PT JOIN Tag T ON PT.TagID = T.TagID WHERE T.ParentTagID = 3)""")
        self.con.commit()

        csr.execute("DELETE FROM EditColor")
        self.con.commit()

        csr.close()

    def category(self):
        csr = self.con.cursor()

        csr.execute(
            "DELETE FROM EditCategory WHERE SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        self.con.commit()

        categories = []
        csr.execute(
            "SELECT DISTINCT T.Name AS Tag FROM Tag T WHERE T.ParentTagID = 2")
        for row in csr.fetchall():
            categories.append(row[0].lower())

        csr.execute("SELECT SKU, Category FROM EditCategory WHERE IsManual = 0")
        for row in csr.fetchall():
            sku = row[0]
            category = row[1].lower()
            for c in categories:
                if c in category:
                    csr.execute("CALL AddToProductTag ({}, {})".format(
                        common.sq(sku), common.sq(c)))
                    self.con.commit()

                    print(f"Category: {c} - Product: {sku}")

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditCategory)
                                                            AND SKU IN (SELECT SKU FROM ProductTag PT JOIN Tag T ON PT.TagID = T.TagID WHERE T.ParentTagID = 2)""")
        self.con.commit()

        csr.execute("DELETE FROM EditCategory")
        self.con.commit()

        csr.close()

    def style(self):
        csr = self.con.cursor()

        csr.execute("DELETE FROM EditStyle WHERE SKU IN (SELECT SKU FROM ProductTag PT JOIN Tag T ON PT.TagID = T.TagID WHERE T.ParentTagID = 1) OR SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        self.con.commit()

        styles = []
        csr.execute(
            "SELECT DISTINCT T.Name AS Tag FROM Tag T WHERE T.ParentTagID = 1")
        for row in csr.fetchall():
            styles.append(row[0].lower())

        csr.execute("SELECT SKU, Style FROM EditStyle WHERE IsManual = 0")
        for row in csr.fetchall():
            sku = row[0]
            style = row[1].lower()
            for s in styles:
                if s in style:
                    csr.execute("CALL AddToProductTag ({}, {})".format(
                        common.sq(sku), common.sq(s)))
                    self.con.commit()

                    print(f"Style: {s} - Product: {sku}")

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditStyle)
                                                            AND SKU IN (SELECT SKU FROM ProductTag PT JOIN Tag T ON PT.TagID = T.TagID WHERE T.ParentTagID = 1)""")
        self.con.commit()

        csr.execute("DELETE FROM EditStyle")
        self.con.commit()

        csr.close()

    def subtype(self):
        csr = self.con.cursor()

        csr.execute(
            "DELETE FROM EditSubtype WHERE SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        self.con.commit()

        subtypes = {}
        csr.execute(
            "SELECT DISTINCT T.Name AS Type, T.TypeID, PT.TypeID FROM Type T LEFT JOIN Type PT ON T.ParentTypeID = PT.TypeID WHERE T.ParentTypeID != 0 AND T.Published != 0")
        for row in csr.fetchall():
            ptype = row[0].lower()
            if ptype[-2:] == 'es':
                if ptype == "accessories":
                    ptype = "accessory"
                elif ptype == "wall sconces":
                    ptype = "wall sconce"
                elif ptype == "rosettes":
                    ptype = "rosette"
                elif ptype == "bookcases":
                    ptype = "bookcase"
                elif ptype == "consoles":
                    ptype = "console"
                elif ptype == "coffee tables":
                    ptype = "coffee table"
                elif ptype == "tables":
                    ptype = "table"
                elif ptype == "vases":
                    ptype = "vase"
                else:
                    ptype = ptype[0:-2]
            elif ptype[-1:] == 's':
                ptype = ptype[0:-1]

            subtypes.update({ptype: {"id": row[1], "parent": row[2]}})

        csr.execute(
            "SELECT T.SKU, T.Subtype, P.ProductTypeID FROM EditSubtype T LEFT JOIN Product P ON P.SKU = T.SKU WHERE T.IsManual = 0")
        for row in csr.fetchall():
            sku = row[0]
            subtype = row[1].lower()
            for key, value in subtypes.items():
                if key in subtype:
                    if value['parent'] == row[2]:
                        csr.execute("CALL AddToProductSubtype ({}, {})".format(
                            common.sq(sku), value['id']))
                        self.con.commit()

                        print(
                            f"Subtype: {value['parent']}:{value['id']} - Product: {sku}")

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditSubtype)
                                                            AND SKU IN (SELECT SKU FROM ProductSubtype PT JOIN Type T ON PT.SubtypeID = T.TypeID WHERE T.ParentTypeID != 0)""")
        self.con.commit()

        csr.execute("DELETE FROM EditSubtype")
        self.con.commit()

        csr.close()

    def size(self):
        csr = self.con.cursor()

        csr.execute(
            "DELETE FROM EditSize WHERE SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        self.con.commit()

        csr.execute("SELECT SKU, Size FROM EditSize WHERE IsManual = 0")
        for row in csr.fetchall():
            sku = row[0]
            size = row[1].lower()
            isLumbar = True
            for key in const.sizeDict.keys():
                if common.check_exact_word(key, size):
                    csr.execute("CALL AddToProductTag ({}, {})".format(
                        common.sq(sku), common.sq(const.sizeDict[key])))
                    self.con.commit()

                    print(f"Size: {const.sizeDict[key]} - Product: {sku}")

                    isLumbar = False

            if isLumbar:
                csr.execute(
                    f"SELECT productTypeId FROM Product WHERE SKU = '{sku}'")
                product = csr.fetchone()

                if product and product[0] == 5:  # Lumbar is Only for Pillows
                    csr.execute("CALL AddToProductTag ({}, {})".format(
                        common.sq(sku), common.sq('Lumbar')))
                    self.con.commit()

                    print(f"Size: Lumbar - Product: {sku}")

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditSize)
                                                            AND SKU IN (SELECT SKU FROM ProductTag PT JOIN Tag T ON PT.TagID = T.TagID WHERE T.ParentTagID = 7)""")
        self.con.commit()

        csr.execute("DELETE FROM EditSize")
        self.con.commit()

        csr.close()

    def collection(self):
        csr = self.con.cursor()

        csr.execute(
            "DELETE FROM EditCollection WHERE SKU IN (SELECT SKU FROM Product WHERE ProductID IS NULL)")
        self.con.commit()

        csr.execute("SELECT SKU, Collection FROM EditCollection")
        for row in csr.fetchall():
            sku = row[0]
            collection = row[1]

            csr.execute("CALL AddToProductCollection ({}, {})".format(
                        common.sq(sku), common.sq(collection)))

            print(f"Collection: {collection} - Product: {sku}")

        csr.execute("""INSERT INTO PendingUpdateTagBodyHTML (ProductID) SELECT ProductID FROM Product WHERE ProductID IS NOT NULL
                                                            AND ProductID NOT IN (SELECT ProductID FROM PendingUpdateTagBodyHTML)
                                                            AND SKU IN (SELECT SKU FROM EditCollection)""")
        self.con.commit()

        csr.execute("DELETE FROM EditCollection")
        self.con.commit()

        csr.close()
