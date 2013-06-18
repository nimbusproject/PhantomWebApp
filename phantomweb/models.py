from django.db import models

from phantomweb.random_primary import RandomPrimaryIdModel


class LaunchConfiguration(RandomPrimaryIdModel):
    name = models.CharField(max_length=128)
    username = models.CharField(max_length=128)

    class Meta(object):
        unique_together = ("name", "username")


class LaunchConfigurationDB(models.Model):
    name = models.CharField(max_length=128)
    username = models.CharField(max_length=128)

    class Meta(object):
        unique_together = ("name", "username")


class HostMaxPairDB(models.Model):
    cloud_name = models.CharField(max_length=128)
    max_vms = models.IntegerField()
    launch_config = models.ForeignKey(LaunchConfigurationDB)
    rank = models.IntegerField()
    common_image = models.BooleanField()

    class Meta(object):
        unique_together = ("cloud_name", "launch_config")


class PhantomInfoDB(models.Model):
    phantom_url = models.CharField(max_length=128)
    dburl = models.CharField(max_length=128)

class RabbitInfoDB(models.Model):
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


class PhantomUser(models.Model):
    username = models.CharField(max_length=128, primary_key=True)
    access_key_id = models.CharField(max_length=128)
