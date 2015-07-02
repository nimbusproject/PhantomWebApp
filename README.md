# Phantom Web Application

This repository contains the web application for [Phantom](http://www.nimbusproject.org/doc/phantom/latest/).

## Installation

To install the web application, you will need Python 2.7 and the [EPU services running](https://github.com/nimbusproject/epu).

After cloning this repository, run the following command, preferably inside a dedicated virtualenv:

    pip install -r requirements.txt --allow-external ceiclient --allow-unverified ceiclient --allow-external cloudinitd --allow-unverified cloudinitd .

You should then be able to run:

    python manage.py syncdb
    python manage.py runserver

Once it is running, go to the admin interface and set up the RabbitMQ
connection info at [http://127.0.0.1:8000/admin/phantomweb/rabbitinfodb/1/](http://127.0.0.1:8000/admin/phantomweb/rabbitinfodb/1/).
If you are running the EPU services on your own machine with the default
RabbitMQ settings, you can set it up with:

* host = 127.0.0.1
* user = guest
* password = guest
* exchange = default_dashi_exchange
* port = 5672
* SSL = off
