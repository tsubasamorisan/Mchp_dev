from django.conf import settings
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.core.mail import EmailMultiAlternatives, get_connection

from allauth.account.models import EmailAddress

import random

def random_mix(seq_a, seq_b):
    iters = [iter(seq_a), iter(seq_b)]
    lens = [len(seq_a), len(seq_b)]
    while all(lens):
        r = random.randrange(sum(lens))
        itindex = r < lens[0]
        it = iters[itindex]
        lens[itindex] -= 1
        yield next(it)
    for it in iters:
        for x in it: yield x
        iters = [iter(seq_a), iter(seq_b)]

def render_email(template_prefix, address, context):
    """
    template prefix example: 'lib/email/account_message'
    it is expected that both a .txt and .html version exist
    A subject template can also be provided.
    """
    try:
        subject_template_name = "{}_subject.txt".format(template_prefix)
        subject = render_to_string(subject_template_name, context)
    except TemplateDoesNotExist:
        subject = ''
    # remove line breaks
    subject = " ".join(subject.splitlines()).strip()

    bodies = {}
    for ext in ['html', 'txt']:
        try:
            template_name = '{0}.{1}'.format(template_prefix, ext)
            bodies[ext] = render_to_string(template_name, context).strip()
        except TemplateDoesNotExist:
            raise Exception("Emails must have plain text and html versions.")
    email = EmailMultiAlternatives(
        subject,
        bodies['txt'],
        settings.DEFAULT_FROM_EMAIL,
        [address]
    )
    email.attach_alternative(bodies['html'], 'text/html')
    print(email)
    return email

def send_email_for(email_template, context, users):
    emails = []
    for user in users:
        address = EmailAddress.objects.filter(
            user=user,
            primary=True,
        )
        if address.exists():
            address = address[0].email
        else:
            continue
        email = render_email(email_template, address, context)
        emails.append(email)
    connection = get_connection()
    connection.send_messages(emails)

