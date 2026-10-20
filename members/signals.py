from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import EventAsset


@receiver(post_delete, sender=EventAsset)
def delete_event_asset_file(sender, instance, **kwargs):
    # also runs when the event is deleted (cascade)
    instance.file.delete(save=False)
