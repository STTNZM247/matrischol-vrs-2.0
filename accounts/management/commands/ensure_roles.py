from django.core.management.base import BaseCommand
from accounts.models import Rol


REQUIRED_ROLES = [
    "admin",
    "administrativo",
    "acudiente",
    "estudiante",
]


class Command(BaseCommand):
    help = "Crea (si faltan) los roles base: admin, administrativo, acudiente, estudiante"

    def handle(self, *args, **options):
        created = 0
        for name in REQUIRED_ROLES:
            obj, was_created = Rol.objects.get_or_create(nom_rol=name)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Roles asegurados. Nuevos creados: {created}"))
