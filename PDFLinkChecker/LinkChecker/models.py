from django.db import models
from enum import Enum
from django.contrib.auth.models import AbstractUser

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
    iteration =  models.IntegerField(default=0)
    pdfDirectory = models.CharField(max_length = 1000)
    checkAllStartAtHour = models.IntegerField(default=7)
    checkAllStartAtMin = models.IntegerField(default=0)
    checkAllIntervalHours = models.IntegerField(default=24)
    checkAllIntervalMins = models.IntegerField(default=0)
    emailNotifyOnNewLink = models.BooleanField(default=True) #when new broken link found
    attachListToEmail = models.BooleanField(default=True)
    emailAddress = models.CharField(max_length = 1000, default="murali@php.com")
    fromEmail= models.CharField(max_length=100, default="murali.singamsetty@gmail.com")
    smtpHost = models.CharField(max_length=100, default="smtp.gmail.com")
    smtpPort = models.IntegerField(default=587)
    smtpEncryption = models.CharField(max_length=20, default="tls")
    smtpUsername = models.CharField(max_length=50, default="murali.singamsetty@gmail.com")
    smtpPassword = models.CharField(max_length=50, default="ysxyoczkwjzmswiu")

class User(AbstractUser):
    pass