import re
from decimal import Decimal, InvalidOperation

from django.db import migrations, models


def to_decimal(text):
    """Reads "12", "12,50", "12.5", "15 €" or "15,-"; anything else, ambiguous or <= 0 gives None."""
    if not text:
        return None
    cleaned = text.replace("€", "").replace(" ", "").rstrip("-").rstrip(",.")
    if re.search(r"[.,]\d{3}$", cleaned):
        return None  # "1.000" could be a thousand or one euro
    cleaned = cleaned.replace(",", ".")
    try:
        value = Decimal(cleaned).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None
    return value if 0 < value < 1000 else None


def convert_salaries(apps, schema_editor):
    Trainer = apps.get_model("members", "Trainer")
    for trainer in Trainer.objects.select_related("user"):
        trainer.salary_value = to_decimal(trainer.salary)
        if trainer.salary and trainer.salary_value is None:
            print(f"\n  TAE von {trainer.user.first_name} {trainer.user.last_name} nicht lesbar: {trainer.salary!r} -> leer")
        trainer.save(update_fields=["salary_value"])


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0053_remove_groups"),
    ]

    operations = [
        migrations.AddField(
            model_name="trainer",
            name="salary_value",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.RunPython(convert_salaries, migrations.RunPython.noop),
        migrations.RemoveField(model_name="trainer", name="salary"),
        migrations.RenameField(model_name="trainer", old_name="salary_value", new_name="salary"),
        migrations.AlterField(
            model_name="trainer",
            name="salary",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=5, null=True, verbose_name="TAE pro Stunde"
            ),
        ),
    ]
