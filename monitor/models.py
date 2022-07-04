from django.db import models


class Log(models.Model):
    source = models.CharField(max_length=200)
    date = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=200, default="Info")
    message = models.CharField(max_length=1000)

    def __str__(self):
        return "{} - {}".format(self.source, self.date)


class API(models.Model):
    brand = models.CharField(max_length=200)
    type = models.CharField(max_length=200, default="Product")
    url = models.CharField(max_length=1000)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}".format(self.brand, self.type)


class FTP(models.Model):
    brand = models.CharField(max_length=200)
    type = models.CharField(max_length=200, default="Product")
    url = models.CharField(max_length=1000)
    port = models.IntegerField(default=22)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - {}".format(self.brand, self.type)


class Schedule(models.Model):
    description = models.CharField(max_length=200)
    type = models.CharField(max_length=200, default="Robot")
    process = models.CharField(max_length=200)
    schedule = models.CharField(max_length=200)

    def __str__(self):
        return "{} - {}".format(self.type, self.process)
