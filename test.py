#!/usr/bin/env python3

import sierra_api_client as api
import sierra_dna_client as dna
import datetime
import configparser
from pprint import pprint

config = configparser.ConfigParser()
config.read('microservice.conf')

API_KEY = config['sierra_api_client']['api_key']
API_SECRET = config['sierra_api_client']['api_secret']

DNA_PORT = config['sierra_dna_client']['port']
DNA_HOST = config['sierra_dna_client']['host']
DNA_DB = config['sierra_dna_client']['db']
DNA_USER = config['sierra_dna_client']['user']
DNA_PASS = config['sierra_dna_client']['pass']

# print("authenticating with API server...")
# session = api.authenticate(API_KEY, API_SECRET)

# print("getting patron record by barcode...")
# barcode = 22141012432304
# patron = api.patron_by_barcode(session, barcode)
# pprint(vars(patron))

# print("getting bib record..")
# bib = api.bib_record_by_id(session, holds[0])
# pprint(vars(bib))

# print("getting patrons with frozen holds expiring on date...")
# date = datetime.date(2018, 2, 21)
# patrons = api.patrons_with_frozen_holds_expiring_on_date(session, date)

# for p in patrons:
#     print("-------")
#     for h in p.holds:
#         pprint(vars(h))

# print("getting patrons expiring on date...")
# date = datetime.date(2018, 12, 25)
# r = api.patrons_expiring_on_date(session, date)
# print(r)

# print("getting patrons in zip code...")
# r = api.patrons_in_zipcode(session, 94610)
# print(r)

print("authenticating with DNA server...")
conn = dna.authenticate(DNA_DB, DNA_USER, DNA_PASS, DNA_HOST, DNA_PORT)

print("getting patrons in zip code...")
n = dna.patrons_in_zipcode(conn, 94612)
print(n)
