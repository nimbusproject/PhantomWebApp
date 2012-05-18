from django.db import models

class PhantomInfoDB(models.Model):
    phantom_url = models.CharField(max_length=128)
    dburl = models.CharField(max_length=128)

class DefaultCloudsDB(models.Model):
    name = models.CharField(max_length=128)
    url = models.CharField(max_length=128)

class UserPhantomInfoDB(models.Model):
    username = models.CharField(max_length=128)
    phantom_key = models.CharField(max_length=128)
    phantom_secret = models.CharField(max_length=128)
    phantom_url = models.CharField(max_length=128)
    public_key = models.CharField(max_length=1024)

class UserCloudInfoDB(models.Model):
    cloudname = models.CharField(max_length=128)
    username = models.CharField(max_length=128)
    iaas_key = models.CharField(max_length=128)
    iaas_secret = models.CharField(max_length=128)
    cloud_url = models.CharField(max_length=128)




