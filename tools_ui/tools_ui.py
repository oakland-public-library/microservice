#!/usr/bin/env python3

import sierra_api_client as api
import sierra_dna_client as dna
import ils_report
from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
import configparser
import json
from operator import itemgetter

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

MAPBOX_TOKEN = config['branch_map']['mapbox_token']


@app.route('/')
def root():
    return render_template('index.html')


@app.route('/find')
def find():
    return redirect('/{}/{}'.format(request.args.get('record_type'),
                                    request.args.get('record_id')))


@app.route('/test_bib')
def test_bib():
    record = api.BibRecord(api_data=json.load(open('test_bib.json')))
    return render_template('bib_record.html', record=record)


@app.route('/bib/<record_id>')
def bib(record_id):
    session = api.authenticate(API_KEY, API_SECRET)
    record_id = record_id.lstrip('b')
    record = api.bib_record_by_id(session, record_id)
    return render_template('bib_record.html', record=record, debug=True)


@app.route('/item/<record_id>')
def item(record_id):
    session = api.authenticate(API_KEY, API_SECRET)
    record = api.item_record_by_id(session, record_id)
    return render_template('item_record.html', record=record, debug=True)


@app.route('/patron/<record_id>')
def patron_id(record_id):
    session = api.authenticate(API_KEY, API_SECRET)
    record = api.patron_record_by_id(session, record_id)
    holds = api.patron_holds(session, record.record_id)
    conn = dna.authenticate(DNA_DB, DNA_USER, DNA_PASS, DNA_HOST, DNA_PORT)
    record.patron_type_name = dna.ptype_name(conn, record.patron_type)
    return render_template('patron_record.html', record=record, holds=holds,
                           debug=True)


@app.route('/patron/barcode/<barcode>')
def patron_bc(barcode):
    session = api.authenticate(API_KEY, API_SECRET)
    record = api.patron_record_by_barcode(session, barcode)
    holds = api.patron_holds(session, record.record_id)
    conn = dna.authenticate(DNA_DB, DNA_USER, DNA_PASS, DNA_HOST, DNA_PORT)
    record.patron_type_name = dna.ptype_name(conn, record.patron_type)
    return render_template('patron_record.html', record=record, holds=holds,
                           debug=True)


@app.route('/hold/<record_id>', methods=['GET', 'POST'])
def hold(record_id):
    session = api.authenticate(API_KEY, API_SECRET)
    if request.method == 'POST':
        if request.form.get('freeze'):
            api.freeze_hold(session, record_id)
        if request.form.get('unfreeze'):
            api.unfreeze_hold(session, record_id)
    record = api.hold_record_by_id(session, record_id)
    actions = [{'name': 'freeze', 'value': 'Freeze Hold'},
               {'name': 'unfreeze', 'value': 'Unfreeze Hold'}]
    return render_template('hold_record.html', record=record, actions=actions,
                           debug=True)


@app.route('/report/hdh')
def report():
    ratio = request.args.get('ratio', default=4)
    conn = dna.authenticate(DNA_DB, DNA_USER, DNA_PASS, DNA_HOST, DNA_PORT)
    report = ils_report.make_hdh(conn, ratio)
    return render_template('hdh_report.html', report=report)


@app.route('/branch')
def map_test():
    conn = dna.authenticate(DNA_DB, DNA_USER, DNA_PASS, DNA_HOST, DNA_PORT)
    branches = sorted(dna.branches(conn), key=itemgetter('name'))
    return render_template('branch_overview.html', mapbox_token=MAPBOX_TOKEN,
                           default_view=[37.794, -122.234],
                           branches=branches)


@app.route('/branch/<branch_id>')
def branch(branch_id):
    conn = dna.authenticate(DNA_DB, DNA_USER, DNA_PASS, DNA_HOST, DNA_PORT)
    branches = dna.branches(conn)
    branch = dna.branch_by_id(conn, branch_id)
    return render_template('branch.html', branch=branch,
                           mapbox_token=MAPBOX_TOKEN,
                           default_view=branch['latlon'],
                           branches=branches, debug=True)

@app.route('/a/<gid>')
def a(gid):
    conn = dna.authenticate(DNA_DB, DNA_USER, DNA_PASS, DNA_HOST, DNA_PORT)
    x = dna.branch_id_by_stat_group(conn, gid)
    r = {}
    r['api_data'] = [{'branch_id': x}]
    return render_template('patron_record.html', record=r, debug=True)


app.run(host='0.0.0.0')
