#!/usr/bin/env python

import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'phantomweb.settings'

from django.contrib.auth.models import User

if len(sys.argv) != 5:
    sys.exit("usage: %s username email password" % sys.argv[0])

user = User.objects.create_user(sys.argv[1], sys.argv[2], sys.argv[3])
user.is_staff = False
user.is_superuser = False
user.save()
