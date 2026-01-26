from django.db.models.signals import pre_delete
from django.dispatch import receiver

from report_maker.models import ExamObject


@receiver(pre_delete, sender=ExamObject)
def delete_examobject_images(sender, instance: ExamObject, **kwargs):
    instance.images.all().delete()
