from django.db import models

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
    lastChecked = models.DateField()
    iteration = models.IntegerField(default=0)
    