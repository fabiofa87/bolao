from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import DailyChatMessage


class Command(BaseCommand):
    help = "Remove mensagens de chat de dias anteriores."

    def handle(self, *args, **options):
        today = timezone.localdate()
        deleted, _ = DailyChatMessage.objects.filter(chat_date__lt=today).delete()
        self.stdout.write(self.style.SUCCESS(f"{deleted} mensagens removidas."))

