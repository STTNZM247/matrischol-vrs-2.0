from django.db import models


class Acudiente(models.Model):
    id_acu = models.AutoField(primary_key=True, db_column='id_acu')
    num_doc_acu = models.CharField(max_length=20, db_column='num_doc_acu')
    tel_acu = models.CharField(max_length=20, null=True, blank=True, db_column='tel_acu')
    dir_acu = models.CharField(max_length=200, null=True, blank=True, db_column='dir_acu')
    lat_acu = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, db_column='lat_acu')
    lon_acu = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, db_column='lon_acu')
    acc_acu = models.IntegerField(null=True, blank=True, db_column='acc_acu', help_text='Precisión (m) de la geolocalización capturada')
    id_usu = models.ForeignKey('accounts.Registro', db_column='id_usu', on_delete=models.CASCADE)
    cedula_img = models.ImageField(upload_to='acudientes/cedulas/', null=True, blank=True, db_column='cedula_img')
    foto_perfil = models.ImageField(upload_to='acudientes/fotos/', null=True, blank=True, db_column='foto_perfil')

    class Meta:
        db_table = 'acudiente'

    def __str__(self):
        return self.num_doc_acu


class Estudiante(models.Model):
    id_est = models.AutoField(primary_key=True, db_column='id_est')
    tip_doc_est = models.CharField(max_length=20, null=True, blank=True, db_column='tip_doc_est')
    num_doc_est = models.CharField(max_length=20, db_column='num_doc_est')
    fch_nac_estu = models.DateField(null=True, blank=True, db_column='fch_nac_estu')
    tel_estu = models.CharField(max_length=20, null=True, blank=True, db_column='tel_estu')
    id_usu = models.ForeignKey('accounts.Registro', db_column='id_usu', on_delete=models.CASCADE)
    id_acu = models.ForeignKey(Acudiente, db_column='id_acu', on_delete=models.CASCADE)
    foto_perfil = models.ImageField(upload_to='estudiantes/fotos/', null=True, blank=True, db_column='foto_perfil')

    class Meta:
        db_table = 'estudiante'

    def __str__(self):
        return self.num_doc_est


class Maestro(models.Model):
    id_mae = models.AutoField(primary_key=True, db_column='id_mae')
    num_doc_mae = models.CharField(max_length=20, db_column='num_doc_mae')
    tel_mae = models.CharField(max_length=20, null=True, blank=True, db_column='tel_mae')
    dir_mae = models.CharField(max_length=100, null=True, blank=True, db_column='dir_mae')
    especialidad = models.CharField(max_length=100, null=True, blank=True, db_column='especialidad')
    id_usu = models.ForeignKey('accounts.Registro', db_column='id_usu', on_delete=models.CASCADE)
    id_inst = models.ForeignKey('school.Institucion', db_column='id_inst', on_delete=models.CASCADE, null=True, blank=True)
    foto_perfil = models.ImageField(upload_to='maestros/fotos/', null=True, blank=True, db_column='foto_perfil')

    class Meta:
        db_table = 'maestro'

    def __str__(self):
        return self.num_doc_mae
