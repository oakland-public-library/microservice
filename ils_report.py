import io
import xlsxwriter
import csv
import datetime


def make_hdh(conn, ratio):
    sql = """
    SELECT
  bibrecord,
  bibtitle,
  holdcount,
  itemcount,
  coalesce(order_copies_count,0) as ordercopycount
FROM (
SELECT
  id2reckey(h.record_id) as bibrecord, /* bib record from holds view */
  brp.best_title as bibtitle, /* title from bib record property view */
  (
    SELECT COUNT(*)
    FROM sierra_view.hold h
    WHERE brp.bib_record_id = h.record_id
  ) AS holdcount, /* Return a count of holds for a given bib */
  (
    SELECT COUNT(*)
    FROM sierra_view.bib_record_item_record_link bil
    WHERE bil.bib_record_id = h.record_id
  ) AS itemcount, /* Return a count of items linked to a given bib */
    (
    SELECT SUM(copies)
    from
    (
    SELECT order_record_id
    FROM sierra_view.bib_record_order_record_link bol
    WHERE bol.bib_record_id = h.record_id
  ) AS totorders /* Return list of order records for a given bib with hold, 
  then sum up the eligible copies */
  JOIN sierra_view.order_record orrec
  ON orrec.record_id = totorders.order_record_id
  JOIN sierra_view.order_record_cmf orf
  ON orf.order_record_id = orrec.record_id
  where
  /* Return only orders records that are not received, and exclude multi 
  copies, otherwise counts will be duplicated */
  orrec.received_date_gmt IS NULL and orrec.order_status_code = 'o' 
  and orf.location_code != 'multi')
  AS order_copies_count
FROM
    sierra_view.hold h
JOIN sierra_view.bib_record_property brp
ON h.record_id = brp.bib_record_id
WHERE
    h.status = '0' /* Look for hold records with on-hold status only */
GROUP BY h.record_id, brp.best_title, holdcount
ORDER BY 3 DESC
) AS derivedtable /*Create derived table from subquery before 
filtering out based on ratio*/
/* Set the hold to item threshold here */
WHERE (holdcount::DECIMAL / COALESCE(NULLIF(itemcount,0),1))::DECIMAL >= (%s)"""
    cur = conn.cursor()
    cur.execute(sql, (ratio,))
    results = cur.fetchall()
    cur.close()
    results = [list(elem) for elem in results]
    for x in results:
        x.append('{0:.2f}'.format(int(x[2]) if x[3] == 0 else int(x[2])/int(x[3])))
    header = [{'label': 'Bib Record'},
              {'label': 'Bib Title'},
              {'label': 'Holds'},
              {'label': 'Items'},
              {'label': 'On Order Copies'},
              {'label': 'Hold-Item Ratio'}]
    report = {'header': header,
              'data': results,
              'description': 'High Demand Holds',
              'date': datetime.datetime.now().isoformat(),
              'ratio': ratio
              }
    return report


def create_excel(report):
    """return excel object in memory from report"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'strings_to_numbers': True,
                                            'in_memory': True})
    worksheet = workbook.add_worksheet()
    for count, values in enumerate(report['header']):
        worksheet.set_column(count, count, len(values['label']))
        worksheet.write(0, count,
                        values['label'])
    for rownum, row in enumerate(report['data'], 1):
        for col in range(len(row)):
            worksheet.write(rownum, col, row[col])
    workbook.close()
    return output


def create_csv(report):
    """return csv object in memory from report"""
    # create proxy stringIO object to work with csv writer
    proxy = io.StringIO()
    writer = csv.writer(proxy, dialect='excel')
    writer.writerow(x['label'] for x in report['header'])
    writer.writerows(report['data'])
    # create output bytesIO object to return to flask
    output = io.BytesIO()
    output.write(proxy.getvalue().encode('utf-8'))
    output.seek(0)
    proxy.close()
    return output
