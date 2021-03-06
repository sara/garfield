from celery import chain
from celery import shared_task

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.template.loader import render_to_string

from twilio.rest import Client

import requests

from contacts.models import Contact
from phone_numbers.models import PhoneNumber
from sims.models import Whisper


@shared_task
def lookup_phone_number(phone_number, type=None, addons=None):
    client = Client(settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN)

    return client.lookups.phone_numbers(phone_number).fetch(add_ons=addons,
                                                            type=type)


@shared_task
def lookup_contact(contact_number):
    contact = Contact.objects.get(phone_number=contact_number)

    return chain(lookup_contact_whitepages.si(contact.id),
                 lookup_contact_nextcaller.si(contact.id),
                 lookup_contact_tellfinder.si(contact.id)).apply_async()


@shared_task
def lookup_contact_whitepages(contact_id):
    contact = Contact.objects.get(pk=contact_id)

    lookup = lookup_phone_number(contact.phone_number,
                                 type="carrier",
                                 addons="whitepages_pro_caller_id")

    if lookup.add_ons['status'] == 'successful':
        contact = apply_lookup_whitepages_to_contact(contact, lookup)

        fields = [field.name for field in Contact._meta.get_fields()
                  if field.name.startswith('whitepages')]

        contact.save(update_fields=fields)

        contact.identified = True
        contact.save(update_fields=['identified'])

    if lookup.add_ons['status'] == 'successful':
        twilio_number = contact.related_phone_numbers.last()
        if twilio_number:
            send_notification_whitepages.apply_async(args=[contact.id,
                                                           twilio_number.e164])


def apply_lookup_whitepages_to_contact(contact, lookup):
    result = lookup.add_ons['results']["whitepages_pro_caller_id"]['result']

    if result['belongs_to']:
        contact.whitepages_entity_type = result['belongs_to'][0]['type']

        if contact.whitepages_entity_type == "Person":
            contact.whitepages_first_name = result['belongs_to'
                                                   ][0]['firstname']
            contact.whitepages_middle_name = result['belongs_to'
                                                    ][0]['middlename']
            contact.whitepages_last_name = result['belongs_to'][0]['lastname']
            contact.whitepages_gender = result['belongs_to'][0]['gender']
        else:
            contact.whitepages_business_name = result['belongs_to'][0]['name']

    if result['current_addresses']:
        contact.whitepages_address = \
            result['current_addresses'][0]['street_line_1']
        contact.whitepages_address_two = \
            result['current_addresses'][0]['street_line_2']
        contact.whitepages_city = result['current_addresses'][0]['city']
        contact.whitepages_state = result['current_addresses'
                                          ][0]['state_code']
        contact.whitepages_country = \
            result['current_addresses'][0]['country_code']
        contact.whitepages_zip_code = \
            result['current_addresses'][0]['postal_code']
        contact.whitepages_address_type = \
            result['current_addresses'][0]['location_type']

        if result['current_addresses'][0]['lat_long']:
            contact.whitepages_latitude = \
                result['current_addresses'][0]['lat_long']['latitude']
            contact.whitepages_longitude = \
                result['current_addresses'][0]['lat_long']['longitude']
            contact.whitepages_accuracy = \
                result['current_addresses'][0]['lat_long']['accuracy']

    contact.whitepages_prepaid = result['is_prepaid']
    contact.whitepages_phone_type = result['line_type']
    contact.whitepages_commercial = result['is_commercial']

    contact.identified = True

    contact.carrier = lookup.carrier['name']
    contact.phone_number_type = lookup.carrier['type']
    contact.phone_number_friendly = lookup.national_format

    return contact


@shared_task
def send_notification_whitepages(contact_id, twilio_number):
    number = PhoneNumber.objects.get(e164=twilio_number)
    contact = Contact.objects.get(pk=contact_id)

    kwargs = {'from_': contact.phone_number,
              'to': number.e164}

    identity = render_to_string("sms_notification_whitepages_identity.html",
                                model_to_dict(contact))

    kwargs['body'] = identity
    send_whisper.apply_async(kwargs=kwargs)

    location = render_to_string("sms_notification_whitepages_location.html",
                                model_to_dict(contact))

    kwargs['body'] = location
    send_whisper.apply_async(kwargs=kwargs)

    return {'results': [identity, location]}


@shared_task
def lookup_contact_nextcaller(contact_id):
    contact = Contact.objects.get(pk=contact_id)

    lookup = lookup_phone_number(contact.phone_number,
                                 addons="nextcaller_advanced_caller_id")

    if lookup.add_ons['status'] == 'successful':
        contact = apply_lookup_nextcaller_to_contact(contact, lookup)

        fields = [field.name for field in Contact._meta.get_fields()
                  if field.name.startswith('nextcaller')]

        contact.save(update_fields=fields)

    if lookup.add_ons['status'] == 'successful':
        twilio_number = contact.related_phone_numbers.last()

        if twilio_number:
            send_notification_nextcaller.apply_async(args=[contact.id,
                                                           twilio_number.e164])


def apply_lookup_nextcaller_to_contact(contact, lookup):
    result = \
        lookup.add_ons['results']['nextcaller_advanced_caller_id']['result']

    if result['records']:
        result = result['records'][0]

        contact.nextcaller_email = result['email']

        contact.nextcaller_first_name = result['first_name']
        contact.nextcaller_middle_name = result['middle_name']
        contact.nextcaller_last_name = result['last_name']
        contact.nextcaller_gender = result['gender']
        contact.nextcaller_age = result['age']

        if not result['first_name'] and not result['last_name']:
            contact.nextcaller_business_name = result['name']

        contact.nextcaller_marital_status = result['marital_status']
        contact.nextcaller_home_owner_status = result['home_owner_status']
        contact.nextcaller_education = result['education']
        contact.nextcaller_household_income = result['household_income']
        contact.nextcaller_length_of_residence = result['length_of_residence']
        contact.nextcaller_market_value = result['market_value']
        contact.nextcaller_occupation = result['occupation']

        if result['presence_of_children'] == 'Yes':
            contact.nextcaller_children_presence = True
        else:
            contact.nextcaller_children_presence = False

        if result['high_net_worth'] == 'Yes':
            contact.nextcaller_high_net_worth = True
        else:
            contact.nextcaller_high_net_worth = False

        if result['address']:
            contact.nextcaller_address = result['address'][0]['line1']
            contact.nextcaller_address_two = result['address'][0]['line2']
            contact.nextcaller_city = result['address'][0]['city']
            contact.nextcaller_state = result['address'][0]['state']
            contact.nextcaller_country = result['address'][0]['country']
            contact.nextcaller_zip_code = result['address'][0]['zip_code']

        if result['phone']:
            contact.nextcaller_phone_type = result['phone'][0]['line_type']
            contact.nextcaller_carrier = result['phone'][0]['carrier']

        for link in result['social_links']:
            if link['type'] == 'facebook':
                contact.nextcaller_facebook = link['url']
            elif link['type'] == 'twitter':
                contact.nextcaller_twitter = link['url']
            elif link['type'] == 'linkedin':
                contact.nextcaller_linkedin = link['url']

        contact.identified = True

    return contact


@shared_task
def send_notification_nextcaller(contact_id, twilio_number):
    number = PhoneNumber.objects.get(e164=twilio_number)
    contact = Contact.objects.get(pk=contact_id)

    kwargs = {'from_': contact.phone_number,
              'to': number.e164}

    identity = render_to_string("sms_notification_nextcaller_identity.html",
                                model_to_dict(contact,
                                              exclude=['id']))

    kwargs['body'] = identity

    send_whisper.apply_async(kwargs=kwargs)

    location = render_to_string("sms_notification_nextcaller_location.html",
                                model_to_dict(contact,
                                              exclude=['id']))

    kwargs['body'] = location

    send_whisper.apply_async(kwargs=kwargs)

    demo = render_to_string("sms_notification_nextcaller_demographics.html",
                            model_to_dict(contact,
                                          exclude=['id']))

    kwargs['body'] = demo

    send_whisper.apply_async(kwargs=kwargs)

    return {"results": [identity, location, demo]}


@shared_task
def lookup_contact_tellfinder(contact_id):
    contact = Contact.objects.get(pk=contact_id)

    uri = "https://api.tellfinder.com/facets" \
          "?q=phone:{0}&keys[]=posttime".format(contact.phone_number)

    headers = {"x-api-key": settings.TELLFINDER_API_KEY}

    results = requests.get(uri, headers=headers)

    if results.status_code == 200:
        result_dict = results.json()

        if result_dict['total'] > 0:
            data = {}

            data['total'] = result_dict['total']
            data['earliest_ad'] = result_dict['facets'][0]['metrics']['min']
            data['latest_ad'] = result_dict['facets'][0]['metrics']['max']

            twilio_number = contact.related_phone_numbers.last()

            if twilio_number:
                send_notification_tellfinder \
                    .apply_async(args=[data,
                                       contact_id,
                                       twilio_number.e164])
    return results.json()


@shared_task
def send_notification_tellfinder(data, contact_id, twilio_number):
    number = PhoneNumber.objects.get(e164=twilio_number)
    contact = Contact.objects.get(pk=contact_id)

    body = render_to_string("sms_notification_tellfinder.html",
                            data)

    kwargs = {'from_': contact.phone_number,
              'to': number.e164,
              'body': body}

    send_whisper.apply_async(kwargs=kwargs)

    return body


@shared_task
def send_whisper(from_=None, to=None, body=None):
    phone_number = PhoneNumber.objects.get(e164=to)
    contact = Contact.objects.get(phone_number=from_)

    whisper = Whisper(related_phone_number=phone_number,
                      related_contact=contact,
                      body=body)

    whisper.save()


@receiver(post_save, sender=Contact)
def identify_contact(sender, **kwargs):
    if kwargs.get('created', False):
        instance = kwargs.get('instance')

        lookup_contact \
            .apply_async(args=[instance.phone_number])
