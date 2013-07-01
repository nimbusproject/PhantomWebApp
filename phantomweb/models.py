from django.db import models

from phantomweb.random_primary import RandomPrimaryIdModel


class LaunchConfiguration(RandomPrimaryIdModel):
    name = models.CharField(max_length=128)
    username = models.CharField(max_length=128)

    def __str__(self):
        return "LaunchConfiguration: %s:%s:%s" % (self.username,
            self.id, self.name)

    class Meta(object):
        unique_together = ("name", "username")


class PublicLaunchConfiguration(RandomPrimaryIdModel):
    username = models.CharField(max_length=128)
    launch_configuration = models.ForeignKey(LaunchConfiguration)
    description = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return "PublicLaunchConfiguration: %s:%s:%s" % (self.username,
            self.launch_configuration.id, self.launch_configuration.name)

    class Meta(object):
        unique_together = ("username", "launch_configuration")


class LaunchConfigurationDB(models.Model):
    name = models.CharField(max_length=128)
    username = models.CharField(max_length=128)

    class Meta(object):
        verbose_name = "AutoScale Launch Configuration"
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
