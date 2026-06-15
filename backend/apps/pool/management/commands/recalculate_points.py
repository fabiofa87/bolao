from django.core.management.base import BaseCommand

from apps.pool.services import recalculate_points


class Command(BaseCommand):
    help = "Recalcula os pontos de todos os palpites."

    def handle(self, *args, **options):
        changed = recalculate_points()
        self.stdout.write(self.style.SUCCESS(f"{changed} palpites atualizados."))

