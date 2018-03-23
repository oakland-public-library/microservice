from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from datetime import datetime
import json

api_url_base = "https://catalog.oaklandlibrary.org/iii/sierra-api/v4"
api_token_url = "https://catalog.oaklandlibrary.org/iii/sierra-api/v4/token"
api_limit = 10


class PatronRecord:
    def __init__(self):
        self.api_data = None
        self.patron_id = None


class BibRecord:
    def __init__(self):
        self.api_data = None
        self.record_id = None


class HoldRecord:
    def __init__(self):
        self.api_data = None
        self.hold_id = None
        self.frozen = None


def authenticate(api_key, api_secret):
    auth = HTTPBasicAuth(api_key, api_secret)
    client = BackendApplicationClient(client_id=api_key)
    session = OAuth2Session(client=client)
    session.fetch_token(token_url=api_url_base + "/token", auth=auth)
    return session


def bib_record_by_id(session, record_id):
    """Return the record number(s) for the given barcode number."""
    r = session.get(api_url_base + "/bibs/{}".format((record_id)))
    bib = BibRecord()
    bib.api_data = json.loads(r.text)
    bib.record_id = bib.api_data['id']
    return bib


def hold_record_by_id(session, hold_id):
    """Return the hold record for the given hold ID."""
    r = session.get(api_url_base + "/patrons/holds/{}".format(str(hold_id)))
    h = HoldRecord()
    h.api_data = json.loads(r.text)
    h.hold_id = h.api_data['id'].split('/')[-1]
    h.record_type = h.api_data['recordType']
    h.frozen = h.api_data['frozen']

    if 'notNeededAfterDate' in h.api_data:
        h.expiration_date = datetime.strptime(h.api_data['notNeededAfterDate'],
                                              '%Y-%m-%d').date()
    else:
        h.expiration_date = None
    return h


def freeze_hold(session, hold_id):
    """Return a list of patron record numbers expiring on the given date."""
    query = {
        "freeze": True
    }
    headers = {'content-type': 'application/json'}
    data = json.dumps(query)
    r = session.put(api_url_base + "/patrons/holds/{}".format(str(hold_id)),
                    data=data, headers=headers)
    return r


def unfreeze_hold(session, hold_id):
    """Return a list of patron record numbers expiring on the given date."""
    query = {
        "freeze": False
    }
    headers = {'content-type': 'application/json'}
    data = json.dumps(query)
    r = session.put(api_url_base + "/patrons/holds/{}".format(str(hold_id)),
                    data=data, headers=headers)
    return r


def patron_record_by_id(session, patron_id):
    """Return the patron record for the given patron ID."""
    r = session.get(api_url_base + "/patrons/{}".format(str(patron_id)))
    p = PatronRecord()
    p.api_data = json.loads(r.text)
    p.patron_id = p.api_data['id']
    p.birth_date = datetime.strptime(p.api_data['birthDate'],
                                     '%Y-%m-%d').date()
    return p


def patron_record_by_barcode(session, barcode):
    """Return the record number(s) for the given barcode number."""
    r = session.get(api_url_base + "/patrons/find?barcode=" + str(barcode))
    p = PatronRecord()
    p.api_data = json.loads(r.text)
    p.patron_id = p.api_data['id']
    p.birthdate = datetime.strptime(p.api_data['birthDate'], '%Y-%m-%d')
    return p


def patron_holds(session, patron_id):
    """Return a list of hold IDs for the given patron."""
    r = session.get("{}/patrons/{}/holds".format(api_url_base, patron_id))
    entries = json.loads(r.text)['entries']
    ids = [x['id'].split('/')[-1] for x in entries]
    holds = []
    for i in ids:
        holds.append(hold_record_by_id(session, i))
    return holds


def patrons_expiring_on_date(session, date):
    """Return a list of patron record numbers expiring on the given date."""
    query = {
        "target": {
            "record": {
                "type": "patron"
            },
            "id": 43
        },
        "expr": {
            "op": "equals",
            "operands": [
                # dates go in to queries as MM-DD-YY,
                # but come out in ISO-8601 (YYYY-MM-DD)
                date.strftime("%m/%d/%Y"),
                ""
            ]
        }
    }
    url = "/patrons/query?offset=0&limit=" + str(api_limit)
    headers = {'content-type': 'application/json'}
    data = json.dumps(query)
    r = session.post(api_url_base + url, data=data, headers=headers)
    entries = json.loads(r.text)['entries']
    return [x['link'].split('/')[-1] for x in entries]


def patrons_with_frozen_holds_expiring_on_date(session, date):
    """Get patrons with expiring frozen holds.

    Returns an array of patron records, each with its holds attribute
    containing an array of hold records whose status is frozen and whose
    expiration date is the same as the date passed to this function.
    """

    query = {
        "queries": [
            {
                "target": {
                    "record": {
                        "type": "patron"
                    },
                    "id": 80807
                },
                "expr": {
                    "op": "equals",
                    "operands": [
                        # dates go in to queries as MM-DD-YY,
                        # but come out in ISO-8601 (YYYY-MM-DD)
                        date.strftime("%m/%d/%Y"),
                        ""
                    ]
                }
            },
            "and",
            {
                "target": {
                    "record": {
                        "type": "patron"
                    },
                    "id": 80804
                },
                "expr": {
                    "op": "equals",
                    "operands": [
                        "true",
                        ""
                    ]
                }
            }
        ]
    }

    url = "/patrons/query?offset=0&limit=" + str(api_limit)
    headers = {'content-type': 'application/json'}
    data = json.dumps(query)
    r = session.post(api_url_base + url, data=data, headers=headers)
    entries = json.loads(r.text)['entries']

    # Now we have a list of patron IDs, where each patron has at least one
    # frozen hold expiring on the specified date.
    patron_ids = [x['link'].split('/')[-1] for x in entries]

    patrons = []
    for patron_id in patron_ids:
        patron = patron_record_by_id(session, patron_id)
        patron.holds = []
        holds = patron_holds(session, patron_id)
        for hold_id in holds:
            hold = hold_record_by_id(session, hold_id)

            # Since the patron may have other holds are either not expiring,
            # or not frozen (or both) check for that here, and append only
            # the expiring frozen holds to our list.
            if hold.frozen:
                if date == hold.expiration_date:
                    patron.holds.append(hold)
    patrons.append(patron)
    return(patrons)


def patrons_in_zipcode(session, zipcode):
    """Get patrons in the specified zip code."""

    query = {
        "target": {
            "record": {
                "type": "patron"
            },
            "id": 80010
        },
        "expr": {
            "op": "equals",
            "operands": [
                str(zipcode),
                ""
            ]
        }
    }

    url = "/patrons/query?offset=0&limit={}".format(str(10))
    headers = {'content-type': 'application/json'}
    data = json.dumps(query)
    r = session.post(api_url_base + url, data=data, headers=headers)
    entries = json.loads(r.text)['entries']
    patron_ids = [x['link'].split('/')[-1] for x in entries]
    return patron_ids
