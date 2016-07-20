# -*- coding: utf-8 -*-

import smtplib
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


def send_email(subject, content, emails, mime='plain', sender=None, password=None):

    if not sender:
        mail_user = 'alarm@mfhui.com'
    else:
        mail_user = sender
    if not password:
        mail_pass = '9e134790f32297ad2f1134a816f05258'
    else:
        mail_pass = password
    mail_host = 'smtp.exmail.qq.com'
    mail_postfix = '@mfhui.com'

    me = '%s<%s@%s>' % (mail_user, mail_user, mail_postfix)

    for email in emails:
        msg = MIMEText(content, mime, _charset="UTF-8")
        msg['Subject'] = subject
        msg['From'] = me
        msg['To'] = email

        s = smtplib.SMTP()
        s.connect(mail_host)
        s.login(mail_user,  mail_pass)
        s.sendmail(me, email, msg.as_string())
        s.close()

    return True


def send_email_with_attachment(subject, content, emails,
                               attachment=None, mime='plain',
                               sender=None, password=None):
    """Send emails with attachment.

       attachment - attachment should have the structure below:
                    {
                      "application": "...", // e.g. vnd.ms-excel
                      "content": 'attachment content",
                      "Content-Disposition": "...",
                      // e.g. \'attachment;filename=order_statistics.xls'
                    }
    """
    if not sender:
        mail_user = "alarm@mfhui.com"
    else:
        mail_user = sender
    if not password:
        mail_pass = "9e134790f32297ad2f1134a816f05258"
    else:
        mail_pass = password
    mail_host = "smtp.exmail.qq.com"
    mail_postfix = "@mfhui.com"

    sender = '%s<%s@%s>' % (mail_user, mail_user, mail_postfix)

    file_msg = None
    if attachment:
        file_msg = MIMEBase("application",
                            attachment["application"])
        file_msg.set_payload(attachment["content"].getvalue())
        attachment["content"].close()
        encoders.encode_base64(file_msg)
        file_msg.add_header(
            "Content-Disposition",
            attachment["Content-Disposition"]
        )
    content_msg = MIMEText(content, mime, "utf-8")

    for email in emails:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = email
        msg.attach(content_msg)
        # Attach attachment
        if file_msg:
            msg.attach(file_msg)

        server = smtplib.SMTP()
        server.connect(mail_host)
        server.login(mail_user, mail_pass)
        server.sendmail(sender, email, msg.as_string())
        server.close()

    return True
