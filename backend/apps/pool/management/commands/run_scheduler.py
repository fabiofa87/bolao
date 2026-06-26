import time

from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.pool.sync import sync_world_cup


class Command(BaseCommand):
    help = "Executa a sincronização da Copa a cada dez minutos."

    def handle(self, *args, **options):
        last_prune_date = None
        while True:
            try:
                today = time.strftime("%Y-%m-%d")
                if today != last_prune_date:
                    call_command("prune_daily_chat")
                    last_prune_date = today
                sync_world_cup()
                self.stdout.write("Sincronização concluída.")
            except Exception as exc:
                self.stderr.write(f"Sincronização falhou: {exc}")
            time.sleep(600)
