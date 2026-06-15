from django.core.management.base import BaseCommand

from apps.pool.sync import sync_world_cup


class Command(BaseCommand):
    help = "Sincroniza jogos e resultados da Copa de 2026."

    def handle(self, *args, **options):
        run = sync_world_cup()
        self.stdout.write(
            self.style.SUCCESS(
                f"Sincronização concluída: {run.matches_received} recebidos, "
                f"{run.matches_changed} alterados."
            )
        )

