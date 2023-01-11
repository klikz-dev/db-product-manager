import os
import cgi
import sqlite3
import csv
import pymysql
from library import db_config
from xml.sax.saxutils import escape
import boto3

db_host = db_config.db_endpoint
db_username = db_config.db_username
db_password = db_config.db_password
db_name = db_config.db_name
db_port = 3306

db_host_local = db_config.db_endpoint_local
db_port_local = db_config.db_port_local

aws_access_key = db_config.aws_access_key
aws_secret_key = db_config.aws_secret_key


def feed():
    #con = pymysql.connect(db_host_local, port=db_port_local, user=db_username, passwd=db_password, db=db_name, connect_timeout=5)
    con = pymysql.connect(db_host, user=db_username,
                          passwd=db_password, db=db_name, connect_timeout=5)
    csr = con.cursor()

    brands = ["York",
              "Fabricut",
              "Kravet",
              "Ralph Lauren"
              ]

    for brand in brands:
        print brand
        fName = "QBFeed_{}.csv".format(brand)
        if os.path.isfile(fName):
            os.remove(fName)

        csvData = []
        csr.execute("""SELECT DISTINCT P.ManufacturerPartNumber
                    FROM Product P JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                    WHERE M.Brand = {}""".format(sq(brand)))

        for row in csr.fetchall():
            mpn = row[0]
            csr.execute("""SELECT P.SKU
                    FROM Product P JOIN ProductManufacturer PM ON P.SKU = PM.SKU JOIN Manufacturer M ON PM.ManufacturerID = M.ManufacturerID
                    WHERE M.Brand = {} AND P.ManufacturerPartNumber = {}
                    LIMIT 1""".format(sq(brand), sq(mpn)))
            tmp = csr.fetchone()
            if tmp == None:
                continue
            sku = tmp[0]
            csvData.append([sku, mpn])

        with open(fName, 'wb') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerows(csvData)

        uploadToS3(fName)

    csr.close()
    con.close()


def formatter(s):
    if s != None and s != "":
        return cgi.escape(s)
    else:
        return ""


def sq(x):
    return "N'" + x.replace("'", "''") + "'"


def uploadToS3(fName):
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key,
                      aws_secret_access_key=aws_secret_key)
    bucket_name = 'decoratorsbestimages'

    s3.upload_file(fName, bucket_name, fName, ExtraArgs={'ACL': 'public-read'})


if __name__ == "__main__":
    print "Feed"
    feed()
