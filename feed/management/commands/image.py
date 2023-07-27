from django.core.management.base import BaseCommand

import os
import glob
import time
from PIL import Image

from library import debug, shopify

PROCESS = "Image"
BASEDIR = f"{os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))}/images"


class Command(BaseCommand):
    help = f"Run {PROCESS} processor"

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):

        if "main" in options['functions']:
            while True:
                with Processor() as processor:
                    processor.compress(path="product")
                    processor.compress(path="roomset")
                    processor.compress(path="hires")

                    total = processor.count(f"{BASEDIR}/compressed")
                    debug.debug(
                        PROCESS, 0, f"Uploading {total} files to Shopify")

                    shopify.UploadImageToShopify(f"{BASEDIR}/compressed")

                print("Finished process. Waiting for next run. {}:{}".format(
                    PROCESS, options['functions']))
                time.sleep(3600)


class Processor:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def compress(self, path):
        for infile in glob.glob(f"{BASEDIR}/{path}/*.*"):
            try:
                fpath, ext = os.path.splitext(infile)
                fname = os.path.basename(fpath)

                with Image.open(infile) as img:
                    if ext == "jpg":
                        compressed = img.convert("RGB").resize(
                            self.size(img), Image.LANCZOS)
                        compressed.save(
                            f"{BASEDIR}/compressed/{fname}.jpg", "JPEG")
                    elif ext == "png":
                        compressed = img.resize(
                            self.size(img), Image.LANCZOS)
                        compressed.save(
                            f"{BASEDIR}/compressed/{fname}.png", "PNG")
                    else:
                        debug.debug(PROCESS, 1, f"Unknow Image Type: {infile}")

                os.remove(infile)

                debug.debug(
                    PROCESS, 0, f"Successfully compressed {infile}")

            except Exception as e:
                debug.debug(
                    PROCESS, 1, f"Failed compresssing {infile}. {str(e)}")

    def size(self, img):
        MAX_WIDTH = 2048

        width, height = img.size

        if MAX_WIDTH < width:
            ratio = width / height
            return (MAX_WIDTH, int(MAX_WIDTH / ratio))
        else:
            return (width, height)

    def count(self, dir):
        total = 0
        for file in os.listdir(dir):
            if os.path.isfile(f"{dir}/{file}"):
                total += 1

        return total
