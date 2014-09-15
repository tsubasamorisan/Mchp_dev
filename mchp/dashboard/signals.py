from django.dispatch.dispatcher import receiver

from calendar_mchp.signals import calendar_event_created,subscription
from user_profile.signals import enrolled
from documents.signals import document_uploaded, document_purchased

from dashboard.models import DashEvent
from dashboard.utils import DASH_EVENTS

@receiver(calendar_event_created)
def add_event(sender, **kwargs):
    event = kwargs['event']

    calendar = event.calendar
    if calendar.private:
        return
    followers = calendar.subscribers.all()
    data = {
        'type': DASH_EVENTS.index('calendar add'),
        'calendar': calendar,
        'course': calendar.course,
        'student': calendar.owner,
        'event': event, 
    }
    dash_item = DashEvent(**data)
    dash_item.event = event
    dash_item.save()
    for student in followers:
        dash_item.followers.add(student)

@receiver(subscription)
def add_subscription_notice(sender, **kwargs):
    subscription = kwargs['subscription']
    calendar = subscription.calendar    
    subscriber = subscription.student
    owner = calendar.owner
    data = {
        'type': DASH_EVENTS.index('subscription'),
        'calendar': calendar,
        'course': calendar.course,
        'student': subscriber,
    }
    dash_item = DashEvent(**data)
    dash_item.save()
    dash_item.followers.add(owner)
    print(dash_item)

@receiver(enrolled)
def add_class_join(sender, **kwargs):
    enroll = kwargs['enroll']

    # first, send the fact that they joined to everyone already enrolled
    followers = enroll.course.student_set.exclude(
        pk=enroll.student.pk
    )
    data = {
        'type': DASH_EVENTS.index('other class join'),
        'course': enroll.course,
        'student': enroll.student,
    }
    dash_item = DashEvent(**data)
    dash_item.save()
    for student in followers:
        dash_item.followers.add(student)
    # now give them their own dash item
    data = {
        'type': DASH_EVENTS.index('class join'),
        'course': enroll.course,
        'student': enroll.student,
    }
    dash_item = DashEvent(**data)
    dash_item.save()
    # only the student who just enrolled is intrested in knowing they just enrolled themselves
    dash_item.followers.add(enroll.student)

@receiver(document_purchased)
def add_document_purchase(sender, **kwargs):
    purchase = kwargs['purchase']
    # this doc has no uploader, so don't inform anyone
    if not purchase.document.upload:
        return

    data = {
        'type': DASH_EVENTS.index('document purchase'),
        'document': purchase.document,
        'course': purchase.document.course,
        'student': purchase.student,
    }
    dash_item = DashEvent(**data)
    dash_item.save()
    dash_item.followers.add(purchase.document.upload.owner)


@receiver(document_uploaded)
def add_document_upload(sender, **kwargs):
    upload = kwargs['upload']

    followers = upload.document.course.student_set.all()
    data = {
        'type': DASH_EVENTS.index('document add'),
        'document': upload.document,
        'course': upload.document.course,
        'student': upload.owner,
    }
    dash_item = DashEvent(**data)
    dash_item.save()
    for student in followers:
        dash_item.followers.add(student)
