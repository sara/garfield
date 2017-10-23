from django.db import models


class Sim(models.Model):
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    friendly_name = models.CharField(max_length=255)
    sid = models.CharField(max_length=255)
    iccid = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    rate_plan = models.CharField(max_length=255)

    def __str__(self):
        return "{0}: {1}".format(self.sid,
                                 self.friendly_name)
