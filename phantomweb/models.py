from django.db import models

class PhantomInfoDB(models.Model):
    phantom_url = models.CharField(max_length=128)
    dburl = models.CharField(max_length=128)
    rabbithost = models.CharField(max_length=128)
    rabbituser = models.CharField(max_length=128)
    rabbitpassword = models.CharField(max_length=128)
    rabbitexchange = models.CharField(max_length=128)
    rabbitport = models.IntegerField()
    rabbitssl = models.BooleanField()

class UserPhantomInfoDB(models.Model):
    username = models.CharField(max_length=128)
    phantom_key = models.CharField(max_length=128)
    phantom_secret = models.CharField(max_length=128)
    phantom_url = models.CharField(max_length=128)
    public_key = models.CharField(max_length=1024)



