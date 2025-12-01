import os
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from accounts.models import Registro, Rol


class Command(BaseCommand):
    help = "Crea o actualiza un usuario admin (modelo Registro) usando variables de entorno."

    def handle(self, *args, **options):
        email = os.getenv('DJANGO_ADMIN_EMAIL')
        password = os.getenv('DJANGO_ADMIN_PASSWORD')
        first_name = os.getenv('DJANGO_ADMIN_FIRST_NAME', 'Admin')
        last_name = os.getenv('DJANGO_ADMIN_LAST_NAME', 'User')
        role_name = os.getenv('DJANGO_ADMIN_ROLE', 'admin')

        if not email or not password:
            self.stdout.write(self.style.WARNING(
                'ensure_admin: variables DJANGO_ADMIN_EMAIL y DJANGO_ADMIN_PASSWORD no definidas; no se crea admin.'
            ))
            return

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
