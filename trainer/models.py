from django.db import models
from members.models import Trainer, Group, Session, User
from multiselectfield import MultiSelectField
from PIL import Image
from django.urls import reverse

class Trainer_table(models.Model):
    title = models.CharField(max_length=140, blank=True, null=True)
    active = models.BooleanField(default=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    final_file = models.FileField(upload_to="trainer_tables", blank=True, null=True)
    
class Table_entry(models.Model):
    table = models.ForeignKey(Trainer_table, blank=True, null=True, on_delete=models.SET_NULL)
    date = models.DateTimeField(blank=True, null=True)
    day = models.TextField(blank=True, null=True)
    group = models.TextField(blank=True, null=True)
    start = models.TextField(blank=True, null=True)
    end = models.TextField(blank=True, null=True)
    dur = models.TextField(blank=True, null=True)
    notes = models.TextField(default = "")
    
    def __str__(self):
        return f"{self.date.strftime('%d.%m.%Y')}\t{self.day}\t{self.group}\t{self.start}\t{self.end}\t{self.dur}\t{self.notes}"

#
# We need to track the participation of members in the training sessions. This will eventually replace the Trainer_table model
# (or fill it automatically at the end of the month)
#

class TrainingSessionEntry(models.Model):
    trainer = models.ManyToManyField(Trainer, related_name='trainer', blank=True)
    cotrainer = models.ManyToManyField(Trainer, related_name='cotrainer', blank=True) # in the case we ever have different rates of payment again...
    session = models.ForeignKey(Session, related_name='session', blank=True, null=True, on_delete=models.SET_NULL) # link to a session to get all the related information
    date = models.DateTimeField(blank=True, null=True)
    day = models.TextField(blank=True, null=True)
    group = models.TextField(blank=True, null=True)
    start = models.TextField(blank=True, null=True)
    end = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    billed = models.BooleanField(default=False) # invoice sent!
    payed = models.BooleanField(default=False) # invoice payed

    def __str__(self):
        return f"{self.date.strftime('%d.%m.%Y')}-{self.group}"
    
    @property
    def get_trainers(self):
        trainers = list(self.trainer.all())
        trainers.extend(self.cotrainer.all())
        return set(trainers)



class TrainingSessionParticipant(models.Model):
    session = models.ForeignKey(TrainingSessionEntry, on_delete=models.CASCADE, related_name='participant')
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )  # set null, so that we still see the number of participants even after user is gone
    name = models.CharField("Name", max_length=200, null=True, blank=True) # in case of Probetraining or non-members
    notes = models.TextField("Notizen", blank=True, null=True) #add notes, e.g. if left earlier or if needed first aid

    def __str__(self):
        if user:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.name


class TrainingSessionInvoice(models.Model):
    date_billed = models.DateTimeField("Rechnungsdatum", blank=True, null=True)
    date_payed = models.DateTimeField("Bezahldatum", blank=True, null=True)
    trainer = models.ForeignKey(Trainer, related_name='invoice', on_delete=models.SET_NULL, null=True)
    sessions = models.ManyToManyField(TrainingSessionEntry, related_name='invoice')
    total_time = models.FloatField('Stunden', blank=True, null=True)
    total_money = models.FloatField('TAE', blank=True, null=True)
    invoice_pdf = models.FileField('PDF', blank=True, null=True, upload_to="trainer_tables/")

    def generate_pdf(self):
        """
        Generate a PDF and store it in this instance's invoice_pdf FileField using Platypus.
        """
        import io
        from django.core.files.base import ContentFile
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

        # Create in-memory buffer
        buffer = io.BytesIO()

        # Set up document
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        elements = []
        styles = getSampleStyleSheet()
        normal = styles["Normal"]
        heading = styles["Heading2"]

        # -----------------------
        # Header
        # -----------------------
        elements.append(Paragraph(f"Rechnungsdatum: {self.date_billed.strftime('%d.%m.%Y')}", heading))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Trainer: {self.trainer.user.first_name} {self.trainer.user.last_name}", normal))
        if self.trainer.license_number:
            elements.append(Paragraph(f"Lizenznummer: {self.trainer.license_number}", normal))
        if self.trainer.license_valid:
            elements.append(Paragraph(f"Gültigkeit: {self.trainer.license_valid.strftime('%d.%m.%Y')}", normal))
        elements.append(Spacer(1, 20))

        # -----------------------
        # Table
        # -----------------------
        table_data = [["Datum", "Tag", "Gruppe", "Von", "Bis", "Anmerkung"]]

        for session in self.sessions.all():
            table_data.append([
                session.date.strftime("%d.%m.%Y"),
                session.date.strftime('%a'),
                session.group,
                session.start,
                session.end,
                session.notes
            ])

        table = Table(table_data, repeatRows=1)
        table.hAlign = 'LEFT'

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        # -----------------------
        # Totals
        # -----------------------
        elements.append(Paragraph(f"Stunden: {self.total_time} mit TAE/Stunde: {self.trainer.salary} €", normal))
        elements.append(Paragraph(f"<b>Gesamt: {self.total_money} €</b>", normal))

        # -----------------------
        # Build PDF
        # -----------------------
        doc.build(elements)

        # Move buffer to beginning
        buffer.seek(0)

        # Save PDF to FileField
        filename = f"invoice_{self.date_billed.strftime('%d.%m.%Y')}_{self.trainer.pk}.pdf"
        self.invoice_pdf.save(filename, ContentFile(buffer.read()))
        buffer.close()