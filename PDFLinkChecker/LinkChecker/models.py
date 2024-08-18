from django.db import models
from enum import Enum
from django.contrib.auth.models import AbstractUser
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re

class MultiEmailField(models.TextField):

    def to_python(self, value):

        if not value:
            return None  # []

        cleaned_email_list = list()
        #email_list = filter(None, value.split(','))
        email_list = filter(None, re.split(r';|,\s|\n', value))

        for email in email_list:
            if email.strip(' @;,'):
                cleaned_email_list.append(email.strip(' @;,'))

        #print cleaned_email_list
        cleaned_email_list = list(set(cleaned_email_list))

        return ", ".join(cleaned_email_list)

    def validate(self, value, model_instance):
        """Check if value consists only of valid emails."""

        # Use the parent's handling of required fields, etc.
        super(MultiEmailField, self).validate(value, model_instance)

        email_list = value.split(',')

        for email in email_list:
            try:
                validate_email(email.strip())
            except:
                raise ValidationError(_('%s is not a valid e-mail address.') % email)

class CheckLinkResult(Enum):
    NO_SUCH_PDF = 1
    NO_SUCH_LINK = 2
    LINK_OK = 3
    LINK_BROKEN = 4
    LINK_BROKEN_SAME_STATUS = 5
    LINK_BROKEN_STATUS_CHANGED = 6
    LINK_NOT_PROCESSED = 7

# Create your models here.
class Links(models.Model):
    url = models.URLField(max_length = 1000)
    statusCode = models.IntegerField()
    reason = models.CharField(max_length = 40)
    dismiss = models.BooleanField()
    ignore = models.BooleanField()
    pdfSource = models.CharField(max_length = 1000)
    finalurl = models.URLField(max_length = 1000)
    urlText = models.CharField(max_length = 1000)
    lastChecked = models.DateTimeField()
    lastIteration = models.IntegerField(default=0)

class Links_table(models.Model):
    url = models.URLField(max_length = 1000)
    finalUrl = models.URLField(max_length = 1000)
    moreInPdf = models.BooleanField(default=False)
    urlText = models.CharField(max_length = 1000) #url anchor
    statusCode = models.IntegerField()
    reason = models.CharField(max_length = 40)
    pdfSource = models.CharField(max_length = 1000)
    broken = models.BooleanField(default=False)
    dismiss = models.BooleanField(default=False)
    ignore = models.BooleanField(default=False)
    brokenSince = models.DateTimeField()
    lastChecked = models.DateTimeField()
    lastIteration = models.IntegerField(default=0)
    lastLog = models.CharField(max_length = 1000)

    
class Globals (models.Model):
    iteration =  models.IntegerField(default = 0)
    pdfDirectory = models.CharField(max_length = 1000)
    checkAllStartAtHour = models.IntegerField(default=7)
    checkAllStartAtMin = models.IntegerField(default=0)
    checkAllIntervalHours = models.IntegerField(default=24)
    checkAllIntervalMins = models.IntegerField(default=0)
    emailNotifyOnNewLink = models.BooleanField(default=True) #when new broken link found
    attachListToEmail = models.BooleanField(default=True)
    sendToEmails = MultiEmailField(max_length = 200, default="murali@php.com,murali_kumar@hotmail.com")
    fromEmail= models.CharField(max_length=100, default="murali.singamsetty@gmail.com")
    smtpHost = models.CharField(max_length=100, default="smtp.gmail.com")
    smtpPort = models.IntegerField(default=587)
    smtpEncryption = models.CharField(max_length=20, default="tls")
    smtpUsername = models.CharField(max_length=50, default="murali.singamsetty@gmail.com")
    smtpPassword = models.CharField(max_length=50, default="ysxyoczkwjzmswiu")

class User(AbstractUser):
    pass