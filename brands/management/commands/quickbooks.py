from django.core.management.base import BaseCommand

import os
import xlsxwriter
import pymysql
from xml.sax.saxutils import escape
import boto3
import time

from library import debug

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
aws_access_key = env('aws_access_key')
aws_secret_key = env('aws_secret_key')

debug = debug.debug

FILEDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FEEDDIR = FILEDIR + '/files/feed/QuickBooks.xlsx'


class Command(BaseCommand):
    help = 'Generate Quickbooks feed'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "main" in options['functions']:
            while True:
                self.feed()
                self.upload()
                time.sleep(36400)

    def feed(self):
        con = pymysql.connect(host=db_host, user=db_username,
                              passwd=db_password, db=db_name, connect_timeout=5)
        csr = con.cursor()

        if os.path.isfile(FEEDDIR):
            os.remove(FEEDDIR)
        workbook = xlsxwriter.Workbook(FEEDDIR)
        worksheet = workbook.add_worksheet()

        worksheet.write(0, 0, 'Code')
        worksheet.write(0, 1, 'Cost')
        worksheet.write(0, 2, 'Price')
        worksheet.write(0, 3, 'Type')
        worksheet.write(0, 4, 'desc')
        worksheet.write(0, 5, 'income')
        worksheet.write(0, 6, 'cogs')
        worksheet.write(0, 7, 'reimbursable')

        csr.execute("""SELECT P.SKU AS Code, PV.Cost AS Cost, PV.Price AS Price, P.Name AS 'desc'
                        FROM Product P JOIN ProductVariant PV ON P.SKU = PV.SKU
                        WHERE PV.IsDefault = 1 AND P.Published = 1""")

        cnt = 0
        for row in csr.fetchall():
            cnt += 1

            sku = row[0]
            cost = row[1]
            price = row[2]
            name = row[3]

            worksheet.write(cnt, 0, sku)
            worksheet.write(cnt, 1, cost)
            worksheet.write(cnt, 2, price)
            worksheet.write(cnt, 3, "non-inventory part")
            worksheet.write(cnt, 4, name)
            worksheet.write(cnt, 5, "Sales Income")
            worksheet.write(cnt, 6, "Cost of Goods Sold")
            worksheet.write(cnt, 7, "yes")

        workbook.close()
        csr.close()
        con.close()

    def upload(self):
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key,
                          aws_secret_access_key=aws_secret_key)
        bucket_name = 'decoratorsbestimages'

        s3.upload_file(FEEDDIR, bucket_name,
                       "QuickBooks.xlsx", ExtraArgs={'ACL': 'public-read'})
        debug("QuickBooks", 0,
              'Uploaded to https://decoratorsbestimages.s3.amazonaws.com/QuickBooks.xlsx')
