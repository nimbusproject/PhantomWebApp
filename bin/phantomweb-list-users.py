#!/usr/bin/env python

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'phantomweb.settings'

from django.contrib.auth.models import User

users = User.objects.all()
for i in users:
    print i
