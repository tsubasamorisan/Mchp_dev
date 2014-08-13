from django.contrib import messages
from django.core import serializers
from django.core.urlresolvers import reverse
from django.db import IntegrityError
# from django.db.models import Count
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect#, get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView,View, UpdateView

from calendar_mchp.models import ClassCalendar, CalendarEvent 
from calendar_mchp.exceptions import TimeOrderError
from lib.decorators import school_required
from schedule.models import Course, Section
from schedule.utils import WEEK_DAYS

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
        courses = self.student.courses.exclude(
            id__in = self.student.calendars.all().values('course__pk')
        )
        calendars = ClassCalendar.objects.filter(
            owner = self.student,
        )
        print(calendars)
        data = {
            'calendars': calendars,
            'courses': courses,
        }
        return render(request, self.template_name, data)

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return redirect(reverse('calendar'))
        # were just going to forgo any fancy django form saving for this one
        cal_type = request.POST.get('cal-type', '')

        if cal_type.lower() == 'class':
            # this is a sellable calendar
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
            # now add the times as recurring events
            return self._make_sections(request.POST.get('times', {}), calendar)
        elif cal_type.lower() == 'personal':
            # this is a personal calendar, which we don't have yet
            return self.send_ajax_error_message("We don't do those yet.", status=501)
        else: 
            # this wasn't anything
            return self.send_ajax_error_message("Im not sure what calendar you wanted", status=403)

        return redirect(reverse('calendar_create'))

    def _make_calendar(self, request):
        course = Course.objects.filter(
            pk=request.POST.get('course', ''),
            student=self.student,
        )
        if not course.exists():
            # you can only create a calendar for a course you're enrolled in
            return self.send_ajax_error_message('You are not enrolled in that class', status=403)
        else:
            # course found
            course = course[0]

        end_date = timezone.make_aware(datetime.strptime(
            request.POST.get('enddate', ''), "%m/%d/%Y"),
            timezone.utc)
        calendar_data = {
            'course': course,
            'owner': self.student,
            'description': request.POST.get('description', ''),
            'end_date': end_date,
            'private': request.POST.get('private', True),
            'color': request.POST.get('color', '#FFFFFF')
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

    @method_decorator(school_required)
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
                section = Section.objects.filter(
                    student=self.student,
                    course=cal.course,
                )
                cal.delete()
                # also delete the section that got made w/ this calendar
                if section.exists():
                    section = section[0]
                    section.delete()

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

    @method_decorator(school_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(CalendarDeleteView, self).dispatch(*args, **kwargs)

calendar_delete = CalendarDeleteView.as_view()

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
        send_event = None
        for index in events:
            event = events[index]
            all_day = False
            date = event['date']

            # most things don't let you submit a time yet
            if event['hasTime']:
                start = datetime.strptime(date, DATE_FORMAT)
                start = timezone.make_aware(start, timezone.utc)
                end = start + timedelta(hours=1)
            else:
                date = datetime.strptime(date, DATE_FORMAT)
                start, end = self._get_class_time(calendar, date)

            # add the event
            event_data = {
                'calendar': calendar,
                'title': event['title'],
                'description': event['description'],
                'start': start,
                'end': end,
                'all_day': all_day
            }
            cal_event = CalendarEvent(**event_data)
            cal_event.save()
            send_event = cal_event

        if self.request.is_ajax():
            messages.success(
                self.request,
                "Event added"
            )
            data = {
                'messages': self.ajax_messages(),
                'event': serializers.serialize("json", (send_event,))
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
            end = datetime.combine(start, section.end_time)
            end = timezone.make_aware(
                end,
                timezone.utc
            )
        else:
            start_time = timezone.make_aware(date, timezone.get_current_timezone())
            start = timezone.localtime(start_time, timezone=timezone.utc)
            print(start)
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
            )
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
        data = {
            'calendars': calendars,
            'selected_calendar': selected_calendar,
        }
        return render(request, self.template_name, data)

    @method_decorator(school_required)
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
            print(request.POST)
            event = CalendarEvent.objects.filter(
                calendar__owner=self.student,
                id = request.POST.get('pk', None)
            )
            if event.exists():
                event = event[0]

                update = request.POST.get('name', '')
                if update == 'date':
                    start = request.POST.get('value', '')
                    start = timezone.make_aware(start, timezone.get_current_timezone())
                    start = timezone.localtime(start, timezone=timezone.utc)
                    end = start + timedelta(hours=1)
                    setattr(event, 'start', start)
                    setattr(event, 'end', end)

                if update == 'title':
                    description = request.POST.get('value', '')
                    setattr(event, 'title', description)

                if update == 'description':
                    description = request.POST.get('value', '')
                    setattr(event, 'description', description)
                if update == 'class':
                    print(request.POST.get('value', 'fuck'))
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
                event.save()
                print(event.description)
                response = "Event updated"
                status=200
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

    @method_decorator(school_required)
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
                id = request.POST.get('id', None)
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

    @method_decorator(school_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(EventDeleteView, self).dispatch(*args, **kwargs)

event_delete = EventDeleteView.as_view()

'''
url: /calendar/preview/<uuid>
name: calendar_preview
'''
class CalendarPreview(DetailView):
    template_name = 'calendar_mchp/calendar_preview.html'
    model = ClassCalendar

    def get(self, request, *args, **kwargs):
        data = {

        }
        return render(request, self.template_name, data)
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
        )
        courses = ClassCalendar.objects.filter(
            owner = self.student,
        ).values('course__pk', 'course__dept', 'course__course_number')
        data = {
            'flags': self.student.one_time_flag.default(self.student),
            'courses': courses,
            'owned_calendars': owned_calendars,
        }
        return render(request, self.template_name, data)

    @method_decorator(school_required)
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

                update = request.POST.get('name', '')
                if update == 'description':
                    description = request.POST.get('value', '')
                    setattr(calendar, 'description', description)

                if update == 'private':
                    private = int(request.POST.get('value', 1))
                    if private  == 1:
                        setattr(calendar, 'private', False)
                    elif private == 2:
                        setattr(calendar, 'private', True)

                if update == 'price':
                    price = request.POST.get('value', 0)
                    try:
                        price = int(price)
                        setattr(calendar, 'price', price)
                    except:
                        response = "That's not a price that you can sell something for"
                        status=400
                        data = {
                            'response': response,
                        }
                        return self.render_to_json_response(data, status=status)

                calendar.save()
                response = "Calendar updated"
                status=200
            else:
                response = "We couldn't find that calendar"
                status=403
            data = {
                'response': response,
            }
            return self.render_to_json_response(data, status=status)
        else:
            return redirect(reverse('calendar'))

    @method_decorator(school_required)
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
                is_recurring=False,
            ).values('id', 'title', 'description', 'start', 'end', 'all_day', 'url',
                     'calendar__course__name', 'calendar__color', 'calendar__course__pk',
                     'calendar__pk'
            ).order_by('start')

            # convert the returned events to a format we can use on the page
            for event in events:
                start_time = timezone.localtime(event['start'], timezone=timezone.get_current_timezone())
                end_time = timezone.localtime(event['end'], timezone=timezone.get_current_timezone())

                event['start'] = start_time.strftime(DATE_FORMAT)
                event['end'] = end_time.strftime(DATE_FORMAT)
                event['allDay'] = event['all_day']
                event['course'] = event['calendar__course__name']
                del event['calendar__course__name']
                del event['all_day']

            data = {
                'events': list(events),
            }
            return self.render_to_json_response(data, status=200)
        else:
            return redirect(reverse('calendar'))

    @method_decorator(school_required)
    def dispatch(self, *args, **kwargs):
        self.student = self.request.user.student
        return super(CalendarFeed, self).dispatch(*args, **kwargs)

calendar_feed = CalendarFeed.as_view()
