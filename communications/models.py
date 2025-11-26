from django.db import models


class Mensaje(models.Model):
    id_men = models.AutoField(primary_key=True, db_column='id_men')
    id_remitente = models.ForeignKey('accounts.Registro', related_name='mensajes_enviados', db_column='id_remitente', on_delete=models.CASCADE)
    id_destinatario = models.ForeignKey('accounts.Registro', related_name='mensajes_recibidos', db_column='id_destinatario', on_delete=models.CASCADE)
    asunto = models.CharField(max_length=100, null=True, blank=True, db_column='asunto')
    cuerpo = models.TextField(null=True, blank=True, db_column='cuerpo')
    fch_envio = models.DateTimeField(auto_now_add=True, db_column='fch_envio')
    leido = models.BooleanField(default=False, db_column='leido')

    class Meta:
        db_table = 'mensaje'

    def __str__(self):
        return self.asunto or f"Mensaje {self.id_men}"


class Notificacion(models.Model):
    id_notif = models.AutoField(primary_key=True, db_column='id_notif')
    tit_notif = models.CharField(max_length=100, db_column='tit_notif')
    men_notif = models.TextField(db_column='men_notif')
    fch_envio = models.DateTimeField(auto_now_add=True, db_column='fch_envio')
    leida = models.BooleanField(default=False, db_column='leida')
    id_usu = models.ForeignKey('accounts.Registro', db_column='id_usu', on_delete=models.CASCADE)

    class Meta:
        db_table = 'notificacion'

    def __str__(self):
        return self.tit_notif


class Reporte(models.Model):
    id_rep = models.AutoField(primary_key=True, db_column='id_rep')
    tit_rep = models.CharField(max_length=100, db_column='tit_rep')
    desc_rep = models.TextField(null=True, blank=True, db_column='desc_rep')
    fch_rep = models.DateTimeField(auto_now_add=True, db_column='fch_rep')
    id_usu = models.ForeignKey('accounts.Registro', db_column='id_usu', on_delete=models.CASCADE)

    class Meta:
        db_table = 'reporte'

    def __str__(self):
        return self.tit_rep


class EmailLog(models.Model):
    id_email_log = models.AutoField(primary_key=True, db_column='id_email_log')
    destinatario = models.EmailField(db_column='destinatario')
    asunto = models.CharField(max_length=150, db_column='asunto')
    cuerpo_resumen = models.CharField(max_length=255, null=True, blank=True, db_column='cuerpo_resumen')
    exito = models.BooleanField(default=False, db_column='exito')
    error = models.TextField(null=True, blank=True, db_column='error')
    fch_envio = models.DateTimeField(auto_now_add=True, db_column='fch_envio')
    tipo = models.CharField(max_length=50, db_column='tipo', help_text='Ej: password_change, notification')
    id_usu = models.ForeignKey('accounts.Registro', null=True, blank=True, db_column='id_usu', on_delete=models.SET_NULL)

    class Meta:
        db_table = 'email_log'

    def __str__(self):
        return f"Email {self.asunto} -> {self.destinatario}"[:60]
