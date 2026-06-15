import time

from django.core.management.base import BaseCommand

from apps.pool.sync import sync_world_cup


class Command(BaseCommand):
    help = "Executa a sincronização da Copa a cada dez minutos."

    def handle(self, *args, **options):
        while True:
            try:
                sync_world_cup()
                self.stdout.write("Sincronização concluída.")
            except Exception as exc:
                self.stderr.write(f"Sincronização falhou: {exc}")
            time.sleep(600)

