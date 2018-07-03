from celery import chain
from celery import shared_task

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.template.loader import render_to_string

import requests

from django.shortcuts import render
from django.http import HttpResponse

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from contacts.models import Contact
from .decorators import twilio_view

# Create your views here.
@twilio_view
def index(request):
  print(request)
  response = MessagingResponse()
  response.message(lookup_contact(request))
  return response

def lookup_contact(request):
    suspect_number = request.GET.get('From')
    contact = Contact.objects.get(phone_number = suspect_number)
    if contact != None:
        return (contact.nextcaller_first_name)
    else:
        return ("No contact")


