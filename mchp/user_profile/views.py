from django.shortcuts import redirect,render, get_object_or_404
from django.template import Context
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.generic.detail import DetailView
from django.views.generic.edit import View
from django.http import HttpResponse, HttpResponseGone
from django.utils.decorators import method_decorator
# from django.db.models import Count

from allauth.account.decorators import verified_email_required
from allauth.account.models import EmailAddress
from allauth.account.adapter import get_adapter

from schedule.models import School
from user_profile.models import Student, UserProfile
from lib.decorators import school_required

import json
import logging
logger = logging.getLogger(__name__)

'''
url: /profile/<number>/slug
url: /profile/<number>
url: /profile/
name: profile
name: my_profile
'''
class ProfileView(DetailView):
    template_name = 'user_profile/profile.html'
    model = Student

    def get_object(self):
        if 'number' in self.kwargs:
            # url: /profile/<number>/
            return get_object_or_404(self.model, id=self.kwargs['number'])
        else:
            # url: /profile/ (logged in users account)
            return get_object_or_404(self.model, user=self.request.user)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context['profile'] = self.object.profile
        return context

    @method_decorator(school_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileView, self).dispatch(*args, **kwargs)

profile = ProfileView.as_view()

'''
url: /accounts/settings/
name: account_settings
'''
class AccountSettingsView(View):
    template_name = 'user_profile/account_settings.html'

    def get(self, request, *args, **kwargs):
        data = {

        }
        return render(request, self.template_name, data)

account_settings = AccountSettingsView.as_view()

# FIXME: wow this is bad
# this should at least be a form view
@verified_email_required
def confirm_school(request):
    if request.method == 'POST':
        if 'school' in request.POST:
            logger.debug(request)
            school = request.POST['school']
            school = School.objects.get(domain=school)
            logger.debug(school)
            student, created = Student.objects.get_or_create(
                user=request.user, school=school
            )
            logger.debug(student)
            if not created:
                student.save()
                profile = UserProfile(student=student)
                profile.save()

            if 'next' in request.POST and request.POST['next'] != '':
                return redirect(request.POST['next'])
            else:
                return redirect('/school/course/add/')

    schools = School.objects.all().values('name', 'domain').order_by('name')
    if 'next' in request.GET:
        next_page = request.GET['next']
        data = {'schools': schools, 'next': next_page}
    else:
        data = {'schools': schools}
    return render(request, 'user_profile/school.html', Context(data))

@require_POST
def get_email(request):
    email = request.POST["email"]
    if request.is_ajax():
        if 'initial_email' in request.session:
            return HttpResponseGone(json.dumps({'message': 'initial_email already set'}), content_type='application/javascript')
        else:
            request.session['initial_email'] = email
            return HttpResponse(json.dumps({}), content_type='application/javascript')
    else:
        request.session['initial_email'] = email
        return redirect('/accounts/signup')

@require_POST
def resend_email(request):
    if request.is_ajax():
        email = request.POST["email"]
        try:
            email_address = EmailAddress.objects.get(email=email)
            get_adapter().add_message(request,
                                      messages.INFO,
                                      'account/messages/'
                                      'email_confirmation_sent.txt',
                                      {'email': email})
            email_address.send_confirmation(request)
        except EmailAddress.DoesNotExist:
            return HttpResponseGone(json.dumps({}), content_type='application/javascript')
        return HttpResponse(json.dumps({}), content_type='application/javascript')
    else:
        return redirect('/')
