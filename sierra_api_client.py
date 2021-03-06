from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from datetime import datetime
import json

api_url_base = "https://catalog.oaklandlibrary.org/iii/sierra-api/v4"
api_token_url = "https://catalog.oaklandlibrary.org/iii/sierra-api/v4/token"
api_limit = 1000

# Which fields to retrieve for patron records. Certain fields may have
# sensitive patron information.
patron_api_fields = {'fields': 'default,fixedFields,barcodes,names'}

# Which fields to retrieve for bibliographic records.
bib_record_fields = {'fields': 'default,fixedFields,varFields,normTitle,'
                     'normAuthor,orders,locations,available'}

# Which fields to retrieve for item records.
item_record_fields = {'fields': 'default,fixedFields,varFields,barcode,'
                      'callNumber,status,itemType,bibIds'}

# Friendly names for record types
record_types = {'i': 'Item', 'b': 'Bibliographic', 'j': 'Volume'}

# URL paths for record types
hold_type_paths = {'i': 'item', 'b': 'bib', 'j': 'vol'}


class PatronRecord:
    def __init__(self, api_data=None):
        self.api_data = api_data
        self.record_id = api_data['id']
        self.patron_type = api_data['patronType']
        self.birthdate = datetime.strptime(api_data['birthDate'], '%Y-%m-%d')
        self.barcodes = api_data['barcodes']


class BibRecord:
    def __init__(self, api_data=None):
        self.api_data = api_data
        self.record_id = api_data['id']
        self.catalog_date = api_data.get('catalogDate', None)
        self.title = api_data['title'].title()
        self.author = api_data.get('author', None)
        self.material_type = api_data['materialType']['value']
        self.material_type_code = api_data['materialType']['code']
        self.publish_year = api_data.get('publishYear', None)
        self.available = api_data['available']
        self.isbns = isbns_from_api_data(api_data)
        self.jacket_url = jacket_url_from_isbns(self.isbns)
        self.bib_call = bib_call_num(api_data)
        self.pub_info = pub_info(api_data)


class ItemRecord:
    def __init__(self, api_data=None):
        self.api_data = api_data
        self.record_id = api_data['id']
        self.barcode = api_data['barcode'] if 'barcode' in api_data else None
        self.call = \
            api_data['callNumber'] if 'callNumber' in api_data else None
        self.status = api_data['status']['display']
        self.status_code = api_data['status']['code']
        self.item_type = api_data['itemType']
        self.bib_record = api_data['bibIds'][0]
        self.vol = vol_from_api_data(self.api_data)


class HoldRecord:
    def __init__(self, api_data=None):
        self.api_data = api_data
        self.record_id = api_data['id'].split('/')[-1]
        self.target_record_id = api_data['record'].split('/')[-1]
        self.target_record_type = record_types[api_data['recordType']]
        self.target_record_type_code = api_data['recordType']
        self.patron_record_id = api_data['patron'].split('/')[-1]
        self.frozen = api_data['frozen']
        d = api_data.get('placed', None)
        self.placed = \
            datetime.strptime(d, '%Y-%m-%d').date() if d else None
        d = api_data.get('notWantedBeforeDate', None)
        self.not_wanted_before = \
            datetime.strptime(d, '%Y-%m-%d').date() if d else None
        d = api_data.get('notNeededAfterDate', None)
        self.not_wanted_after = \
            datetime.strptime(d, '%Y-%m-%d').date() if d else None
        self.hold_type_path = hold_type_paths[self.target_record_type_code]


class CheckoutRecord:
    def __init__(self, api_data=None):
        self.api_data = api_data
        self.record_id = api_data['id'].split('/')[-1]
        self.patron_record_id = api_data['patron'].split('/')[-1]
        self.item_record_id = api_data['item'].split('/')[-1]
        self.barcode = api_data['item'].split('/')[-1]
        self.due_date = api_data['dueDate'].split('/')[-1]
        self.out_date = api_data['outDate'].split('/')[-1]


def authenticate(api_key, api_secret):
    auth = HTTPBasicAuth(api_key, api_secret)
    client = BackendApplicationClient(client_id=api_key)
    session = OAuth2Session(client=client)
    session.fetch_token(token_url=api_url_base + '/token', auth=auth)
    return session


def bib_record_by_id(session, record_id):
    """Return a bib record for the given record number"""
    d = session.get(api_url_base + '/bibs/{}'.format((record_id)),
                    params=bib_record_fields)
    r = BibRecord(api_data=json.loads(d.text))
    return r


def item_record_by_id(session, record_id):
    """Return a item record for the given record number"""
    d = session.get(api_url_base + '/items/{}'.format((record_id)),
                    params=item_record_fields)
    r = ItemRecord(api_data=json.loads(d.text))
    return r


def hold_record_by_id(session, hold_id):
    """Return the hold record for the given hold ID"""
    d = session.get(api_url_base + '/patrons/holds/{}'.format(str(hold_id)))
    r = HoldRecord(api_data=json.loads(d.text))
    return r


def checkout_record_by_id(session, checkout_id):
    """Return the hold record for the given hold ID"""
    d = session.get(api_url_base + '/patrons/checkouts/{}'.format(str(checkout_id)))
    r = CheckoutRecord(api_data=json.loads(d.text))
    return r


def freeze_hold(session, hold_id):
    """Return a list of patron record numbers expiring on the given date"""
    query = {
        'freeze': True
    }
    headers = {'content-type': 'application/json'}
    data = json.dumps(query)
    r = session.put(api_url_base + '/patrons/holds/{}'.format(str(hold_id)),
                    data=data, headers=headers)
    return r


def unfreeze_hold(session, hold_id):
    """Return a list of patron record numbers expiring on the given date"""
    query = {
        'freeze': False
    }
    headers = {'content-type': 'application/json'}
    data = json.dumps(query)
    r = session.put(api_url_base + '/patrons/holds/{}'.format(str(hold_id)),
                    data=data, headers=headers)
    return r


def patron_record_by_id(session, record_id):
    """Return the patron record for the given patron ID"""
    r = session.get(api_url_base + '/patrons/{}'.format(str(record_id)),
                    params=patron_api_fields)
    p = PatronRecord(api_data=json.loads(r.text))
    return p


def patron_record_by_barcode(session, barcode):
    """Return the record number(s) for the given barcode number"""
    r = session.get(api_url_base + '/patrons/find?barcode={}'.format(
        str(barcode)), params=patron_api_fields)
    p = PatronRecord(api_data=json.loads(r.text))
    return p


def patron_holds(session, record_id):
    """Return a list of hold IDs for the given patron"""
    r = session.get('{}/patrons/{}/holds'.format(api_url_base, record_id))
    entries = json.loads(r.text)['entries']
    ids = [x['id'].split('/')[-1] for x in entries]
    hold_ids = []
    for i in ids:
        hold_ids.append(i)
    return hold_ids


def patrons_expiring_on_date(session, date):
    """Return a list of patron record numbers expiring on the given date"""
    query = {
        'target': {
            'record': {
                'type': 'patron'
            },
            'id': 43
        },
        'expr': {
            'op': 'equals',
            'operands': [
                # dates go in to queries as MM-DD-YY,
                # but come out in ISO-8601 (YYYY-MM-DD)
                date.strftime('%m/%d/%Y'),
                ''
            ]
        }
    }
    url = '/patrons/query?offset=0&limit=' + str(api_limit)
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
        'queries': [
            {
                'target': {
                    'record': {
                        'type': 'patron'
                    },
                    'id': 80807
                },
                'expr': {
                    'op': 'equals',
                    'operands': [
                        # dates go in to queries as MM-DD-YY,
                        # but come out in ISO-8601 (YYYY-MM-DD)
                        date.strftime('%m/%d/%Y'),
                        ''
                    ]
                }
            },
            'and',
            {
                'target': {
                    'record': {
                        'type': 'patron'
                    },
                    'id': 80804
                },
                'expr': {
                    'op': 'equals',
                    'operands': [
                        'true',
                        ''
                    ]
                }
            }
        ]
    }

    url = '/patrons/query?offset=0&limit=' + str(api_limit)
    headers = {'content-type': 'application/json'}
    data = json.dumps(query)
    r = session.post(api_url_base + url, data=data, headers=headers)
    entries = json.loads(r.text)['entries']

    # Now we have a list of patron IDs, where each patron has at least one
    # frozen hold expiring on the specified date.
    record_ids = [x['link'].split('/')[-1] for x in entries]

    patrons = []
    for record_id in record_ids:
        patron = patron_record_by_id(session, record_id)
        patron.holds = []
        holds = patron_holds(session, record_id)
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
    """Get patrons in the specified zip code"""

    query = {
        'target': {
            'record': {
                'type': 'patron'
            },
            'id': 80010
        },
        'expr': {
            'op': 'equals',
            'operands': [
                str(zipcode),
                ''
            ]
        }
    }

    url = '/patrons/query?offset=0&limit={}'.format(str(api_limit))
    headers = {'content-type': 'application/json'}
    data = json.dumps(query)
    r = session.post(api_url_base + url, data=data, headers=headers)
    entries = json.loads(r.text)['entries']
    record_ids = [x['link'].split('/')[-1] for x in entries]
    return record_ids


def isbns_from_api_data(api_data):
    isbns = [[y['content'] for y in x['subfields'] if y['tag'] == 'a']
             for x in api_data['varFields'] if x['fieldTag'] == 'i']
    return [s[0].split()[0] for s in isbns]


def jacket_url_from_isbns(isbns):
    # TODO: get "best" ISBN for jacket image
    isbn = isbns[0] if isbns else None
    return ('http://imagesa.btol.com/ContentCafe/Jacket.aspx'
            '?UserID=ContentCafeClient&Password=Client'
            '&Return=T&Type=L&Value={}'.format(str(isbn)))


def bib_call_num(api_data):
    """get first a-tagged call number from c index in varfields"""
    call_num = [[y['content'] for y in x['subfields'] if y['tag'] == 'a']
                for x in api_data['varFields'] if x['fieldTag'] == 'c']
    call_num = [x for sc in call_num for x in sc]
    return call_num[0] if len(call_num) else None


def pub_info(api_data):
    """return concatenated pub info from subfields of p tagged varfield"""
    pub_data = [[y['content'] for y in x['subfields']]
                for x in api_data['varFields'] if x['fieldTag'] == 'p']
    pub_data = ' '.join([x for sc in pub_data for x in sc])
    return pub_data


def vol_from_api_data(api_data):
    """return first v tagged volume in item varfields"""
    vol = [x['content'] for x in api_data['varFields']
           if x['fieldTag'] == 'v']
    return vol[0] if vol else None


def patron_checkouts(session, record_id):
    """Return a list of checkout ids for the given patron"""
    r = session.get('{}/patrons/{}/checkouts'.format(api_url_base, record_id))
    entries = json.loads(r.text)['entries']
    ids = [x['id'].split('/')[-1] for x in entries]
    return ids
