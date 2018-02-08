from oauthlib.oauth2 import BackendApplicationClient
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
import json

api_url_base = "https://catalog.oaklandlibrary.org/iii/sierra-api/v4"
api_token_url = "https://catalog.oaklandlibrary.org/iii/sierra-api/v4/token"
api_limit = 999999999


def auth(api_key, api_secret):
    auth = HTTPBasicAuth(api_key, api_secret)
    client = BackendApplicationClient(client_id=api_key)
    session = OAuth2Session(client=client)
    session.fetch_token(token_url=api_url_base + "/token", auth=auth)
    return session


def patron_record_by_barcode(session, barcode):
    """Return the record number(s) for the given barcode number."""
    r = session.get(api_url_base + "/patrons/find?barcode=" + str(barcode))
    return r


def patrons_expiring_on_date(session, date):
    """Return the record number(s) for the given barcode number."""
    # dates go in to queries as MM-DD-YY, but come out in ISO-8601 (YYYY-MM-DD)
    q = {
        "target": {
            "record": {
                "type": "patron"
            },
            "id": 43
        },
        "expr": {
            "op": "equals",
            "operands": [
                date.strftime("%m/%d/%Y"),
                ""
            ]
        }
    }
    url = "/patrons/query?offset=0&limit=" + str(api_limit)
    headers = {'content-type': 'application/json'}
    data = json.dumps(q)
    r = session.post(api_url_base + url, data=data, headers=headers)
    return r
