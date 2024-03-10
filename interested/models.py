from django.db import models
from members.models import Session


# Create your models here.
## Probetrainingsanmeldungen
class Tester(models.Model):
    first_name = models.CharField("Vorname", max_length=400)
    last_name = models.CharField("Nachname", max_length=400)
    email = models.CharField("Email", max_length=300)
    birthday = models.DateTimeField("Geburtstag")
    telnr = models.CharField("Telefonnummer", max_length=300, blank=True, null=True)
    sex = models.CharField("Geschlecht", max_length=30)
    notes = models.TextField("Anmerkungen", blank=True, null=True)
    einverstaendnis = models.FileField(
        "Einverständniserklärung",
        upload_to=f"Probetrainings/Einverständnis/",
        null=True,
        blank=True,
    )
    batch = models.ForeignKey(
        "TesterBatch", on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TesterBatch(models.Model):
    name = models.CharField("Batchname", max_length=300)
    unique_ident = models.CharField("Identifier", max_length=300, blank=True, null=True)

    def __str__(self):
        return self.name if self.name else "Unbenannter Batch"


class TestSession(models.Model):
    batch = models.ForeignKey(TesterBatch, on_delete=models.CASCADE)
    session = models.ForeignKey(
        Session, on_delete=models.SET_NULL, null=True, blank=True
    )
    date = models.DateTimeField("Datum")
    testers = models.ManyToManyField(
        Tester, blank=True, verbose_name="Anwesende Probetrainingsmenschen"
    )

    def __str__(self):
        return f"{self.batch}:{self.date}"
