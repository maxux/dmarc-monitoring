import time
import traceback
from .report import DMARCReport
from .reporter import DMARCReporter
from .termcolor import termcolor as logger

class DMARCMonitor:
    def __init__(self, backend, persistance):
        self.backend = backend
        self.persistance = persistance

        self.reporter = DMARCReporter()

    def debug(self):
        info = {
            "filename": "workdir/sample-rua-dmarc-report.xml",
            "receiver": "local@debug.net",
            "received": int(time.time()),
        }

        logger.info(f"[+] processing: {info['filename']}")
        report = DMARCReport()
        report.process(info)

        # Dump Report
        self.reporter.dump(report)

        if self.persistance is None:
            return True

        try:
            self.persistance.connect()
            self.persistance.report(report.report)
            self.persistance.disconnect()

        except:
            traceback.print_exc()

        self.persistance.disconnect()
        return True

    def checker(self):
        unread = self.backend.unread()
        logger.debug(f"[+] mailbox: {len(unread)} unread messages")

        for id in unread:
            if not self.backend.isreport(id):
                logger.debug(f"[-] message: {id}: does not contains dmarc report")
                continue

            logger.debug(f"[+] message: {id}: extracting report")
            info = self.backend.extract(id)

            logger.info(f"[+] processing: {info['filename']}")
            report = DMARCReport()
            if not report.process(info):
                raise RuntimeError(f"Cannot process report {info['filename']}")

            self.reporter.dump(report)

            if self.persistance is None:
                # self.backend.setread(id)
                continue

            try:
                self.persistance.connect()
                self.persistance.report(report.report)
                self.persistance.disconnect()

            except:
                traceback.print_exc()
                self.persistance.disconnect()

            self.backend.setread(id)

        return True

    def recurrent(self):
        try:
            # if self.debug():
            #     return False

            if self.checker():
                return False

            return True

        except KeyboardInterrupt:
            print("")
            logger.warning("Interruption from keyboard, gracefully stopping")
            return False

    def monitor(self):
        while True:
            logger.process("[+] monitor: checking for new reports")

            if not self.recurrent():
                return False

            logger.process("[+] monitor: waiting for next cycle")

            try:
                time.sleep(1200)

            except KeyboardInterrupt:
                print("")
                logger.warning("Interruption from keyboard, gracefully stopping")
                exit(0)
