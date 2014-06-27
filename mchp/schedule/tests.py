from django.test import TestCase
from django.db.utils import IntegrityError
from django.db.transaction import atomic
from schedule.models import School, Course

class SchoolTestCase(TestCase):

    def setUp(self):
        test_uni = {
            'domain': "www.test.edu", 
            'name': "Test University", 
            'phone_number':"(520) 555-5555",
            'street': "413 n What st.", 
            'city':"Test city",
            'state': 'AZ',
            'country': 'USA',
        }
        self.school = School(**test_uni)
        self.school.save()

    def testCourseUnique(self):
        data = {
            'domain': self.school,
            'dept': 'CSC',
            'course_number': '245',
            'professor': 'mccann',
        }
        c = Course(**data)
        c.save()
        other = Course(**data)
        with atomic():
            self.assertRaises(IntegrityError, other.save)

    def testEDUValidation(self):
        from django.forms import ModelForm

        class TestForm(ModelForm):
            class Meta:
                model = School
                fields = '__all__'

        post = { 
            'domain': "www.google.com", 
            'name': "Test University", 
            'phone_number':"(520) 555-5555",
            'street': "413 n What st.", 
            'city':"Test city"
        }
        test_school = School()
        test_school_form = TestForm(instance=test_school)
        self.assertEqual(test_school_form.is_valid(), False)
        test_school_form = TestForm(post, instance=test_school)
        self.assertEqual(test_school_form.is_valid(), False)

        post['domain'] = 'www.test.edu'
        test_school = School()
        test_school_form = TestForm(post, instance=test_school)
        self.assertEqual(test_school_form.is_valid(), True)

        test_school.save(force_insert=True)
        other_school = School(domain='http://www.test.edu/', name='other')
        # otherwise transaction errors occur, only happens with unittests
        with atomic():
            self.assertRaises(IntegrityError, other_school.save, force_insert=True)

