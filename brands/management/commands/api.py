from django.core.management.base import BaseCommand
from monitor.models import API

import requests
import json
import time

from library import debug

debug = debug.debug


class Command(BaseCommand):
    help = 'Check API Status'

    def handle(self, *args, **options):
        while True:
            self.main()

            print("Finished Process. Waiting for Next run")
            time.sleep(86400)

    def main(self):
        apis = API.objects.all()
        for api in apis:
            if api.brand == "Scalamandre":
                try:
                    r = requests.post("http://scala-api.scalamandre.com/api/Auth/authenticate", headers={'Content-Type': 'application/json'}, data=json.dumps(
                        {"Username": "Decoratorsbest", "Password": "EuEc9MNAvDqvrwjgRaf55HCLr8c5B2^Ly%C578Mj*=CUBZ-Y4Q5&Sc_BZE?n+eR^gZzywWphXsU*LNn!"}))
                    j = json.loads(r.text)
                    API_TOKEN = j['token']

                    r = requests.get("{}".format(api.url), headers={
                                     'Authorization': 'Bearer {}'.format(API_TOKEN)})
                    if r.status_code == 200:
                        debug(
                            "API", 0, "API Status for {} - {} is good".format(api.brand, api.type))
                        api.status = True
                    else:
                        debug(
                            "API", 1, "API Status for {} - {} is not good".format(api.brand, api.type))
                except:
                    debug(
                        "API", 2, "Failed Checking API Status for {} - {}".format(api.brand, api.type))
                    pass

            if api.brand == "Kravet" and api.type == "Stock":
                try:
                    r = requests.get(
                        "{}?user=DBEST767&password=b1028H47kkr&pattern=BAMBOO&color=CHARCOAL".format(api.url))
                    if r.status_code == 200:
                        debug(
                            "API", 0, "API Status for {} - {} is good".format(api.brand, api.type))
                        api.status = True
                    else:
                        debug(
                            "API", 1, "API Status for {} - {} is not good".format(api.brand, api.type))
                except:
                    debug(
                        "API", 2, "Failed Checking API Status for {} - {}".format(api.brand, api.type))
                    pass

            if api.brand == "Maxwell":
                try:
                    r = requests.get("{}?count=1000&page=1".format(api.url), headers={
                                     'x-api-key': '286d17936503cc7c82de30e4c4721a67'})
                    if r.status_code == 200:
                        debug(
                            "API", 0, "API Status for {} - {} is good".format(api.brand, api.type))
                        api.status = True
                    else:
                        debug(
                            "API", 1, "API Status for {} - {} is not good".format(api.brand, api.type))
                except:
                    debug(
                        "API", 2, "Failed Checking API Status for {} - {}".format(api.brand, api.type))
                    pass

            if api.brand == "Fabricut" and api.type == "Product":
                try:
                    r = requests.get("{}/0026912".format(api.url))
                    if r.status_code == 200:
                        debug(
                            "API", 0, "API Status for {} - {} is good".format(api.brand, api.type))
                        api.status = True
                    else:
                        debug(
                            "API", 1, "API Status for {} - {} is not good".format(api.brand, api.type))
                except:
                    debug(
                        "API", 2, "Failed Checking API Status for {} - {}".format(api.brand, api.type))
                    pass

            if api.brand == "Fabricut" and api.type == "Stock":
                try:
                    r = requests.get("{}".format(api.url))
                    if r.status_code == 200:
                        debug(
                            "API", 0, "API Status for {} - {} is good".format(api.brand, api.type))
                        api.status = True
                    else:
                        debug(
                            "API", 1, "API Status for {} - {} is not good".format(api.brand, api.type))
                except:
                    debug(
                        "API", 2, "Failed Checking API Status for {} - {}".format(api.brand, api.type))
                    pass

            if api.brand == "Pindler" and api.type == "Stock":
                try:
                    r = requests.get(
                        "{}8406-SAGE&yards=10&token=683150AbX72VWZ312910tB5259532c".format(api.url))
                    if r.status_code == 200:
                        debug(
                            "API", 0, "API Status for {} - {} is good".format(api.brand, api.type))
                        api.status = True
                    else:
                        debug(
                            "API", 1, "API Status for {} - {} is not good".format(api.brand, api.type))
                except:
                    debug(
                        "API", 2, "Failed Checking API Status for {} - {}".format(api.brand, api.type))
                    pass

            if api.brand == "Ralph Lauren" and api.type == "Stock":
                try:
                    r = requests.get("{}?sku=RLL61104L.RL.0".format(api.url))
                    if r.status_code == 200:
                        debug(
                            "API", 0, "API Status for {} - {} is good".format(api.brand, api.type))
                        api.status = True
                    else:
                        debug(
                            "API", 1, "API Status for {} - {} is not good".format(api.brand, api.type))
                except:
                    debug(
                        "API", 2, "Failed Checking API Status for {} - {}".format(api.brand, api.type))
                    pass

            if api.brand == "Phillip Jefferies":
                try:
                    r = requests.get("{}".format(api.url))
                    if r.status_code == 200:
                        debug(
                            "API", 0, "API Status for {} - {} is good".format(api.brand, api.type))
                        api.status = True
                    else:
                        debug(
                            "API", 1, "API Status for {} - {} is not good".format(api.brand, api.type))
                except:
                    debug(
                        "API", 2, "Failed Checking API Status for {} - {}".format(api.brand, api.type))
                    pass

            if api.brand == "Seabrook" and api.type == "Stock":
                try:
                    r = requests.get("{}/NA525".format(api.url), headers={
                                     'x-api-key': 'Z0ELIAGuzd3poCHVVngGD7iS44qMuXfM51NWqLyC'})
                    if r.status_code == 200:
                        debug(
                            "API", 0, "API Status for {} - {} is good".format(api.brand, api.type))
                        api.status = True
                    else:
                        debug(
                            "API", 1, "API Status for {} - {} is not good".format(api.brand, api.type))
                except:
                    debug(
                        "API", 2, "Failed Checking API Status for {} - {}".format(api.brand, api.type))
                    pass

            if api.brand == "Stout":
                try:
                    r = requests.post("{}".format(api.url), data={
                                      'id': '7544-7', 'key': 'aeba0d7a-9518-4299-b06d-46ab828e3288'})
                    if r.status_code == 200:
                        debug(
                            "API", 0, "API Status for {} - {} is good".format(api.brand, api.type))
                        api.status = True
                    else:
                        debug(
                            "API", 1, "API Status for {} - {} is not good".format(api.brand, api.type))
                except:
                    debug(
                        "API", 2, "Failed Checking API Status for {} - {}".format(api.brand, api.type))
                    pass

            api.save()
