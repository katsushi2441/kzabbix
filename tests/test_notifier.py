from kzabbix.notifier import EmailNotifier


class FakeSMTP:
    def __init__(self, *args, **kwargs):
        self.logged_in = None
        self.message = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def login(self, username, password):
        self.logged_in = (username, password)

    def send_message(self, message):
        self.message = message


def test_authenticated_smtp_ssl_is_preferred(monkeypatch):
    smtp = FakeSMTP()
    monkeypatch.setattr("kzabbix.notifier.smtplib.SMTP_SSL", lambda *args, **kwargs: smtp)

    def unexpected_relay(*args, **kwargs):
        raise AssertionError("relay must not be used after authenticated SMTP succeeds")

    monkeypatch.setattr("kzabbix.notifier.requests.post", unexpected_relay)
    notifier = EmailNotifier(
        host="mail.example.jp",
        port=465,
        username="sender@example.jp",
        password="secret",
        sender="sender@example.jp",
        recipient="recipient@example.com",
        relay_url="https://relay.example.jp/notify.php",
        relay_token="relay-token",
    )

    notifier.send("test subject", "test report")

    assert smtp.logged_in == ("sender@example.jp", "secret")
    assert smtp.message["From"] == "sender@example.jp"
    assert smtp.message["To"] == "recipient@example.com"


def test_relay_is_used_when_authenticated_smtp_fails(monkeypatch):
    def failed_smtp(*args, **kwargs):
        raise OSError("SMTP unavailable")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    relay_calls = []

    def relay(*args, **kwargs):
        relay_calls.append((args, kwargs))
        return Response()

    monkeypatch.setattr("kzabbix.notifier.smtplib.SMTP_SSL", failed_smtp)
    monkeypatch.setattr("kzabbix.notifier.requests.post", relay)
    notifier = EmailNotifier(
        host="mail.example.jp",
        port=465,
        username="sender@example.jp",
        password="secret",
        sender="sender@example.jp",
        recipient="recipient@example.com",
        relay_url="https://relay.example.jp/notify.php",
        relay_token="relay-token",
    )

    notifier.send("test subject", "test report")

    assert len(relay_calls) == 1
