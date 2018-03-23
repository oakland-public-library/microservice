#!/usr/bin/env python3

import sierra_api_client as api
import sierra_dna_client as dna
from flask import Flask
from flask import render_template
import datetime
import configparser
from pprint import pprint

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('../microservice.conf')

API_KEY = config['sierra_api_client']['api_key']
API_SECRET = config['sierra_api_client']['api_secret']

DNA_PORT = config['sierra_dna_client']['port']
DNA_HOST = config['sierra_dna_client']['host']
DNA_DB = config['sierra_dna_client']['db']
DNA_USER = config['sierra_dna_client']['user']
DNA_PASS = config['sierra_dna_client']['pass']


@app.route('/')
def root():
    return 'Hello, World!'


@app.route('/patron/<barcode>')
def patron(barcode):
    print("authenticating with API server...")
    session = api.authenticate(API_KEY, API_SECRET)
    print("getting patron record by barcode...")
    patron = api.patron_record_by_barcode(session, barcode)
    print("getting holds for patron...")
    holds = api.patron_holds(session, patron.patron_id)
    return render_template('patron.html', patron=patron, holds=holds,
                           barcode=barcode)


@app.route('/test')
def test():
    return render_template('test.html')


app.run()
