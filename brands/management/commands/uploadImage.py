from pathlib import Path
from django.core.management.base import BaseCommand

import time
from os import listdir, remove
from os.path import isfile, join, isdir
from PIL import Image
from resizeimage import resizeimage

from library import debug, shopify

debug = debug.debug

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PATH_OUT = BASE_DIR / "images/compressed/"


class Command(BaseCommand):
    help = 'Upload Image to Shopify'

    def handle(self, *args, **options):
        while True:
            self.compressProductImages(
                BASE_DIR / "images/product/")

            self.compressRoomshotImages(
                BASE_DIR / "images/roomset/")

            self.dirFileCount(
                BASE_DIR / "images/compressed/")

            self.uploadImages(
                BASE_DIR / "images/compressed/")

            print("Completed. Waiting for next run.")

            time.sleep(3600)

    def compressProductImages(self, mypath):
        good, total = 0, 0

        for f in listdir(mypath):
            total = total + 1
            isOk = False

            try:
                fd_img = open(join(mypath, f), 'rb')

                #### Fix Webp Images ####
                if f.split(".")[1] == "webp":
                    img_tmp = Image.open(fd_img).convert("RGB")
                    img_tmp.save(
                        join(mypath, f.split(".")[0]) + ".jpg", "jpeg")

                    # remove(fd_img)
                    img = Image.open(join(mypath, f.split(".")[0]) + ".jpg")
                else:
                    img = Image.open(fd_img)
                ###########################

                width, height = img.size
                scalew = min(500, width, height)

                if scalew < 100:
                    debug("Image", 1, "Ignored image {}. Size too small".format(f))
                else:
                    ######################################################
                    #### Comment below for Scalamandre & Decor Brands ####
                    ######################################################
                    # img = resizeimage.resize_cover(img, [scalew, scalew])
                    ######################################################

                    img.save(join(PATH_OUT, f), img.format)
                    debug(
                        "Image", 0, "Status check for Image {} successful. Good to upload".format(f))
                    good = good + 1

                    remove(join(mypath, f))

                fd_img.close()

            except Exception as e:
                debug("Image", 1,
                      "Optimizing image {} Failed. File type error.".format(f))
                print(e)
                fd_img.close()

        print('total, uploaded : ' + str(total) + ',' + str(good))

    def compressRoomshotImages(self, mypath):
        good, total = 0, 0

        for f in listdir(mypath):
            total = total + 1
            isOk = False

            try:
                fd_img = open(join(mypath, f), 'rb')
                img = Image.open(fd_img)
                width, height = img.size
                scalew = min(500, width, height)

                if scalew < 100:
                    debug("Image", 1, "Ignored image {}. Size too small".format(f))
                else:
                    img.save(join(PATH_OUT, f), img.format)
                    debug(
                        "Image", 0, "Status check for Image {} successful. Good to upload".format(f))
                    good = good + 1
                    isOk = True

                if isOk:
                    m = 'delete'
                    remove(join(mypath, f))

                fd_img.close()

            except Exception as e:
                debug("Image", 1,
                      "Optimizing image {} Failed. File type error.".format(f))
                print(e)
                fd_img.close()

        print('total, uploaded : ' + str(total) + ',' + str(good))

    def dirFileCount(self, mypath):
        ct = 0
        for f in listdir(mypath):
            if isfile(join(mypath, f)):
                ct = ct + 1

        print('Total to be uploaded to Shopify : ' + str(ct))

    def uploadImages(self, mypath):
        shopify.UploadImageToShopify(mypath)
