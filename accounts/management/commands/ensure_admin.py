import os
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from accounts.models import Registro, Rol
import random
import string


class Command(BaseCommand):
    help = "Crea o actualiza un usuario admin (modelo Registro) usando variables de entorno."

    def handle(self, *args, **options):
        # Valores por defecto para reseteo/migración inicial
        email = os.getenv('DJANGO_ADMIN_EMAIL') or 'matrischol.app@gmail.com'
        password = os.getenv('DJANGO_ADMIN_PASSWORD')
        first_name = os.getenv('DJANGO_ADMIN_FIRST_NAME', 'Admin')
        last_name = os.getenv('DJANGO_ADMIN_LAST_NAME', 'User')
        role_name = os.getenv('DJANGO_ADMIN_ROLE', 'admin')

        if not email:
            self.stdout.write(self.style.WARNING('ensure_admin: sin email; define DJANGO_ADMIN_EMAIL o usa por defecto.'))
            return
        # Si no hay password definido, generar uno fuerte temporal y mostrarlo en logs
        if not password:
            alphabet = string.ascii_letters + string.digits + '!@#$%^&*()-_=+'
            password = ''.join(random.choice(alphabet) for _ in range(16))
            self.stdout.write(self.style.WARNING(f"ensure_admin: DJANGO_ADMIN_PASSWORD no definido; generado temporal: {password}"))

        role, _ = Rol.objects.get_or_create(nom_rol=role_name)

        reg, created = Registro.objects.get_or_create(
            ema_usu=email,
            defaults={
                'nom_usu': first_name,
                'ape_usu': last_name,
                'con_usu': make_password(password),
                'id_rol': role,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Usuario admin creado: {email} (rol: {role_name})"))
            return

        # Si ya existe, asegurar rol y actualizar password si se define
        updated = False
        if reg.id_rol_id != role.id_rol if hasattr(role, 'id_rol') else reg.id_rol_id != role.id:
            reg.id_rol = role
            updated = True
        if password:
            reg.con_usu = make_password(password)
            updated = True
        if first_name and reg.nom_usu != first_name:
            reg.nom_usu = first_name
            updated = True
        if last_name and reg.ape_usu != last_name:
            reg.ape_usu = last_name
            updated = True
        if updated:
            reg.save()
            self.stdout.write(self.style.SUCCESS(f"Usuario admin actualizado: {email} (rol: {role_name})"))
        else:
            self.stdout.write(self.style.NOTICE(f"Usuario admin ya existía sin cambios: {email}"))
