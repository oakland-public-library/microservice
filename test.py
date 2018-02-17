#!/usr/bin/env python3

import sierra_api_client as sierra
import datetime
import configparser
from pprint import pprint

config = configparser.ConfigParser()
config.read('microservice.conf')

API_KEY = config['sierra_client_api']['api_key']
API_SECRET = config['sierra_client_api']['api_secret']


def authenticate():
    print("authenticating...")
    session = sierra.authenticate(API_KEY, API_SECRET)
    return session


session = authenticate()

# print("getting patron record by barcode...")
# barcode = 22141012432304
# patron = sierra.patron_by_barcode(session, barcode)
# pprint(vars(patron))

# print("getting bib record..")
# bib = sierra.bib_record_by_id(session, holds[0])
# pprint(vars(bib))

print("getting patrons with frozen holds expiring on date...")
date = datetime.date(2018, 2, 21)
patrons = sierra.patrons_with_frozen_holds_expiring_on_date(session, date)

for p in patrons:
    print("-------")
    for h in p.holds:
        pprint(vars(h))


# print("getting patron holds...")
# barcode = 22141012432304
# holds = sierra.patron_holds(session, patron_ids[0])
# print(holds)

# for hold_id in holds:
#     print("getting hold record...")
#     r = sierra.hold_record_by_id(session, hold_id)
#     pprint(vars(r))



# print("getting patrons expiring on date...")
# date = datetime.date(2018, 12, 25)
# r = sierra.patrons_expiring_on_date(session, date)
# print(r)
