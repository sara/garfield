from django.db import models
from contacts.models import Contact

# Create your models here.
class Lookup(models.Model):
    look_up_date = models.DateTimeField(auto_now_add=True)
    officer_phone_number = models.CharField(max_length=12,
                                            db_index=True,
                                            blank=False,
                                            null=False)
    contact_phone_number = models.CharField(max_length=15,
                                            db_index=True,
                                            blank=False,
                                            null=False)
    related_contact = models.ForeignKey(Contact, null=True, on_delete=models.SET_NULL)

    def save(self,force_insert=False,force_update=False,**kwargs):
        super(Lookup,self).save(force_insert,force_update)

