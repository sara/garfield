from django.core.exceptions import ValidationError
from django.test import TestCase

from mock import patch

from contacts.models import Contact


class ContactModelTestCase(TestCase):
    @patch('deterrence.tasks.check_campaign_for_contact.apply_async')
    @patch('contacts.tasks.lookup_contact.apply_async')
    def setUp(self, mock_lookup, mock_check_campaign):
        self.contact = Contact.objects.create(phone_number="+15558675309")

    def test_string_representation(self):
        self.assertEquals(str(self.contact),
                          "+15558675309: None None")

    @patch('contacts.tasks.lookup_contact.apply_async')
    def test_phone_number_validation(self, mock_lookup):
        contact = Contact(phone_number="1111")
        self.assertRaises(ValidationError,
                          contact.full_clean)
