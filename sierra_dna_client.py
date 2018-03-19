import psycopg2
from datetime import date

dna_limit = 1000


class User:
    def __init__(self):
        self.user_id = None
        self.login = None
        self.full_name = None
        self.last_password_change_gmt = None
        self.is_exempt = None
        self.is_suspended = None
        self.is_context_only = None


def authenticate(dbname, user, password, host, port):
    conn = psycopg2.connect(dbname=dbname, user=user, password=password,
                            host=host, port=port, sslmode='require')
    return conn


def patrons_in_zipcode(conn, zipcode):
    cur = conn.cursor()
    cur.execute("select count(*) as exact_count from " +
                "sierra_view.patron_record_address where " +
                "postal_code = '{}'".format(str(zipcode)))
    r = cur.fetchone()
    cur.close()
    return r[0]


def user_by_login(conn, login):
    cur = conn.cursor()
    cur.execute("SELECT * from sierra_view.iii_user where " +
                "name = '{}'".format(login))
    r = cur.fetchone()
    cur.close()
    u = User()
    u.user_id = r[0]
    u.login = r[1]
    u.full_name = r[4]
    u.last_password_change_gmt = r[14]
    u.is_exempt = r[15]
    u.is_suspended = r[16]
    u.is_context_only = r[17]
    return u


def new_titles(conn, since):
    since = since.strftime("%Y-%m-%d")
    now = date.today()
    now = now.strftime("%Y-%m-%d")
    print(since)
    print(now)
    cur = conn.cursor()
    cur.execute("select record_id from sierra_view.bib_record where " +
                "cataloging_date_gmt >= '{}' ".format(since) +
                "and cataloging_date_gmt <= '{}' ".format(now) +
                "limit {}".format(dna_limit))
    r = cur.fetchall()
    cur.close()
    return [n[0] for n in r]
