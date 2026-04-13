import os
import base64
import google.auth
import re

from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from .termcolor import termcolor as logger

SCOPES = ['https://mail.google.com/']

class DMARCBackendGMail:
    def __init__(self, domain, workdir="workdir"):
        self.domain = domain
        self.workdir = workdir

        # GMail API Credentials
        self.token = "token.json"

        if not os.path.exists(self.token):
            raise RuntimeError("No credentials token found")

        self.creds = Credentials.from_authorized_user_file(self.token, SCOPES)

    def unread(self):
        """Fetch a list of unread messages from inbox"""
        service = build('gmail', 'v1', credentials=self.creds)
        threads = []

        try:
            news = (service.users().threads().list(userId="me", q="is:unread").execute().get("threads", []))
            for thread in news:
                threads.append(thread['id'])

            return threads

        except HttpError as error:
            print(f"[-] retrieving unread thread failed, error occurred: {error}")

        return None


    def thread(self, threadid):
        service = build('gmail', 'v1', credentials=self.creds)

        try:
            content = (service.users().threads().get(userId="me", id=threadid).execute())
            return content

        except HttpError as error:
            print(f"[-] retrieving thread failed, error occurred: {error}")

        return None

    def findattachement(self, message):
                  # host    ! domain   ! from   ! to     .ext"
        match = r"([a-z\.]+)!([a-z\.]+)!([0-9]+)!([0-9]+).(.+)"
        payload = message["payload"]

        if "filename" in payload:
            if re.match(match, payload["filename"]):
                return payload

        if "parts" in payload:
            for part in payload["parts"]:
                if re.match(match, part["filename"]):
                    return part

        return None

    def isreport(self, id):
        messages = self.thread(id)
        if messages is None:
            return None

        if len(messages["messages"]) > 1:
            raise NotImplemented("Multiple messages in thread")

        return (self.findattachement(messages["messages"][0]) is not None)

    def saveattachement(self, msgid, attachid, filename):
        service = build('gmail', 'v1', credentials=self.creds)

        try:
            attachement = (service.users().messages().attachments().get(userId="me", messageId=msgid, id=attachid).execute())
            data = base64.urlsafe_b64decode(attachement["data"].encode("utf-8"))

            destination = f"{self.workdir}/{filename}"
            with open(destination, "wb") as f:
                f.write(data)

            return destination

        except HttpError as error:
            print(f"[-] retrieving thread failed, error occurred: {error}")

        return None

    # FIXME: avoid redoing download
    def extract(self, id):
        messages = self.thread(id)
        if messages is None:
            return None

        if len(messages["messages"]) > 1:
            raise NotImplemented("Multiple messages in thread")

        report = self.findattachement(messages["messages"][0])
        if report is None:
            return None

        attachmentid = report["body"]["attachmentId"]
        filesize = report["body"]["size"]
        filename = report["filename"]

        logger.process(f"[+] extract: download report: {filename} ({filesize} bytes)")
        target = self.saveattachement(id, attachmentid, filename)

        mailinfo = {
            "filename": target,
            "receiver": None,
            "received": None,
        }

        # Try to extract mail metadata from headers
        headers = messages["messages"][0]["payload"]["headers"]
        for header in headers:
            if header["name"] == "Delivered-To":
                mailinfo["receiver"] = header["value"]

            if header["name"] == "Date":
                received = datetime.strptime(header["value"], "%a, %d %b %Y %H:%M:%S %z")
                mailinfo["received"] = int(received.timestamp())

        return mailinfo

    def setread(self, id):
        service = build('gmail', 'v1', credentials=self.creds)

        query = {"removeLabelIds": ["UNREAD"]}
        parameters = {
            "userId": "me",
            "id": id,
            "body": query
        }

        flag = (service.users().threads().modify(**parameters).execute().get("threads", []))

        return True
