#!/usr/bin/env python3

import sierra_api_client as sierra
import datetime
import configparser

config = configparser.ConfigParser()
config.read('microservice.conf')

API_KEY = config['sierra_client_api']['api_key']
API_SECRET = config['sierra_client_api']['api_secret']


def auth():
    print("authenticating")
    session = sierra.auth(API_KEY, API_SECRET)
    return session


session = auth()

print("getting patron record by barcode")
barcode = 22141012432304
r = sierra.patron_record_by_barcode(session, barcode)
print(r.text)

print("getting patrons expiring on date")
date = datetime.date(2018, 12, 25)
r = sierra.patrons_expiring_on_date(session, date)
print(r)
