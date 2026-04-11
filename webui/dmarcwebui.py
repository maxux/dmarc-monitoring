import time
import pymysql
from datetime import datetime
from flask import Flask, request, jsonify, render_template, abort, g
from flask_babel import Babel, gettext, ngettext, format_datetime
from config import config

class DMARCWebUI:
    def __init__(self):
        self.config = config

        self.app = Flask(__name__, static_url_path='/static')
        self.app.url_map.strict_slashes = False

        self.app.config["DEBUG"] = True

        self.babel = Babel(self.app)
        self.babel.init_app(self.app, locale_selector=self.translation_get_locale)
        self.translations_accepted = ['en']

    def translation_get_locale(self):
        return "en"

    def database(self, autocommit=True):
        conninfo = {
            "host": self.config["db-server"],
            "user": self.config["db-user"],
            "password": self.config["db-password"],
            "database": self.config["db-dbname"],
            "autocommit": autocommit,
            "cursorclass": pymysql.cursors.DictCursor,
        }

        if "db-socket" in self.config:
            # unix socket is used in priority in pymysql
            # if unix socket path is specified,
            # even with host defined
            conninfo["unix_socket"] = self.config["db-socket"]

        return pymysql.connect(**conninfo)

    def typesload(self):
        cursor = g.db.cursor()
        cursor.execute("""
            SELECT id, rkey, name, severity
            FROM dmarc_types
        """)

        types = {}
        for row in cursor.fetchall():
            types[row["id"]] = row

        return types

    def typemap(self, id):
        return g.types.get(id, None)

    def reports(self):
        reports = []
        reportsmap = {}

        cursor = g.db.cursor()
        cursor.execute("""
            SELECT dr.id, dr.receiver, dr.received, dr.parsed, dr.filename,
                   dr.rdate, dr.orgname, dr.reportid,
                   drp.domain, drp.adkim, drp.aspf, drp.policy, drp.subpolicy,
                   drp.percent
            FROM dmarc_reports dr
            LEFT JOIN dmarc_reports_policy drp ON (drp.rid = dr.id)
            ORDER BY dr.rdate DESC
        """)

        for row in cursor.fetchall():
            row["records"] = []

            reports.append(row)
            reportsmap[row["id"]] = row

        cursor = g.db.cursor()
        cursor.execute("""
            SELECT id, rid, source,
                   eamount, edisp, edkim, espf, ereason, ecomment,
                   mailfrom, mailto,
                   dkimdom, dkimresult, spfdom, spfresult
            FROM dmarc_reports_records
            ORDER BY eamount DESC
        """)

        for record in cursor.fetchall():
            reportsmap[record["rid"]]["records"].append(record)

        return reports

    def aggregation(self):
        cursor = g.db.cursor()
        cursor.execute("""
            SELECT SUM(eamount) eamount, source, edisp, edkim, espf,
                   mailfrom, dkimdom, dkimresult, spfdom, spfresult
            FROM dmarc_reports_records
            GROUP BY edisp, edkim, espf, mailfrom, dkimdom, dkimresult, spfdom, spfresult
            ORDER BY eamount DESC
        """)

        return cursor.fetchall()

    def routes(self):
        @self.app.before_request
        def before_request_handler():
            # nothing to prepare for static files
            if request.path.startswith("/static"):
                return

            # always open a connection to database
            # we need it all the time (except for static content)
            g.db = self.database()
            g.types = self.typesload()

        @self.app.after_request
        def after_request_handler(response):
            # shortcut static files
            if request.path.startswith("/static"):
                return response

            # gracefully close database connection
            if "db" in g:
                g.db.close()

            return response

        @self.app.context_processor
        def inject_now():
            return {'now': datetime.utcnow()}

        """
        @self.app.get('/reports')
        def dmarc_reports():
            return jsonify({})
        """

        @self.app.get('/aggregation')
        def dmarc_aggregation():
            contents = {
                "aggregation": self.aggregation(),
                "types": g.types,
            }
            return render_template("aggregation.html", **contents)


        @self.app.get('/')
        def dmarc_index():
            contents = {
                "reports": self.reports(),
                "types": g.types,
            }
            return render_template("reports.html", **contents)

if __name__ == "dmarcwebui":
    print("[+] wsgi: initializing dmarc webui application")

    root = DMARCWebUI()
    root.routes()
    app = root.app
