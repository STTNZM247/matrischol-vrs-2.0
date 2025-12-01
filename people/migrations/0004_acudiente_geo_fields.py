from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0003_maestro'),
    ]

    operations = [
        migrations.AddField(
            model_name='acudiente',
            name='lat_acu',
            field=models.DecimalField(null=True, blank=True, max_digits=9, decimal_places=6, db_column='lat_acu'),
        ),
        migrations.AddField(
            model_name='acudiente',
            name='lon_acu',
            field=models.DecimalField(null=True, blank=True, max_digits=9, decimal_places=6, db_column='lon_acu'),
        ),
        migrations.AddField(
            model_name='acudiente',
            name='acc_acu',
            field=models.IntegerField(null=True, blank=True, db_column='acc_acu', help_text='Precisión (m) de la geolocalización capturada'),
        ),
    ]
