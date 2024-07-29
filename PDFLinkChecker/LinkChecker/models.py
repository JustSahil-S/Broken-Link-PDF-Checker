from django.db import models
import datetime
from enum import Enum

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
    brokenSince = models.DateTimeField(default=datetime.datetime.now())
    lastChecked = models.DateTimeField()
    lastIteration = models.IntegerField(default=0)
    lastLog = models.CharField(max_length = 1000)

    
class Globals (models.Model):
    iteration =  models.IntegerField(default=0)
    pdfDirectory = models.CharField(max_length = 1000)
    checkAllNextAt = models.DateTimeField(default=datetime.datetime.now())
    recheckIntervalDays = models.IntegerField(default=0)
    recheckIntervalHours = models.IntegerField(default=0)
    recheckIntervalMins = models.IntegerField(default=5)

