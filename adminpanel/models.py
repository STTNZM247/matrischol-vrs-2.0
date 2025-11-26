from django.db import models
from accounts.models import Registro


class AdminActionLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(Registro, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, default='other')
    model_name = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=200, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp.isoformat()} {self.action} {self.model_name} {self.object_repr}"


class AdminNotification(models.Model):
    """Optional simple notification model to show admin push-like notifications.

    Created when important events occur (registro created/updated).
    """
    user = models.ForeignKey(Registro, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=150)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    # optional link to a related InstitucionRequest
    institucion_request = models.ForeignKey('InstitucionRequest', null=True, blank=True, on_delete=models.CASCADE)
    # optional link to a related CursoRequest
    curso_request = models.ForeignKey('CursoRequest', null=True, blank=True, on_delete=models.CASCADE)
    # optional link to a related MatriculaRequest
    matricula_request = models.ForeignKey('school.MatriculaRequest', null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp.isoformat()} - {self.title}"


class InstitucionRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_NEEDS_INFO = 'needs_info'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_APPROVED, 'Aprobada'),
        (STATUS_REJECTED, 'Rechazada'),
        (STATUS_NEEDS_INFO, 'Falta información'),
    ]

    id_req = models.AutoField(primary_key=True)
    nom_inst = models.CharField(max_length=100)
    tip_inst = models.CharField(max_length=20, null=True, blank=True)
    cod_dane_inst = models.CharField(max_length=20, null=True, blank=True)
    dep_inst = models.CharField(max_length=50, null=True, blank=True)
    mun_inst = models.CharField(max_length=50, null=True, blank=True)
    dire_inst = models.CharField(max_length=100, null=True, blank=True)
    tel_inst = models.CharField(max_length=20, null=True, blank=True)
    ema_inst = models.CharField(max_length=100, null=True, blank=True)
    id_adm = models.ForeignKey('accounts.Administrativo', null=True, blank=True, on_delete=models.SET_NULL)
    submitted_by = models.ForeignKey('accounts.Registro', null=True, blank=True, on_delete=models.SET_NULL, related_name='institucion_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewer = models.ForeignKey('accounts.Registro', null=True, blank=True, on_delete=models.SET_NULL, related_name='institucion_reviews')
    reviewer_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Solicitud {self.id_req} - {self.nom_inst} ({self.status})"

    def missing_fields(self):
        """Return list of important missing fields for basic completeness check."""
        missing = []
        if not self.nom_inst:
            missing.append('Nombre de institución')
        if not self.tipo_inst_complete():
            missing.append('Tipo de institución')
        if not self.cod_dane_inst:
            missing.append('Código DANE')
        if not self.dep_inst:
            missing.append('Departamento')
        if not self.mun_inst:
            missing.append('Municipio')
        if not self.dire_inst:
            missing.append('Dirección')
        if not self.ema_inst and not self.tel_inst:
            missing.append('Contacto (email o teléfono)')
        return missing

    def tipo_inst_complete(self):
        return bool(self.tip_inst and self.tip_inst.strip())


class CursoRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_NEEDS_INFO = 'needs_info'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_APPROVED, 'Aprobada'),
        (STATUS_REJECTED, 'Rechazada'),
        (STATUS_NEEDS_INFO, 'Falta información'),
    ]

    id_req = models.AutoField(primary_key=True)
    id_inst = models.ForeignKey('school.Institucion', null=True, blank=True, on_delete=models.SET_NULL)
    mode = models.CharField(max_length=20, default='primaria')
    sections = models.IntegerField(default=3)
    cupos = models.IntegerField(default=30)
    start_grade = models.IntegerField(null=True, blank=True)
    end_grade = models.IntegerField(null=True, blank=True)
    submitted_by = models.ForeignKey('accounts.Registro', null=True, blank=True, on_delete=models.SET_NULL, related_name='curso_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewer = models.ForeignKey('accounts.Registro', null=True, blank=True, on_delete=models.SET_NULL, related_name='curso_reviews')
    reviewer_comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"CursoRequest {self.id_req} - {self.id_inst.nom_inst if self.id_inst else 'sin institución'} ({self.status})"

    def missing_fields(self):
        missing = []
        if not self.id_inst:
            missing.append('Institución')
        if self.mode == 'custom' and (self.start_grade is None or self.end_grade is None):
            missing.append('Grado inicio y fin (modo personalizado)')
        return missing


