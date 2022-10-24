from django.db import models


class Log(models.Model):
    class Meta:
        verbose_name = "Log"
        verbose_name_plural = "Logs"

    source = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=200, default="Info")
    message = models.CharField(max_length=1000)

    def __str__(self):
        return "{} - {}".format(self.source, self.date)


class Profit(models.Model):
    class Meta:
        verbose_name = "Cost of Goods"
        verbose_name_plural = "Cost of Goods"

    po = models.CharField(max_length=200, primary_key=True)
    type = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    cost = models.FloatField(default=0)
    price = models.FloatField(default=0)
    date = models.DateTimeField()

    def __str__(self):
        return "#{}".format(self.po)


class NoOrderCustomers(models.Model):
    class Meta:
        verbose_name = "No Order Customers"
        verbose_name_plural = "No Order Customers"

    customerId = models.CharField(max_length=200, primary_key=True)
    firstName = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    lastName = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    email = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    marketing = models.CharField(
        max_length=200, default=None, null=True, blank=True)
    date = models.DateTimeField()

    def __str__(self):
        return "{} {}".format(self.firstName, self.lastName)
