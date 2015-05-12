from django.db import models
from django.utils import timezone


class SubscriberManager(models.Manager):
    """ Return only subscribers with active user accounts. """
    def get_queryset(self):
        return super().get_queryset().filter(user__is_active=True)


class CampaignManager(models.Manager):
    def active(self):
        """ Return active campaigns.

        """
        now = timezone.now()
        return self.get_queryset().filter(when__lte=now, until__gte=now)
