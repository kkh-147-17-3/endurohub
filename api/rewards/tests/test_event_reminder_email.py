from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from accounts.models import UserProfile
from rewards.management.commands.send_event_reminder import CONFIRMATION


User = get_user_model()


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='ENDURO/HUB <contact@endurohub.kr>',
)
class EventReminderEmailTests(TestCase):
    def make_user(self, email, *, verified=True, opted_in=True, active=True):
        user = User.objects.create_user(
            username=email,
            email=email,
            is_active=active,
        )
        UserProfile.objects.create(
            user=user,
            email_verified=verified,
            email_updates_opt_in=opted_in,
        )
        return user

    def test_test_mode_sends_only_to_explicit_address(self):
        self.make_user('member@example.com')

        call_command('send_event_reminder', to='owner@example.com')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['owner@example.com'])
        self.assertTrue(mail.outbox[0].subject.startswith('[TEST]'))
        self.assertIn('text/html', [part[1] for part in mail.outbox[0].alternatives])
        self.assertEqual(len(mail.outbox[0].attachments), 1)
        self.assertEqual(
            mail.outbox[0].attachments[0]['Content-ID'],
            '<endurohub-multisport-event>',
        )
        self.assertEqual(mail.outbox[0].attachments[0].get_content_type(), 'image/png')
        html = mail.outbox[0].alternatives[0].content
        self.assertIn('src="cid:endurohub-multisport-event"', html)
        self.assertIn('word-break: keep-all', html)
        self.assertNotIn('.summary-cell { display: block', html)

    def test_send_all_requires_exact_confirmation(self):
        with self.assertRaises(CommandError):
            call_command('send_event_reminder', send_all=True)

    @patch('rewards.management.commands.send_event_reminder.date')
    def test_send_all_only_targets_verified_opted_in_active_users(self, mock_date):
        mock_date.today.return_value = date(2026, 9, 4)
        self.make_user('eligible@example.com')
        self.make_user('opted-out@example.com', opted_in=False)
        self.make_user('unverified@example.com', verified=False)
        self.make_user('inactive@example.com', active=False)

        call_command(
            'send_event_reminder',
            send_all=True,
            confirm=CONFIRMATION,
            delay=0,
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['eligible@example.com'])
        self.assertFalse(mail.outbox[0].subject.startswith('[TEST]'))
