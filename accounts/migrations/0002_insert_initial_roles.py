from django.db import migrations


def create_roles(apps, schema_editor):
    Rol = apps.get_model('accounts', 'Rol')
    roles = ['acudiente', 'estudiante', 'admin', 'administrativo']
    for r in roles:
        Rol.objects.get_or_create(nom_rol=r)


def delete_roles(apps, schema_editor):
    Rol = apps.get_model('accounts', 'Rol')
    Rol.objects.filter(nom_rol__in=['acudiente', 'estudiante', 'admin', 'administrativo']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_roles, delete_roles),
    ]
