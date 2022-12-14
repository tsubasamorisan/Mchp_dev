import copy
import re
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView,View, UpdateView

from calendar_mchp.models import ClassCalendar, CalendarEvent, Subscription
from calendar_mchp.exceptions import TimeOrderError, CalendarExpiredError, BringingUpThePastError
from documents.models import Document
from notification.api import add_notification_for, add_notification
from lib.decorators import class_required
from referral.models import ReferralCode
from schedule.models import Enrollment, Section, Course
from schedule.utils import WEEK_DAYS
from user_profile.models import OneTimeFlag

from datetime import datetime,timedelta
import json
import logging
logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ" 

class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.

    I stole this right from the django website.
    """
    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def ajax_messages(self):
        django_messages = []

        for message in messages.get_messages(self.request):
            django_messages.append({
                "level": message.level,
                "message": message.message,
                "extra_tags": message.tags,
            })
        return django_messages

    def send_ajax_error_message(self, message, **kwargs):
        messages.error(
            self.request,
            message,
        )
        data = {
            'messages': self.ajax_messages(),
        }
        status = kwargs.get('status', 500)
        return self.render_to_json_response(data, status=status)

'''
url: /calendar/create/
name: calendar_create
'''
class CalendarCreateView(View, AjaxableResponseMixin):
    template_name = 'calendar_mchp/calendar_create.html'

    def get_success_url(self):
        return reverse('calendar')

    def get(self, request, *args, **kwargs):
        courses = self.student.courses()
        course_pks = self.student.calendars.all().values('course__pk')
        # [{'course__pk': 8}, {'course__pk': 88}, ...] -> [8, 88]
        course_pks = [course['course__pk'] for course in course_pks]
        # filter out courses w/ calendars already made
        courses = [course for course in courses if course.pk not in course_pks]

        calendars = ClassCalendar.objects.filter(
            owner = self.student,
        )
        data = {
            'calendars': calendars,
            'courses': courses,
        }
        return render(request, self.template_name, data)

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return redirect(reverse('calendar'))
        # were just going to forgo any fancy django form saving for this one
        calendar = self._make_calendar(request)
        try:
            calendar.save()
        except (IntegrityError, TimeOrderError) as err:
            # they made a calendar for this class
            if err.__class__ == IntegrityError:
                return self.send_ajax_error_message('You have already made a calendar for that course', status=403)
            else:
                # the start date was too early
                return self.send_ajax_error_message(str(err), status=403)
        # now add the times as sections
        return self._make_sections(request.POST.get('times', {}), calendar)

    def _make_calendar(self, request):
        enroll = Enrollment.objects.filter(
            student = self.student,
            course__pk=request.POST.get('course', -1)
        )
        if not enroll.exists():
            # you can only create a calendar for a course you're enrolled in
            return self.send_ajax_error_message('You are not enrolled in that class', status=403)
        else:
            # course found
            course = enroll[0].course

        calendar_data = {
            'course': course,
            'owner': self.student,
            'description': request.POST.get('description', ''),
            'private': True,
            'color': request.POST.get('color', '#FFFFFF'),
        }
        return ClassCalendar(**calendar_data)
    
    def _make_sections(self, times, calendar):
        times = json.loads(times)
        for day in times:
            start_time = timezone.make_aware(datetime.strptime(
                times[day]['start'], DATE_FORMAT),
                timezone.get_current_timezone())
            start_time = timezone.localtime(start_time, timezone=timezone.utc)
            end_time = timezone.make_aware(datetime.strptime(
                times[day]['end'], DATE_FORMAT),
                timezone.get_current_timezone())
            end_time = timezone.localtime(end_time, timezone=timezone.utc)
            section_data = {
                'course': calendar.course,
                'student': self.student,

                'day': WEEK_DAYS.index(day),
                'start_time': start_time,
                'end_time': end_time,
            }
            section = Section(**section_data)
            # TODO error handling
            section.save()
        data = {
            'calendar': calendar.pk,
        }
        return self.render_to_json_response(data, status=200)

    @method_decorator(class_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(CalendarCreateView, self).dispatch(*args, **kwargs)

calendar_create = CalendarCreateView.as_view()

'''
url: /calendar/delete/
name: calendar_delete
'''
class CalendarDeleteView(DeleteView, AjaxableResponseMixin):
    model = ClassCalendar

    def post(self, request, *args, **kwargs):
        if self.request.is_ajax():
            cal = ClassCalendar.objects.filter(
                owner=self.student,
                pk = request.POST.get('id', None)
            )
            if cal.exists(): 
                cal = cal[0]
                cal.delete()
                # also delete the section that got made w/ this calendar
                Section.objects.filter(
                    student=self.student,
                    course=cal.course,
                ).delete()
                # clear out any subscriptions and let people know
                subs = Subscription.objects.filter(
                    calendar=cal
                )
                subscribers = list(map(lambda sub: sub.student.user, subs))
                add_notification_for(
                    subscribers,
                    '{} has deleted a calendar for {}'.format(request.user.username, cal.course)
                )
                subs.delete()

                messages.success(
                    self.request,
                    "Calendar deleted"
                )
                status = 200
            else:
                messages.error(
                    self.request,
                    "Is that really your calendar?"
                )
                status = 403
            data = {
                'messages': self.ajax_messages(),
            }
            return self.render_to_json_response(data, status=status)
        else:
            return redirect(reverse('calendar'))

    def get(self, request, *args, **kwargs):
        return redirect(reverse('calendar'))

    @method_decorator(class_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(CalendarDeleteView, self).dispatch(*args, **kwargs)

calendar_delete = CalendarDeleteView.as_view()

'''
url: /calendar/unsubscribe/
name: calendar_unsubscribe
'''
class CalendarUnsubscribeView(View, AjaxableResponseMixin):
    model = Subscription

    def post(self, request, *args, **kwargs):
        if self.request.is_ajax():
            sub = Subscription.objects.filter(
                student=self.student,
                calendar = request.POST.get('pk', None)
            )
            if sub.exists(): 
                sub = sub[0]
                sub.delete()
                messages.success(
                    self.request,
                    "Say \"Adi??s\" to that calendar subscription..."
                )
                status = 200
            else:
                messages.error(
                    self.request,
                    "You don't have a subscription to that calendar; neither does it have a subscription to you"
                )
                status = 403
            data = {
                'messages': self.ajax_messages(),
            }
            return self.render_to_json_response(data, status=status)
        else:
            return redirect(reverse('calendar'))

    def get(self, request, *args, **kwargs):
        return redirect(reverse('calendar'))

    @method_decorator(class_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(CalendarUnsubscribeView, self).dispatch(*args, **kwargs)

calendar_unsubscribe = CalendarUnsubscribeView.as_view()

'''
url: /calendar/events/add/
name: event_add
'''
class EventAddView(View, AjaxableResponseMixin):
    template_name = 'calendar_mchp/event_add.html'
    model = CalendarEvent

    def post(self, request, *args, **kwargs):
        calendar = ClassCalendar.objects.filter(
            pk=request.POST.get('calendar', ''),
            owner=self.student
        )
        if not calendar.exists():
            return
        else:
            calendar = calendar[0]

        events = request.POST.get('events', '[]')
        events = json.loads(events)
        error = False
        created_events= []
        for index in events:
            event = events[index]
            all_day = False
            date = event['date']

            # most things don't let you submit a time yet
            if event['hasTime']:
                start = datetime.strptime(date, DATE_FORMAT)
                start = timezone.make_aware(start, timezone.get_current_timezone())
                end = start + timedelta(hours=1)
            else:
                date = datetime.strptime(date, DATE_FORMAT)
                start, end = self._get_class_time(calendar, date)

            # add the event
            event_data = {
                'calendar': calendar,
                'title': event['title'][:30],
                'description': event['description'][:200],
                'start': start,
                'end': end,
                'all_day': all_day,
                'last_edit': timezone.now(),
            }
            cal_event = CalendarEvent(**event_data)
            try:
                cal_event.save()
                created_events.append(cal_event)
            except ( CalendarExpiredError, BringingUpThePastError ) as e:
                messages.error(
                    self.request,
                    str(e)
                )
                error = True
        if not error:
            messages.success(
                self.request,
                "Your events have been updated"
            )
            # send a notification to everyone that an event has been added
            subscribers = list(map(lambda sub: sub.student.user, Subscription.objects.filter(
                calendar=calendar,
                calendar__private=False,
            )))
            add_notification_for(
                subscribers,
                '{} has added an event to {}'.format(request.user.username, calendar.course)
            )

            # Propagate created events to student calenders
            student_calendars = ClassCalendar.objects.filter(original_calendar=calendar)
            student_events = []
            for original_event in created_events:
                for student_calendar in student_calendars:
                    event = copy.copy(original_event)
                    event.pk = None
                    event.id = None
                    event.calendar = student_calendar
                    event.original_event = original_event
                    student_events.append(event)

            CalendarEvent.objects.bulk_create(student_events)

        if self.request.is_ajax():
            data = {
                'messages': self.ajax_messages(),
            }
            return self.render_to_json_response(data, status=200)
        else:
            return redirect(reverse('calendar'))

    def _get_class_time(self, calendar, date):
        section = Section.objects.filter(
            course=calendar.course,
            day = date.weekday()
        )
        if section.exists():
            section = section[0]
            start = datetime.combine(date, section.start_time)
            start = timezone.make_aware(
                start,
                timezone.utc
            )
            # this little dance is because of the way section store times but not dates in utc,
            # so if the time is late enough in the day, it would suddenly be on the wrong day
            # because of the conversion, thus we transform the time and then reapply the day.
            start = timezone.localtime(start, timezone.get_current_timezone()).time()
            start = datetime.combine(date, start)
            start = timezone.make_aware(
                start,
                timezone.get_current_timezone()
            )
            # ultimately the event ends up being in utc time on the correct day
            start = timezone.localtime(start, timezone.utc)
            # skip the same dance for the end time, and just set it to be in an hour
            end = start + timedelta(hours=1)
        else:
            start_time = timezone.make_aware(date, timezone.get_current_timezone())
            start = timezone.localtime(start_time, timezone=timezone.utc)
            start = start + timedelta(hours=8) # set default to 8am
            end = start + timedelta(hours=1)
        return (start, end)

    def get(self, request, *args, **kwargs):
        calendars = ClassCalendar.objects.filter(
            owner = self.student
        )
        for calendar in calendars:
            sections = Section.objects.filter(
                course=calendar.course,
                student=self.student,
            ).order_by('day')
            calendar.end_date = timezone.make_naive(calendar.end_date, timezone.utc)
            for section in sections:
                day_name = WEEK_DAYS[section.day]
                start_date = datetime.combine(datetime.today(), section.start_time)
                end_date = datetime.combine(datetime.today(), section.end_time)

                start_time = timezone.make_aware(start_date, timezone.utc)
                end_time = timezone.make_aware(end_date, timezone.utc)
                start_time = timezone.localtime(start_time, timezone=timezone.get_current_timezone())
                end_time = timezone.localtime(end_time, timezone=timezone.get_current_timezone())
                section.day_name = day_name
                section.start = start_time
                section.end = end_time

            setattr(calendar, 'sections', sections)
        selected_calendar = request.GET.get('calendar', '')
        event_flag = 'events tutorial'
        data = {
            'calendars': calendars,
            'selected_calendar': selected_calendar,
            'events_tutorial': self.student.one_time_flag.get_flag(self.student, event_flag),
            'events_tutorial_name': event_flag, 
        }
        return render(request, self.template_name, data)

    @method_decorator(class_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(EventAddView, self).dispatch(*args, **kwargs)

event_add = EventAddView.as_view()

'''
url: /calendar/events/update/
name: event_update
'''
class EventUpdateView(UpdateView, AjaxableResponseMixin):
    model = CalendarEvent

    def post(self, request, *args, **kwargs):
        if self.request.is_ajax():
            event = CalendarEvent.objects.filter(
                calendar__owner=self.student,
                id = request.POST.get('pk', None)
            )
            if event.exists():
                event = event[0]

                date = request.POST.get('date', None)
                if date:
                    start = timezone.make_aware(datetime.strptime(
                        json.loads(date), DATE_FORMAT),
                        timezone.get_current_timezone())
                    start = timezone.localtime(start, timezone=timezone.utc)
                    end = start + timedelta(hours=1)
                    setattr(event, 'start', start)
                    setattr(event, 'end', end)

                update = request.POST.get('name', '')
                if update == 'title':
                    description = request.POST.get('value', '')[:30]
                    setattr(event, 'title', description)

                if update == 'description':
                    description = request.POST.get('value', '')[:200]
                    setattr(event, 'description', description)
                if update == 'class':
                    calendar = ClassCalendar.objects.filter(
                        owner = self.student,
                        course__pk = request.POST.get('value', -1)
                    )
                    if calendar.exists():
                        calendar = calendar[0]
                        event.calendar = calendar
                    else:
                        response = "We couldn't find a calendar for that class"
                        status=403
                        data = {
                            'response': response,
                        }
                        return self.render_to_json_response(data, status=status)
                try:
                    event.save()
                    response = "Event updated"
                    status=200
                    # send a notification to everyone that this calendar event has been updated
                    subscribers = list(map(lambda sub: sub.student.user, Subscription.objects.filter(
                        calendar=event.calendar
                    )))
                    add_notification_for(
                        subscribers,
                        '{} has updated event: {} in {}'.format(request.user.username, event.title, event.calendar.course)
                    )
                except (CalendarExpiredError, BringingUpThePastError) as e:
                    status=403
                    data = {
                        'response': str(e),
                    }
                    return self.render_to_json_response(data, status=status)
            else:
                response = "Event not found"
                status=403
            data = {
                'response': response,
            }
            return self.render_to_json_response(data, status=status)
        else:
            return redirect(reverse('calendar'))

    def get(self, request, *args, **kwargs):
        return redirect(reverse('calendar'))

    @method_decorator(class_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(EventUpdateView, self).dispatch(*args, **kwargs)

event_update = EventUpdateView.as_view()

'''
url: /calendar/events/delete/
name: event_delete
'''
class EventDeleteView(DeleteView, AjaxableResponseMixin):
    model = CalendarEvent

    def post(self, request, *args, **kwargs):
        if self.request.is_ajax():
            event = CalendarEvent.objects.filter(
                calendar__owner=self.student,
                id = request.POST.get('pk', None)
            )
            if event.exists():
                event = event[0]
                event.delete()

                messages.success(
                    self.request,
                    "Event deleted"
                )
            else:
                messages.error(
                    self.request,
                    "Event not found"
                )
            data = {
                'messages': self.ajax_messages(),
            }
            return self.render_to_json_response(data, status=200)
        else:
            return redirect(reverse('calendar'))

    def get(self, request, *args, **kwargs):
        return redirect(reverse('calendar'))

    @method_decorator(class_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(EventDeleteView, self).dispatch(*args, **kwargs)

event_delete = EventDeleteView.as_view()

'''
url: /calendar/preview/<pk>
name: calendar_preview
'''
class CalendarPreview(DetailView):
    template_name = 'calendar_mchp/calendar_preview.html'
    model = ClassCalendar

    def post(self,request, *args, **kwargs):
        if not self.student:
            return redirect(reverse('landing_page'))
        calendar = get_object_or_404(self.model, pk=self.kwargs['pk'], private=False)

        if calendar.owner == self.student:
            messages.error(
                request,
                "We know it's good, but you can't subscribe to your own calendar!"
            )
            return self.get(request, *args, **kwargs)

        subscription, created = Subscription.objects.get_or_create(
            student=self.student,
            calendar=calendar,
        )
        if not created:
            if subscription.enabled:
                messages.warning(
                    request,
                    "Slow down there kiddo, you're already subscribed to that calendar"
                )
        else:
            messages.success(
                request,
                "Your subscription has been noted"
            )
            add_notification(
                calendar.owner.user, 
                '{} has subscribed to your {} calendar'.format(request.user.username, calendar.course)
            )
        return redirect(reverse('calendar'))

    def get(self, request, *args, **kwargs):
        referral_link = ''
        if not request.user.is_anonymous() and request.user.student_exists():
            referral_link = ReferralCode.objects.get_referral_code(request.user).referral_link

        calendar = get_object_or_404(self.model, pk=self.kwargs['pk'], private=False)

        events = CalendarEvent.objects.filter(
            calendar=calendar,
            start__lt=timezone.now(),
        ).order_by('start')[:3]
        count = CalendarEvent.objects.filter(
            calendar=calendar,
            start__lte=timezone.now()
        ).count()
        next_event = CalendarEvent.objects.filter(
            calendar=calendar,
            start__gte=timezone.now()
        ).order_by('start')[:1]
        if next_event.exists():
            next_event = next_event[0]
        else:
            next_event = None
        total_count = CalendarEvent.objects.filter(
            calendar=calendar
        ).count()

        # class meeting times
        sections = Section.objects.filter(
            course=calendar.course,
            student=calendar.owner,
        )
        for section in sections:
            day_name = WEEK_DAYS[section.day]
            start_date = datetime.combine(datetime.today(), section.start_time)
            end_date = datetime.combine(datetime.today(), section.end_time)

            start_time = timezone.make_aware(start_date, timezone.utc)
            end_time = timezone.make_aware(end_date, timezone.utc)
            start_time = timezone.localtime(start_time, timezone=timezone.get_current_timezone())
            end_time = timezone.localtime(end_time, timezone=timezone.get_current_timezone())
            section.day_name = day_name
            section.start = start_time
            section.end = end_time
        setattr(calendar, 'sections', sections)

        cals = ClassCalendar.objects.filter(
            owner=calendar.owner
        ).count()
        docs = Upload.objects.filter(
            owner=calendar.owner
        ).count()
        all_counts = cals + docs
        if all_counts == 0:
            all_counts = 1
        cal_percent = (cals * 100) / all_counts
        doc_percent = (docs * 100) / all_counts

        preview_flag_name = 'calendar preview referral'
        data = {
            'calendar': calendar,
            'owner': calendar.owner,
            'owner_level': round((timezone.now() - calendar.owner.user.date_joined) / timedelta(days=7)),
            'events': events,
            'past_count': count,
            'next_event': next_event,
            'total_count': total_count,
            'referral_link': referral_link,
            'referral_reward': settings.MCHP_PRICING['referral_reward'],
            'current_path': request.get_full_path(),
            'preview_flag': OneTimeFlag.objects.get_flag(self.student, preview_flag_name),
            'preview_flag_name': preview_flag_name ,
            'cal_percent': cal_percent,
            'doc_percent': doc_percent,
        }
        return render(request, self.template_name, data)
    
    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_anonymous() and self.request.user.student_exists():
            self.student = self.request.user.student
        else:
            self.student = None
        return super(CalendarPreview, self).dispatch(*args, **kwargs)

calendar_preview = CalendarPreview.as_view()

'''
url: /calendar/
name: calendar
'''
class CalendarView(View):
    template_name = 'calendar_mchp/calendar.html'

    def get(self, request, *args, **kwargs):
        owned_calendars = ClassCalendar.objects.filter(
            owner=self.student
        ).order_by(
            'private', 'title'
        ).annotate(
            subscriptions=Count('subscribers')
        )
        cal_courses = ClassCalendar.objects.filter(
            owner = self.student,
        ).values('course__pk', 'course__dept', 'course__course_number')
        courses = self.student.courses()

        calendar_tutorial = 'calendar tutorial'
        data = {
            'turtorial_flag': self.student.one_time_flag.get_flag(self.student, calendar_tutorial),
            'turtorial_flag_name': calendar_tutorial, 
            'calendar_courses': cal_courses,
            'courses': courses,
            'owned_calendars': owned_calendars,
            'total_school_calendars': len(owned_calendars)
        }
        return render(request, self.template_name, data)

    @method_decorator(class_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(CalendarView, self).dispatch(*args, **kwargs)

calendar = CalendarView.as_view()

'''
url: /calendar/update/
name: calendar_update
'''
class CalendarUpdateView(View, AjaxableResponseMixin):
    def get(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['POST'])

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            calendar = ClassCalendar.objects.filter(
                owner=self.student,
                id = request.POST.get('pk', None)
            )
            if calendar.exists():
                calendar = calendar[0]

                date = request.POST.get('date', None)
                if date:
                    end_date = timezone.make_aware(datetime.strptime(
                        json.loads(date), DATE_FORMAT),
                        timezone.get_current_timezone())
                    end_date = timezone.localtime(end_date, timezone=timezone.utc)
                    setattr(calendar, 'end_date', end_date)

                update = request.POST.get('name', '')
                if update == 'description':
                    description = request.POST.get('value', '')
                    setattr(calendar, 'description', description)

                changed_privacy = False
                if update == 'private':
                    private = int(request.POST.get('value', 1))
                    if private  == 1:
                        setattr(calendar, 'private', False)
                    elif private == 2:
                        setattr(calendar, 'private', True)
                    changed_privacy = True
                    # notif followers
                    subscribers = list(map(lambda sub: sub.student.user, Subscription.objects.filter(
                        calendar=calendar,
                    )))
                    private = 'private' if calendar.private else 'public'
                    add_notification_for(
                        subscribers,
                        '{} has made their {} calendar {}'.format(request.user.username, calendar.course, private)
                    )

                calendar.save()
                response = "Calendar updated"
                status=200
            else:
                response = "We couldn't find that calendar"
                status=403
            data = {
                'response': response,
                'privacy': changed_privacy,
            }
            return self.render_to_json_response(data, status=status)
        else:
            return redirect(reverse('calendar'))

    @method_decorator(class_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(CalendarUpdateView, self).dispatch(*args, **kwargs)

calendar_update = CalendarUpdateView.as_view()

'''
url: /calendar/feed/
name: calendar_feed
'''
class CalendarFeed(View, AjaxableResponseMixin):

    def post(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['GET'])

    def get(self, request, *args, **kwargs):
        if self.request.is_ajax():
            # get the ranges that full calendar sends in the request
            start = request.GET.get('start', '')
            start = timezone.make_aware(datetime.strptime(
                start, "%Y-%m-%d"),
                timezone.utc
            )
            end = request.GET.get('end', '')
            end = timezone.make_aware(datetime.strptime(
                end, "%Y-%m-%d"),
                timezone.utc
            )
            # event data
            events = CalendarEvent.objects.filter(
                calendar__owner=self.student,
                calendar__end_date__gte=timezone.now(),
                is_recurring=False,
                start__range=(start,end)
            ).order_by('start').values('id', 'title', 'description', 'start', 'end', 'all_day', 'url',
                     'calendar__course__name', 'calendar__color', 'calendar__course__pk',
                     'calendar__pk', 'calendar__private', 'last_edit'
            )

            # convert the returned events to a format we can use on the page
            for event in events:
                start_time = timezone.localtime(event['start'], timezone=timezone.get_current_timezone())
                end_time = timezone.localtime(event['end'], timezone=timezone.get_current_timezone())
                last_edit = timezone.localtime(event['last_edit'], timezone=timezone.utc)

                event['last_edit'] = last_edit.strftime(DATE_FORMAT)
                event['start'] = start_time.strftime(DATE_FORMAT)
                event['end'] = end_time.strftime(DATE_FORMAT)
                event['allDay'] = event['all_day']
                event['course'] = event['calendar__course__name']
                event['owned'] = True

                del event['calendar__course__name']
                del event['all_day']

            data = {
                'events': list(events),
            }
            return self.render_to_json_response(data, status=200)
        else:
            return redirect(reverse('calendar'))

    @method_decorator(class_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(CalendarFeed, self).dispatch(*args, **kwargs)

calendar_feed = CalendarFeed.as_view()

'''
url: /calendar/list/
name: calendar_list
'''
class CalendarListView(View, AjaxableResponseMixin):

    def post(self, request, *args, **kwargs):
        return HttpResponseNotAllowed(['GET'])

    def get(self, request, *args, **kwargs):
        if self.request.is_ajax():
            course = request.GET.get('course', -1)
            calendars = ClassCalendar.objects.filter(
                course=course,
                private=False,
                end_date__gte=timezone.now(),
            ).annotate(
                events=Count('calendarevent__pk'),
            ).order_by(
                'create_date', 'title'
            ).values('title', 'owner', 'events', 'owner__user__username','pk',
                     'description', 'create_date', 'course__professor')
            for calendar in calendars:
                date = timezone.localtime(calendar['create_date'], timezone=timezone.utc)
                calendar['date'] = date.strftime(DATE_FORMAT)
                calendar_instance = ClassCalendar.objects.get(pk=calendar['pk'])
                calendar['subscriptions'] = calendar_instance.subscribers.count()
                sections = Section.objects.filter(
                    course=calendar_instance.course,
                    student__pk=calendar['owner'],
                )
                time_string = ''
                for section in sections:
                    day_name = WEEK_DAYS[section.day]
                    start_date = datetime.combine(datetime.today(), section.start_time)
                    end_date = datetime.combine(datetime.today(), section.end_time)

                    start_time = timezone.make_aware(start_date, timezone.utc)
                    end_time = timezone.make_aware(end_date, timezone.utc)
                    start_time = timezone.localtime(start_time, timezone=timezone.get_current_timezone())
                    end_time = timezone.localtime(end_time, timezone=timezone.get_current_timezone())
                    time_string += day_name[:3] + ' '
                    time_string += start_time.strftime('%I%p').lstrip('0') + '-'
                    time_string += end_time.strftime('%I%p').lstrip('0') + '&nbsp;&nbsp;&nbsp;&nbsp;'
                calendar['time'] = time_string
                del calendar['create_date']

            data = {
                'calendars': list(calendars),
            }
            return self.render_to_json_response(data, status=200)
        else:
            return redirect(reverse('calendar'))

    @method_decorator(class_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(CalendarListView, self).dispatch(*args, **kwargs)

calendar_list = CalendarListView.as_view()


class EventDetailView(DetailView):
    """ Event detail at `/calendar/event/<pk>` with name `event-detail`.

    """
    template_name = 'calendar_mchp/event_detail.html'
    model = CalendarEvent

    def get_context_data(self, **kwargs):
        context = super(EventDetailView, self).get_context_data(**kwargs)
        event = context['calendarevent']
        context['event'] = event
        context['course'] = event.calendar.course
        context['documents'] = event.get_documents()

        if event.calendar and event.calendar.course:
            classmates = Course.objects.get_classlist_for(event.calendar.course)
            context['classmates'] = classmates

        return context

event_detail = EventDetailView.as_view()
