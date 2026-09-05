from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend

from palvelut.metrics import record_email


class MetricsSMTPEmailBackend(SMTPEmailBackend):
    def send_messages(self, email_messages):
        try:
            sent = super().send_messages(email_messages)
        except Exception:
            record_email(delivered=False)
            raise
        for _ in range(sent):
            record_email(delivered=True)
        if sent < len(email_messages):
            for _ in range(len(email_messages) - sent):
                record_email(delivered=False)
        return sent
