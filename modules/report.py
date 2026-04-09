import gzip
import zipfile
import time
import xml.etree.ElementTree as xtree

from modules.termcolor import termcolor as logger

class DMARCReport:
    def __init__(self):
        # Specifications: https://dmarc.org/dmarc-xml/0.1/rua.xsd
        self.report = {
            "mail": {
                "sourcefile": None,
                "receiver": None,
                "received": None,
            },
            "metadata": {
                "id": None,             # Report ID
                "organization": None,   # Organization Name
                "date_begin": None,     # The time range in UTC covered by messages in this report
                "date_end": None,       #   specified in seconds since epoch
                "parsed": None,
            },
            "policy": {
                "domain": None,  # The domain at which the DMARC record was found
                "adkim": None,   # The DKIM alignment mode (relaxed or strict)
                "aspf": None,    # The SPF alignment mode (relaxed or strict)
                "p": None,       # The policy to apply to messages from the domain
                "sp": None,      # The policy to apply to messages from subdomains
                "pct": None,     # The percent of messages to which policy applies
            },
            "records": [],
        }

    def uncompress(self, target):
        data = None

        if target.endswith(".gz"):
            logger.debug(f"[+] uncompress: gunzip: {target}")
            with gzip.open(target, "rb") as fz:
                data = fz.read()

        if target.endswith(".zip"):
            logger.debug(f"[+] uncompress: unzip: {target}")
            with zipfile.ZipFile(target, "r") as fz:
                names = fz.namelist()
                if len(names) > 1:
                    raise NotImplemented("Multiple reports in zip file not supported")

                with fz.open(names[0]) as f:
                    data = f.read()

        if target.endswith(".xml"):
            with open(target, "rb") as f:
                data = f.read()

        return data

    def xval(self, root, tag):
        val = root.find(tag)
        if val is None:
            return None

        return val.text
    #
    # Reasons that may affect DMARC disposition or execution thereof:
    #
    #  forwarded:  Message was relayed via a known forwarder, or local
    #    heuristics identified the message as likely having been forwarded.
    #    There is no expectation that authentication would pass.
    #
    #  local_policy:  The Mail Receiver's local policy exempted the message
    #    from being subjected to the Domain Owner's requested policy
    #    action.
    #
    #  mailing_list:  Local heuristics determined that the message arrived
    #    via a mailing list, and thus authentication of the original
    #    message was not expected to succeed.
    #
    #  other:  Some policy exception not covered by the other entries in
    #    this list occurred.  Additional detail can be found in the
    #    PolicyOverrideReason's "comment" field.
    #
    #  sampled_out:  Message was exempted from application of policy by the
    #    "pct" setting in the DMARC policy record.
    #
    #  trusted_forwarder:  Message authentication failure was anticipated by
    #    other evidence linking the message to a locally-maintained list of
    #    known and trusted forwarders.
    #
    def record(self, root):
        # This element contains all the authentication results used to
        # evaluate the DMARC disposition for the given set of messages
        data = {
            "row": {
                "source": None,      # source_ip: The connecting IP
                "count": None,       # count: The number of matching messages
                "policy": {          # policy_evaluated: The DMARC disposition applying to matching messages
                    "disposition": None,
                    "dkim": None,    # dkim result type: pass or fail
                    "spf": None,     # spf result type: pass or fail
                    "reason": {      # See 'Reasons that may affect DMARC disposition' above
                        "type": None,
                        "comment": None,
                    },
                },
            },
            "identifiers": {
                "envto": None,       # envelope_to: The envelope recipient domain
                "hfrom": None,       # header_from: The payload From domain
            },
            "authresults": {
                "dkim": [],          # There may be no DKIM signatures, or multiple DKIM signatures
                "spf": [],           # There will always be at least one SPF result
            },
        }

        # Row
        xrow = root.find("row")
        row = data["row"]
        row["source"] = xrow.find("source_ip").text
        row["count"] = int(xrow.find("count").text)

        pe = xrow.find("policy_evaluated")
        px = row["policy"]
        px["disposition"] = pe.find("disposition").text
        px["dkim"] = pe.find("dkim").text
        px["spf"] = pe.find("spf").text

        reason = pe.find("reason")
        if reason:
            px["reason"]["type"] = reason.find("type").text
            px["reason"]["comment"] = self.xval(reason, "comment")

        # Identifiers
        xid = root.find("identifiers")
        ident = data["identifiers"]

        ident["envto"] = self.xval(xid, "envelope_to")
        ident["hfrom"] = xid.find("header_from").text

        # AuthResults
        xauth = root.find("auth_results")
        auth = data["authresults"]

        for dkim in xauth.iter("dkim"):
            auth["dkim"].append({
                "domain": dkim.find("domain").text,
                "result": dkim.find("result").text,
            })

        for spf in xauth.iter("spf"):
            auth["spf"].append({
                "domain": spf.find("domain").text,
                "result": spf.find("result").text,
            })

        return data

    def records(self, root):
        for rx in root.iter("record"):
            rec = self.record(rx)
            self.report["records"].append(rec)


    def policy_value(self, value):
        if value == "r":
            return "relaxed"

        if value == "s":
            return "strict"

        return value

    def policy_published(self, root):
        pp = root.find("policy_published")
        policy = self.report["policy"]

        for k in ["domain", "adkim", "aspf", "p", "sp", "pct"]:
            tag = pp.find(k)

            # Ignore missing field
            if tag is None:
                continue

            policy[k] = self.policy_value(tag.text)


    def report_metadata(self, root):
        md = root.find("report_metadata")
        info = self.report["metadata"]

        info["id"] = md.find("report_id").text
        info["organization"] = md.find("org_name").text

        drange = md.find("date_range")
        info["date_begin"] = int(drange.find("begin").text)
        info["date_end"] = int(drange.find("end").text)

    def report_mail(self, info):
        mail = self.report["mail"]
        meta = self.report["metadata"]

        mail["receiver"] = info["receiver"]
        mail["received"] = info["received"]
        mail["sourcefile"] = info["filename"]
        meta["parsed"] = int(time.time())


    def process(self, info):
        data = self.uncompress(info["filename"])
        if data is None:
            return None

        # Save mail internal metadata
        self.report_mail(info)

        # Load XML DOM
        root = xtree.fromstring(data)

        # Parse XML content
        self.report_metadata(root)
        self.policy_published(root)
        self.records(root)

        return True
