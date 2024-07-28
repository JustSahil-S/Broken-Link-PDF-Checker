from django.db import models
import datetime


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