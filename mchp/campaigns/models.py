from django.core.mail import get_connection
from django.db import models
from django.template import Context, Template
from django.utils import timezone
from django.conf import settings
from . import managers

import smtplib
from . import utils

# all campaigns will be sent from this email address
CAMPAIGN_FROM_EMAIL = 'mchp <study@mycollegehomepage.com>'
CAMPAIGN_SUBSCRIBER_BACKING = settings.AUTH_USER_MODEL


class BaseCampaignSubscriber(models.Model):
    """ Abstract base class for subscriber in a campaign.

    Attributes
    ----------
    campaign : campaigns.models.Campaign
        The campaign associated with this subscriber.
    notified : django.db.models.DateTimeField
        When was this user notified?
    # did_unsubscribe : django.db.models.BooleanField
    #     Has this user unsubscribed?
    opens : django.db.models.PositiveIntegerField
        How many opens has this user generated?
    clicks : django.db.models.PositiveIntegerField
        How many click-throughs has this user generated?

    """
    campaign = models.ForeignKey('Campaign', related_name='subscribers')
    notified = models.DateTimeField(blank=True, null=True)
    # unsubscribed = models.BooleanField(default=True)
    opens = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        verbose_name = 'subscriber'

    def mark_notified(self):
        """ Mark subscriber as notified now. """
        self.notified = timezone.now()
        self.save(update_fields=['notified'])

    def is_notified(self):
        """ Has this user been notified?

        """
        return self.notified is not None


class CampaignSubscriber(BaseCampaignSubscriber):
    """ Subscriber in a campaign.

    Attributes
    ----------
    user : django.db.models.ForeignKey
        A user account backing this subscriber.

    """
    user = models.ForeignKey(CAMPAIGN_SUBSCRIBER_BACKING)

    objects = managers.SubscriberManager()

    class Meta:
        unique_together = ('campaign', 'user')

    def __str__(self):
        return self.user.get_full_name()


class BaseCampaignTemplate(models.Model):
    """ Abstract base for contents of a campaign template.

    Attributes
    ----------
    subject : django.db.models.CharField
        A subject for the campaign.
    body : django.db.models.TextField
        A template for the message.

    """
    subject = models.CharField(max_length=255)
    body = models.TextField()

    class Meta:
        abstract = True
        verbose_name = 'template'


class CampaignTemplate(BaseCampaignTemplate):
    """ Contents of a campaign template.

    Attributes
    ----------
    name : django.db.models.CharField
        An internal name to identify this campaign.

    """
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.refresh_template_cache()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.refresh_template_cache()

    def refresh_template_cache(self):
        """ Refresh templates in memory.

        """
        self.subject_template = Template(self.subject)
        self.body_template = Template(self.body)


class BaseCampaign(models.Model):
    """ A campaign configuration.

    Attributes
    ----------
    template : campaigns.CampaignTemplate
        A template associated with this campaign.
    when : django.db.models.DateTimeField, optional
        When does this campaign start?
    until : django.db.models.DateTimeField
        When does this campaign end?

    Notes
    -----
    A campaign is considered inactive if `when` is unset or in the future
    or if `until` is past.

    """
    template = models.ForeignKey(CampaignTemplate)
    when = models.DateTimeField("campaign start", blank=True, null=True,
        help_text='If field is unset, this campaign will be disabled.')  # noqa
    until = models.DateTimeField("campaign end", blank=True, null=True)

    class Meta:
        abstract = True
        verbose_name = 'campaign'

    def active(self):
        if self.when and self.when <= timezone.now():
            if not self.until or self.until >= timezone.now():
                return True
        return False
    active.boolean = True

    def _blast(self, context=None):
        """ Must override.

        Parameters
        ----------
        context : dict, optional
            A dictionary to turn into context variables for the message.

        Raises
        ------
        NotImplementedError
            If this method is not overridden.

        """
        return NotImplementedError

    def blast(self, context=None, force=False):
        """ Send a blast to this campaign.

        Parameters
        ----------
        context : dict, optional
            A dictionary to turn into context variables for the message.
        force : bool, optional
            `True` to notify subscribers who have already been notified,
            `False` otherwise.  Default `False`.

        """
        if self.active():
            self._blast(context=context)


class Campaign(BaseCampaign):
    """ Concrete campaign class.

    Attributes
    ----------
    name : django.db.models.CharField
        An internal name to identify this campaign.

    """
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def opens(self):
        """ How many opens has this campaign accumulated? """
        return self.subscribers.objects.aggregate(sum=models.Sum('clicks')).sum

    def opened(self):
        """ How many subscribers have opened their messages? """
        return self.subscribers.objects.filter(opens__gt=0).count()

    def clicks(self):
        """ How many click-throughs has this campaign accumulated? """
        return self.subscribers.objects.aggregate(sum=models.Sum('clicks')).sum

    def clicked(self):
        """ How many subscribers have clicked through their messages? """
        return self.subscribers.objects.filter(clicks__gt=0).count()

    # def unsubscribes(self):
    #     """ How many unsubscribes has this campaign accumulated? """
    #     return self.subscribers.objects.aggregate(models.Sum('unsubscribes'))

    # def unsubscribed(self):
    #     """ How many subscribers have unsubscribed from their messages? """
    #     return self.subscribers.objects.filter(unsubscribes__gt=0).count()

    def _blast(self, context=None, force=False):
        """ Send a blast to this campaign if it is active.

        Parameters
        ----------
        context : dict, optional
            A dictionary to turn into context variables for the message.
        force : bool, optional
            `True` to notify subscribers who have already been notified,
            `False` otherwise.  Default `False`.

        """
        subscribers = self.subscribers.all()
        if not force:
            subscribers = subscribers.filter(notified__isnull=True)

        if subscribers:
            self._send(subscribers)

    def _message(self, recipient, connection, context=None):
        """ Build and send a single message from a campaign.

        Parameters
        ----------
        recipient : str
            An e-mail address (and optional name) to which to send.
        connection : django.core.mail.backends.console.EmailBackend
            A connection with which to send the message.
        context : dict, optional
            A dictionary to turn into context variables for the message.

        """
        context = Context(context)

        subject = self.template.subject_template.render(context)
        body = self.template.body_template.render(context)

        return utils.make_email_message(subject, body, CAMPAIGN_FROM_EMAIL,
                                        recipient, connection)

    def _send(self, recipients, context=None):
        """ Build and send a blast.

        Parameters
        ----------
        context : dict, optional
            A dictionary to turn into context variables for the message.

        """
        connection = get_connection()
        connection.open()
        for recipient in recipients:
            msg_context = context.copy() if context else {}
            msg_context.update(recipient=recipient)
            message = self._message(recipient.user.email,
                                    connection,
                                    msg_context)
            try:
                message.send()
            except smtplib.SMTPException:
                raise
            else:
                recipient.mark_notified()
        connection.close()
