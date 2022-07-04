from misc.models import Config, YotpoEmail, YotpoSMS
from django.core.management.base import BaseCommand

from library import debug, config

import time
import requests
import json

debug = debug.debug


class Command(BaseCommand):
    help = 'Award Reward Points'

    def add_arguments(self, parser):
        parser.add_argument('functions', nargs='+', type=str)

    def handle(self, *args, **options):
        if "main" in options['functions']:
            while True:
                self.klaviyoEmail()
                self.klaviyoSMS()
                print("Completed process. Waiting for next run.")
                time.sleep(60)

    def klaviyoEmail(self):
        url = "https://a.klaviyo.com/api/v2/group/MwdTjY/members/all"
        headers = {"Accept": "application/json"}

        config_obj = Config.objects.first()
        marker = config_obj.yotpo_email_marker

        print(marker)

        if marker == "" or marker == None:
            querystring = {"api_key": config.klaviyo_key}

            response = requests.request(
                "GET", url, headers=headers, params=querystring)

            try:
                records = json.loads(response.text)
            except Exception as e:
                print(e)

            try:
                marker = records["marker"]
                config_obj.yotpo_email_marker = marker
                config_obj.save()
            except:
                marker = ""

        while marker:
            querystring = {"api_key": config.klaviyo_key, "marker": marker}

            response = requests.request(
                "GET", url, headers=headers, params=querystring)

            try:
                records = json.loads(response.text)
            except Exception as e:
                print(e)

            try:
                marker = records["marker"]
                config_obj.yotpo_email_marker = marker
                config_obj.save()
            except:
                marker = ""

        emails = []
        try:
            for record in records["records"]:
                email = record["email"]
                emails.append(email)

            for email in emails:
                try:
                    YotpoEmail.objects.get(email=email)
                    continue
                except YotpoEmail.DoesNotExist:
                    YotpoEmail.objects.create(email=email)
                    pass

                yotpoUrl = "https://loyalty.yotpo.com/api/v2/actions"

                yotpoPayload = {'type': 'CustomAction',
                                'customer_email': email,
                                'action_name': 'klaviyo_signup',
                                'reward_points': '15',
                                'history_title': 'Email Subscription'}

                yotpoHeaders = {
                    'x-guid': 'iFmwz0U2X_848XL9wZaPsg',
                    'x-api-key': 'QTi7jhR5TzhekEUwOpKn8Qtt'
                }

                response = requests.request(
                    "POST", yotpoUrl, headers=yotpoHeaders, data=yotpoPayload)

                print("Email: " + response.text)
        except Exception as e:
            print(e)
            pass

    def klaviyoSMS(self):
        url = "https://a.klaviyo.com/api/v2/group/Vj6WM6/members/all"
        headers = {"Accept": "application/json"}

        config_obj = Config.objects.first()
        marker = config_obj.yotpo_sms_marker

        if marker == "" or marker == None:
            querystring = {"api_key": config.klaviyo_key}

            response = requests.request(
                "GET", url, headers=headers, params=querystring)

            try:
                records = json.loads(response.text)

                marker = records["marker"]
                config_obj.yotpo_sms_marker = marker
                config_obj.save()
            except:
                marker = ""

        while marker:
            querystring = {"api_key": config.klaviyo_key, "marker": marker}

            response = requests.request(
                "GET", url, headers=headers, params=querystring)

            try:
                records = json.loads(response.text)

                marker = records["marker"]
                config_obj.yotpo_sms_marker = marker
                config_obj.save()
            except:
                marker = ""

        try:
            emails = []
            for record in records["records"]:
                email = record["email"]
                emails.append(email)

            for email in emails:
                try:
                    YotpoSMS.objects.get(email=email)
                    continue
                except YotpoSMS.DoesNotExist:
                    YotpoSMS.objects.create(email=email)
                    pass

                yotpoUrl = "https://loyalty.yotpo.com/api/v2/actions"

                yotpoPayload = {'type': 'CustomAction',
                                'customer_email': email,
                                'action_name': 'klaviyo_sms',
                                'reward_points': '15',
                                'history_title': 'SMS Subscription'}

                yotpoHeaders = {
                    'x-guid': 'iFmwz0U2X_848XL9wZaPsg',
                    'x-api-key': 'QTi7jhR5TzhekEUwOpKn8Qtt'
                }

                response = requests.request(
                    "POST", yotpoUrl, headers=yotpoHeaders, data=yotpoPayload)

                print("SMS: " + response.text)
        except Exception as e:
            print(e)
            pass
