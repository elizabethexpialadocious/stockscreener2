# geneeal sendmail function

import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email.message import EmailMessage

import requests

# found this here
# https://stackoverflow.com/questions/3362600/how-to-send-email-attachments

# modified to use local sendmail which was not installed when I wrote
# the first version; it now uses gmail to send messages out of the # localhost


def send_with_attachment(sender, recipient, subject, body, files=None, body_mime_type='plain', bcc=None):
    '''
    send email via the lacal system with possible file attachment
    sender: email address sending the email
    recipient: person to whom it should be delivered
    subject: subject text
    body: text for the body of the message, note possibility of changing the mime type
    files: list of files, defaults to none
    body_mime_type: mime type of the body, defaults to plain text (e.g. 'html')

    '''
    # send_from, send_to, subject, text, files=None,
    # assert isinstance(recipient, list)

    receivers = [recipient]   # will be addended if bcc is defined below
    # this is the actual receivers of the email

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    if not (bcc is None) and isinstance(bcc, list):
        # msg['Bcc'] = COMMASPACE.join(bcc)
        # receivers = receivers + "," + COMMASPACE.join(bcc)
        receivers += bcc
        # print(msg['Bcc'])

    # msg.attach(MIMEText(body))

    part1 = MIMEText(body, body_mime_type)
    msg.attach(part1)

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)

    print(receivers)
    smtp = smtplib.SMTP("localhost")
    smtp.sendmail(msg['From'], receivers, msg.as_string())
    smtp.close()
