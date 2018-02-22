import psycopg2


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
