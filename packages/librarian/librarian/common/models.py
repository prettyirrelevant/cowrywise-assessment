from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField('created at')
    updated_at = models.DateTimeField('updated at')

    class Meta:
        abstract = True
