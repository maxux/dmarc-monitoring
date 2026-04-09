import os
import pymysql
from datetime import datetime
from .termcolor import termcolor as logger

class DMARCPersistance:
    def __init__(self, dbinfo):
        self.dbinfo = {
            "host": dbinfo["host"],
            "user": dbinfo["user"],
            "password": dbinfo["password"],
            "database": dbinfo["database"],
            "autocommit": True,
            "cursorclass": pymysql.cursors.DictCursor
        }

        self.db = None
        self.types = None

    def connect(self):
        logger.debug(f"[+] database: connecting to persistance backend")
        self.db = pymysql.connect(**self.dbinfo)

        if self.types is None:
            self.types = self.typesload()

    def disconnect(self):
        if self.db is not None:
            logger.debug(f"[+] database: disconnecting persistance backend")
            self.db.close()
            self.db = None

    def typesload(self):
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, rkey, name, severity FROM dmarc_types
        """)

        types = {}
        for row in cursor.fetchall():
            types[row['rkey']] = row

        return types

    def typeid(self, key):
        entry = self.types.get(key)
        if entry is None:
            return None

        return entry["id"]

    def resource(self, filename):
        report = None

        with open(filename, "rb") as f:
            report = f.read()

        basefile = os.path.basename(filename)
        data = {"filename": basefile, "report": report}

        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO dmarc_resources (filename, report)
            VALUES (%(filename)s, %(report)s)
            ON DUPLICATE KEY UPDATE
            created = CURRENT_TIMESTAMP, report = %(report)s

        """, data)

        return True

    def metadata(self, report):
        reportbegin = report["metadata"]["date_begin"]
        reportdt = datetime.fromtimestamp(reportbegin)
        reportdate = reportdt.strftime("%Y-%m-%d")

        receiveddt = datetime.fromtimestamp(report["mail"]["received"])
        received = receiveddt.strftime("%Y-%m-%d %H:%M:%S")

        parseddt = datetime.fromtimestamp(report["metadata"]["parsed"])
        parsed = parseddt.strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "receiver": report["mail"]["receiver"],
            "received": received,
            "parsed": parsed,
            "filename": os.path.basename(report["mail"]["sourcefile"]),
            "reportdate": reportdate,
            "orgname": report["metadata"]["organization"],
            "reportid": report["metadata"]["id"],
        }

        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO dmarc_reports (
                receiver, received, parsed, filename,
                rdate, orgname, reportid
            )
            VALUES (
                %(receiver)s, %(received)s, %(parsed)s, %(filename)s,
                %(reportdate)s, %(orgname)s, %(reportid)s
            )

        """, data)

        return cursor.lastrowid

    def policy(self, id, report):
        px = report["policy"]

        data = {
            "rid": id,
            "domain": px["domain"],
            "adkim": self.typeid(px["adkim"]),
            "aspf": self.typeid(px["aspf"]),
            "policy": self.typeid(px["p"]),
            "subpolicy": self.typeid(px["sp"]),
            "percent": px["pct"],
        }

        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO dmarc_reports_policy (
                rid, domain, adkim, aspf,
                policy, subpolicy, percent
            )
            VALUES (
                %(rid)s, %(domain)s, %(adkim)s, %(aspf)s,
                %(policy)s, %(subpolicy)s, %(percent)s
            )

        """, data)

        return True

    def record(self, id, record):
        px = record["row"]["policy"]
        adk = record["authresults"]["dkim"][0]
        asp = record["authresults"]["spf"][0]

        data = {
            "rid": id,
            "source": record["row"]["source"],
            "eamount": record["row"]["count"],
            "edisp": self.typeid(px["disposition"]),
            "edkim": self.typeid(px["dkim"]),
            "espf": self.typeid(px["spf"]),
            "ereason": self.typeid(px["reason"]["type"]),
            "ecomment": px["reason"]["comment"],
            "mailfrom": record["identifiers"]["hfrom"],
            "mailto": record["identifiers"]["envto"],
            "dkimdom": adk["domain"],
            "dkimresult": self.typeid(adk["result"]),
            "spfdom": asp["domain"],
            "spfresult": self.typeid(asp["result"])
        }

        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO dmarc_reports_records (
                rid, source,
                eamount, edisp, edkim, espf, ereason, ecomment,
                mailfrom, mailto,
                dkimdom, dkimresult, spfdom, spfresult
            )
            VALUES (
                %(rid)s, %(source)s,
                %(eamount)s, %(edisp)s, %(edkim)s, %(espf)s, %(ereason)s, %(ecomment)s,
                %(mailfrom)s, %(mailto)s,
                %(dkimdom)s, %(dkimresult)s, %(spfdom)s, %(spfresult)s
            )

        """, data)

        return True

    def report(self, report):
        # Save blob report content
        logger.debug(f"[+] database: saving resource: {report['mail']['sourcefile']}")
        self.resource(report["mail"]["sourcefile"])

        # Save report metadata
        logger.debug(f"[+] database: saving metadata: {report['metadata']['id']}")
        rid = self.metadata(report)

        # Save report policy
        logger.debug(f"[+] database: saving policy: id: {rid}, domain: {report['policy']['domain']}")
        self.policy(rid, report)

        # Save report records
        logger.debug(f"[+] database: saving records: id: {rid}, records: {len(report['records'])}")
        for record in report["records"]:
            self.record(rid, record)

        return rid
