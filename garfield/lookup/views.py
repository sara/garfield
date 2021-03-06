import requests
from django.http import HttpResponse

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from contacts.models import Contact
from .models import Lookup
from .decorators import twilio_view
import phonenumbers
from .lookup_constants import *

@twilio_view
def index(request):
    """
        Endpoint to lookup contact information via Twilio
    """
    response = MessagingResponse()
    message = ""
    try:
      parsed_data = lookup_contact(request)
    except InputError as e:
      message = str(e.message)
      response.message(message)
      return response
    except Contact.DoesNotExist as contacexp:
        response.message(contact_not_found)
        return response
    message += "%s %d\n" % (number_of_texts, parsed_data['num_texts'])

    message += "%s %s\n"% (number_of_calls, parsed_data['num_calls'])
    
    message += "%s %d\n"% (number_of_contacts, parsed_data['contact_contact_count'])
    if parsed_data['contact_carrier'] != None:
      message += "Carrier:  " + parsed_data['contact_carrier']
    response.message(message)
    return response

def lookup_contact(request):
    """
        Given a Phone Number in a twilio response body lookup the information 
        in our db and return meta data
        :param request A query dict from twilio 
    """
    contact_number = request.POST.get('Body')
    try:
      valid = is_valid_number(contact_number)
      if valid is False:
        raise Exception
    except Exception as e:
      complete_error_message = "Error on input %s \n%s" % (contact_number, error_message)
      raise InputError(contact_number, complete_error_message)
    contact_information = {}
    try:
      contact = Contact.objects.get(phone_number = contact_number)
      num_texts = contact.sms_message_count 
      num_calls = contact.call_count
      contact_contact_count = contact.contact_count
      contact_carrier = contact.carrier
      contact_information['phone_number'] = contact_number
      contact_information['num_texts'] = num_texts
      contact_information['num_calls'] = num_calls
      contact_information['contact_contact_count'] = contact_contact_count
      contact_information['contact_carrier'] = contact_carrier
      create_lookup_entry(request, contact_number, contact)
    except:
      create_lookup_entry(request, contact_number, None)
      raise Contact.DoesNotExist
    return (contact_information)

class Error(Exception):
  pass

class InputError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

def is_valid_number(number:str):
    try:
      phnumber = phonenumbers.parse(number)
      return(phonenumbers.is_possible_number(phnumber))
    except Exception as e:
      raise e

def create_lookup_entry(request, contact_phone_number, related_contact): 
    from_number = request.POST.get('From')
    lookup_entry = Lookup.objects.create(officer_phone_number=from_number, contact_phone_number=contact_phone_number, related_contact=related_contact)
    lookup_entry.save()



