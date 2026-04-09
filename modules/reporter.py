from datetime import datetime
from .termcolor import termcolor as logger

class DMARCReporter:
    def __init__(self):
        pass

    def result(self, value):
        if value == "pass":
            return f"{logger.green}PASS{logger.reset}"

        if value == "fail":
            return f"{logger.red}FAIL{logger.reset}"

        if value == "none":
            return f"{logger.green}NONE{logger.reset}"

        if value == "reject":
            return f"{logger.red}DROP{logger.reset}"

        if value == "quarantine":
            return f"{logger.orange}SPAM{logger.reset}"

        return f"{logger.blpurple}{value}{logger.reset}"

    def xdt(self, epoch):
        return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M:%S")

    def dump(self, report):
        mx = report.report["mail"]
        md = report.report["metadata"]
        px = report.report["policy"]
        rc = report.report["records"]

        receiveddt = datetime.fromtimestamp(mx["received"])
        received = receiveddt.strftime("%Y-%m-%d %H:%M:%S")

        logger.debug("[~] -----------------------------------------------------------")
        logger.report("dmarc report id  ", md['id'])
        logger.report("organization name", md['organization'])
        logger.report("mail received by ", mx['receiver'], received)
        logger.report("report time range", f"{self.xdt(md['date_begin'])} - {self.xdt(md['date_end'])}")

        logger.debug("[~] -----------------------------------------------------------")

        logger.column("policy domain ", px['domain'])
        logger.column("dkim alignment", px['adkim'])
        logger.column("spf alignment ", px['aspf'])
        logger.column("domain dispos.", px['p'])
        logger.column("subdomain dis.", px['sp'])

        logger.debug("[~] -----------------------------------------------------------")

        for record in rc:
            row = record["row"]
            px = row["policy"]
            idx = record["identifiers"]
            auth = record["authresults"]

            src = row["source"]
            xfrom = idx["hfrom"]
            xto = idx["envto"] or "---"

            print(f"[:] {row['count']} messages from {src} ({xfrom} -> {xto})")

            disp = self.result(px["disposition"])
            dkim = self.result(px["dkim"])
            spf = self.result(px["spf"])

            rx = ""
            if px["reason"]["type"] is not None:
                rx = f"-- {px['reason']['type']}"

            print(f"[=] dmarc: {disp} / DKIM: {dkim} / SPF: {spf} {rx}")

            dk = auth["dkim"][0]
            sp = auth["spf"][0]

            dkr = self.result(dk["result"])
            spr = self.result(sp["result"])

            print(f"[=] dkim : {dkr} / {dk['domain']}")
            print(f"[=] spf  : {spr} / {sp['domain']}")
            print("[=]")

        logger.debug("[~] -----------------------------------------------------------")
