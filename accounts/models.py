from django.db import models


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True, db_column='id_rol')
    nom_rol = models.CharField(max_length=50, db_column='nom_rol')

    class Meta:
        db_table = 'rol'

    def __str__(self):
        return self.nom_rol


class Registro(models.Model):
    id_usu = models.AutoField(primary_key=True, db_column='id_usu')
    nom_usu = models.CharField(max_length=50, db_column='nom_usu')
    ape_usu = models.CharField(max_length=50, db_column='ape_usu')
    ema_usu = models.EmailField(max_length=100, unique=True, db_column='ema_usu')
    con_usu = models.CharField(max_length=255, db_column='con_usu')
    id_rol = models.ForeignKey(Rol, db_column='id_rol', on_delete=models.PROTECT)

    class Meta:
        db_table = 'registro'

    def __str__(self):
        return f"{self.nom_usu} {self.ape_usu}"


class Administrativo(models.Model):
    id_adm = models.AutoField(primary_key=True, db_column='id_adm')
    num_doc_adm = models.CharField(max_length=20, db_column='num_doc_adm')
    tel_adm = models.CharField(max_length=20, null=True, blank=True, db_column='tel_adm')
    dir_adm = models.CharField(max_length=300, null=True, blank=True, db_column='dir_adm')
    tip_carg_adm = models.CharField(max_length=50, null=True, blank=True, db_column='tip_carg_adm')
    cedula_img = models.ImageField(upload_to='administrativos/cedulas/', null=True, blank=True, db_column='cedula_img')
    foto_perfil = models.ImageField(upload_to='administrativos/fotos/', null=True, blank=True, db_column='foto_perfil')
    id_usu = models.ForeignKey(Registro, db_column='id_usu', on_delete=models.CASCADE)

    class Meta:
        db_table = 'administrativo'

    def __str__(self):
        return self.num_doc_adm


class PasswordResetRequest(models.Model):
    """Solicitud de restablecimiento de contraseña con token único y expiración."""
    id = models.AutoField(primary_key=True, db_column='id_pwd_req')
    registro = models.ForeignKey(Registro, db_column='id_usu', on_delete=models.CASCADE, related_name='password_resets')
    token = models.CharField(max_length=64, unique=True, db_column='token')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    expires_at = models.DateTimeField(db_column='expires_at')
    used = models.BooleanField(default=False, db_column='used')
    ip_request = models.CharField(max_length=45, null=True, blank=True, db_column='ip_request')

    class Meta:
        db_table = 'password_reset_request'

    def is_valid(self):
        from django.utils import timezone
        return (not self.used) and timezone.now() < self.expires_at

    def mark_used(self):
        self.used = True
        self.save(update_fields=['used'])

    def __str__(self):
        return f"Reset token {self.token[:12]}... for {self.registro.ema_usu}" if self.registro else self.token
