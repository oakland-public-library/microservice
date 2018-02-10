from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from datetime import datetime
import json

api_url_base = "https://catalog.oaklandlibrary.org/iii/sierra-api/v4"
api_token_url = "https://catalog.oaklandlibrary.org/iii/sierra-api/v4/token"
api_limit = 999999999


class Patron:
    def __init__(self):
        self.api_data = None
        self.patron_number = None


def authenticate(api_key, api_secret):
    auth = HTTPBasicAuth(api_key, api_secret)
    client = BackendApplicationClient(client_id=api_key)
    session = OAuth2Session(client=client)
    session.fetch_token(token_url=api_url_base + "/token", auth=auth)
    return session


def patron_by_barcode(session, barcode):
    """Return the record number(s) for the given barcode number."""
    r = session.get(api_url_base + "/patrons/find?barcode=" + str(barcode))
    p = Patron()
    p.api_data = json.loads(r.text)
    p.patron_number = p.api_data['id']
    p.birthdate = datetime.strptime(p.api_data['birthDate'], '%Y-%m-%d')
    return p


def patron_holds(session, patron):
    """Return a list of hold id for the given patron."""
    response = session.get("{}/patrons/{}/holds".format(api_url_base,
                                                        patron.patron_number))
    entries = json.loads(response.text)['entries']
    return [x['id'].split('/')[-1] for x in entries]


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
    response = session.post(api_url_base + url, data=data, headers=headers)
    entries = json.loads(response.text)['entries']
    return [x['link'].split('/')[-1] for x in entries]
