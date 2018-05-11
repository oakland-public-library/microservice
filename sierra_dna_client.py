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


def ptype_name(conn, ptype):
    """Return the name for a given patron type ID"""
    cur = conn.cursor()
    cur.execute("select description from sierra_view.ptype_property_name " +
                "join sierra_view.ptype_property on id = ptype_id " +
                "where value = '{}' and iii_language_id = 1".format(ptype))
    r = cur.fetchall()
    cur.close()
    return r[0][0]


def branches(conn):
    """Return address and geographical data for all branches"""
    cur = conn.cursor()
    cur.execute("select code_num,address,address_latitude,address_longitude " +
                "from sierra_view.branch where address <> ''")
    r = cur.fetchall()
    cur.close()
    return [{'code': s[0], 'name': s[1].split('$')[0],
             'address': s[1].split('$')[1],
             'city_zip': s[1].split('$')[2],
             'phone': s[1].split('$')[3],
             'lat': s[2], 'lon': s[3]} for s in r]


def branch_by_id(conn, bid):
    """Return address and geographical data for a branch"""
    cur = conn.cursor()
    cur.execute("select code_num,address,address_latitude,address_longitude " +
                "from sierra_view.branch where code_num = {}".format(bid))
    r = cur.fetchone()
    cur.close()
    return {'code': r[0], 'name': r[1].split('$')[0],
            'address': r[1].split('$')[1],
            'city_zip': r[1].split('$')[2],
            'phone': r[1].split('$')[3],
            'latlon': [float(r[2]), float(r[3])]}


def branch_id_by_stat_group(conn, gid):
    """Return branch ID for a statistical group code"""
    cur = conn.cursor()
    cur.execute("select lc.branch_code_num from sierra_view.statistic_group " +
                "sg join sierra_view.location lc on sg.location_code = " +
                "lc.code where sg.code_num = {}".format(gid))
    r = cur.fetchone()
    cur.close()
    return r[0]


def bib_from_vol(conn, vol):
    """Return bib record from volume record """
    cur = conn.cursor()
    cur.execute("SELECT id2reckey(bv.bib_record_id) " +
                "FROM sierra_view.bib_record_volume_record_link bv " +
                "WHERE bv.volume_record_id = reckey2id('j{}')".format(vol))
    r = cur.fetchone()
    cur.close()
    return r[0][1:]

