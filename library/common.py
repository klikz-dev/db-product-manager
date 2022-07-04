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
