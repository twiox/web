from decimal import Decimal, InvalidOperation

from django.db import migrations, models

DEFAULT_LAT, DEFAULT_LONG = Decimal("51.347127"), Decimal("12.350504")


def to_coordinate(text, limit):
    """Reads "51.3602" or "51,3602"; None if unreadable or out of range."""
    try:
        value = Decimal(str(text).strip().replace(",", ".")).quantize(Decimal("0.000001"))
    except (InvalidOperation, ValueError):
        return None
    return value if -limit <= value <= limit else None


def convert_spots(apps, schema_editor):
    Spot = apps.get_model("members", "Spot")
    for spot in Spot.objects.all():
        lat, long = to_coordinate(spot.lat, 90), to_coordinate(spot.long, 180)
        if lat is None or long is None:
            print(f"\n  Spot {spot.title!r}: Koordinaten nicht lesbar ({spot.lat!r}, {spot.long!r}) -> Standardposition")
            lat, long = DEFAULT_LAT, DEFAULT_LONG
        spot.lat_value, spot.long_value = lat, long
        if spot.description.strip() == "Lorem Ipsum":  # the old default text
            spot.description = ""
        spot.save(update_fields=["lat_value", "long_value", "description"])


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0054_salary_as_decimal"),
    ]

    operations = [
        migrations.AddField(model_name="spot", name="lat_value", field=models.DecimalField(decimal_places=6, max_digits=9, null=True)),
        migrations.AddField(model_name="spot", name="long_value", field=models.DecimalField(decimal_places=6, max_digits=9, null=True)),
        migrations.RunPython(convert_spots, migrations.RunPython.noop),
        migrations.RemoveField(model_name="spot", name="lat"),
        migrations.RemoveField(model_name="spot", name="long"),
        migrations.RenameField(model_name="spot", old_name="lat_value", new_name="lat"),
        migrations.RenameField(model_name="spot", old_name="long_value", new_name="long"),
        migrations.AlterField(
            model_name="spot", name="lat",
            field=models.DecimalField("Breitengrad", decimal_places=6, max_digits=9, default=DEFAULT_LAT),
        ),
        migrations.AlterField(
            model_name="spot", name="long",
            field=models.DecimalField("Längengrad", decimal_places=6, max_digits=9, default=DEFAULT_LONG),
        ),
        migrations.AlterField(
            model_name="spot", name="description",
            field=models.TextField("Beschreibung", blank=True, default=""),
        ),
        # photos and the rendered markdown are no longer used
        migrations.RemoveField(model_name="spot", name="description_rendered"),
        migrations.RemoveField(model_name="spot", name="picture"),
    ]
