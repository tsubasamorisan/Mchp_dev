from django.db import models
from django.template.defaultfilters import slugify
from django.conf import settings

from documents.exceptions import DuplicateFileError
from schedule.models import School, Course

import hashlib
import uuid
import os.path
import magic

import logging
logger = logging.getLogger(__name__)

DOCUMENT_LOCATION = "documents/"
PREVIEW_LOCATION = "previews/"

def get_sentinel_course():
    school, created = School.objects.get_or_create(domain='deleted.edu', name='deleted')
    course, created = Course.objects.get_or_create(domain=school, 
                                        dept='del', 
                                        course_number=100,
                                        professor='deleted')
    return course

class Document(models.Model):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=1000)
    course = models.ForeignKey('schedule.Course', on_delete=models.SET(get_sentinel_course))

    up = models.IntegerField(default=0)
    down = models.IntegerField(default=0)
    price = models.PositiveIntegerField(default=0)

    document = models.FileField(upload_to=DOCUMENT_LOCATION)
    filetype = models.CharField(max_length=150)
    md5sum = models.CharField(max_length=32)
    uuid = models.CharField(max_length=32)
    create_date = models.DateTimeField(auto_now_add=True)

    preview = models.ImageField(upload_to=PREVIEW_LOCATION, blank=True, null=True)
    slug = models.SlugField(max_length=80)
    
    '''
    Add a bunch of information and check for duplicates before saving

    also, those seeks are absolutely fucking necessary with the s3 stuff
    '''
    def save(self, *args, **kwargs):
        if not self.pk: # object is new
            if self.document.size < 1:
                # ya, I know, maybe all empty files are duplicates of the same file 
                raise DuplicateFileError("No empty files")
            hash = hashlib.md5()
            for chunk in self.document.chunks():
                hash.update(chunk)
            self.md5sum = hash.hexdigest()
            self.document.file.seek(0,0)
            
            if Document.objects.filter(md5sum=self.md5sum).exists():
                raise DuplicateFileError("This file already has already been uploaded")

            chunk = self.document.file.read(1024)
            self.filetype = magic.from_buffer(chunk, mime=True)
            self.document.file.seek(0,0)
            self.slug = slugify(self.title)[:80]
            self.uuid = uuid.uuid4().hex

        super(Document, self).save(*args, **kwargs)

    def filename(self):
        return os.path.basename(self.document.name)

    def purchase_count(self):
        return DocumentPurchase.objects.filter(document=self).count()

    def rating(self):
        return self.up - self.down

    def tmp_url(self):
        doc = self.document
        from storages.backends.S3 import QueryStringAuthGenerator
        q = QueryStringAuthGenerator(doc.storage.connection.aws_access_key_id, doc.storage.connection.aws_secret_access_key)
        q.set_expires_in(60)
        url = q.generate_url('post', settings.AWS_STORAGE_BUCKET_NAME, 'media/' + doc.name)
        logger.debug(url)
        import subprocess

        proc = subprocess.Popen(["./url2.py {}".format('media/' + doc.name)], stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        url = out
        logger.debug(url)
        return url

    '''
    converts the number of postive votes to a score on a scale of 0-100

    OldRange = (OldMax - OldMin)  
    NewRange = (NewMax - NewMin)  
    NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
    '''
    def normalize_positive_votes(self):
        if self.up < 1:
            return 0
        else:
            return ((self.up * 100) / (self.up + self.down))

    # same, but for negative votes
    def normalize_negative_votes(self):
        if self.normalize_positive_votes() == 0:
            return 0
        else: 
            return 100 - self.normalize_positive_votes()

    def __str__(self):
        return "{}".format(self.title)

class Upload(models.Model):
    document = models.ForeignKey(Document)
    owner = models.ForeignKey('user_profile.Student')

    class Meta:
        unique_together = ('document', 'owner')

    def __str__(self):
        return "{} uploaded {}".format(
            self.owner.user.username, 
            self.document.title)

class DocumentPurchase(models.Model):
    document = models.ForeignKey(Document, related_name='purchased_document')
    student = models.ForeignKey('user_profile.Student')
    purchase_date = models.DateTimeField(auto_now_add=True)

    review = models.CharField(max_length=250, blank=True)
    review_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('document', 'student')

    def __str__(self):
        return "{} bought {}".format(
            self.student.user.username, 
            self.document.title)
