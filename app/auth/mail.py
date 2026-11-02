"""Bounded SMTP delivery. Mail errors never activate pending accounts."""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from html import escape
from urllib.parse import quote

from app.auth.settings import settings

logger = logging.getLogger(__name__)


def send_verification(recipient, value):
    config = settings()
    if config.mail_backend == 'fake':
        return
    message = EmailMessage()
    message['From'], message['To'] = config.mail_from, recipient
    message['Subject'] = 'Xác thực email Sổ học tập / Verify your email'
    link = config.base_url + '/#verify-email=' + quote(value, safe='')
    message.set_content('Xác thực email Sổ học tập trong 30 phút. Mở liên kết và xác nhận:\n\n'
                        + link + '\n\nNếu không đăng ký, bạn có thể bỏ qua thư này. '
                        'Không chia sẻ liên kết. / Verify your email within 30 minutes. '
                        'Ignore this message if you did not register.')
    message.add_alternative('<h1>Xác thực email Sổ học tập</h1><p>Liên kết hết hạn sau 30 phút.</p>'
                            '<p><a href="' + escape(link, quote=True) + '">Xác thực email / Verify email</a></p>'
                            '<p>Nếu không đăng ký, hãy bỏ qua thư này. Không chia sẻ liên kết.</p>', subtype='html')
    try:
        client = smtplib.SMTP_SSL if config.mail_security == 'tls' else smtplib.SMTP
        kwargs = {'context': ssl.create_default_context()} if config.mail_security == 'tls' else {}
        with client(config.mail_host, config.mail_port, timeout=10, **kwargs) as smtp:
            if config.mail_security == 'starttls':
                smtp.starttls(context=ssl.create_default_context())
            if config.mail_user:
                smtp.login(config.mail_user, config.mail_password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException):
        logger.warning('Auth mail stage=delivery code=smtp_unavailable')
