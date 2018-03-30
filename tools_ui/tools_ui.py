#!/usr/bin/env python3

import sierra_api_client as api
import sierra_dna_client as dna
import ils_report
from flask import Flask
from flask import render_template
from flask import request
import datetime
import configparser
from pprint import pprint
import json

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


@app.route('/bib/<record_id>')
def bib(record_id):
    if record_id == 'test':
        record = api.BibRecord(api_data=json.load(open('bib.json')))
    else:
        session = api.authenticate(API_KEY, API_SECRET)
        record = api.bib_record_by_id(session, record_id.lstrip('b'))
    return render_template('bib_record.html', record=record)


@app.route('/patron/<barcode>')
def patron(barcode):
    session = api.authenticate(API_KEY, API_SECRET)
    record = api.patron_record_by_barcode(session, barcode)
    holds = api.patron_holds(session, record.record_id)
    return render_template('patron_record.html', record=record, holds=holds,
                           barcode=barcode)


@app.route('/report')
def report():
    ratio = request.args.get('ratio', default=4)
    conn = dna.authenticate(DNA_DB, DNA_USER, DNA_PASS, DNA_HOST, DNA_PORT)
    report = ils_report.make_hdh(conn, ratio)
    return render_template('hdh_report.html', report=report)


app.run()
