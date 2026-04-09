from modules.gmail import DMARCBackendGMail
from modules.persistance import DMARCPersistance
from modules.processor import DMARCMonitor

if __name__ == "__main__":
    dbinfo = {
        "host": "",
        "user": "",
        "password": "",
        "database": "",
    }

    backend = DMARCBackendGMail("example.com")
    # persist = DMARCPersistance(dbinfo)
    persist = None

    dmon = DMARCMonitor(backend, persist)
    dmon.monitor()
