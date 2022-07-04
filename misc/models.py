from django.db import models


class YotpoEmail(models.Model):
    email = models.EmailField(primary_key=True)

    def __str__(self):
        return self.email


class YotpoSMS(models.Model):
    email = models.EmailField(primary_key=True)

    def __str__(self):
        return self.email


class Config(models.Model):
    yotpo_email_marker = models.CharField(
        max_length=200, default="", null=True, blank=True)

    yotpo_sms_marker = models.CharField(
        max_length=200, default="", null=True, blank=True)

    last_processed_order = models.CharField(
        max_length=200, default="", null=True, blank=True)

    last_processed_sample = models.CharField(
        max_length=200, default="", null=True, blank=True)
