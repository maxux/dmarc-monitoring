from modules.gmail import DMARCBackendGMail
from modules.persistance import DMARCPersistance
from modules.processor import DMARCMonitor
from config import config

if __name__ == "__main__":
    dbinfo = {
        "host": config.get("db-server", None),
        "user": config.get("db-user", None),
        "password": config.get("db-password", None),
        "database": config.get("db-dbname", None),
    }

    backend = DMARCBackendGMail(config.get("dmarc-domain", None))
    persist = DMARCPersistance(dbinfo)

    if dbinfo["database"] is None:
        persist = None

    dmon = DMARCMonitor(backend, persist)
    dmon.monitor()
