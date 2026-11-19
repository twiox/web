from django.apps import AppConfig


class PublicConfig(AppConfig):
    """The public pages (landing, Interessierte, Veranstalter, Impressum, ...) and their sign-ups.

    The app was called "interested"; the label stays, so the database tables (interested_tester, ...),
    the migrations and "interested.Tester" references keep working without a database change.
    """

    name = "public"
    label = "interested"
