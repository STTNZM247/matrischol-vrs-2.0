from django.db import models
from django.conf import settings
from django.conf.urls.static import static

class Institucion(models.Model):
    id_inst = models.AutoField(primary_key=True, db_column='id_inst')
    nom_inst = models.CharField(max_length=100, db_column='nom_inst')
    tip_inst = models.CharField(max_length=20, null=True, blank=True, db_column='tip_inst')
    cod_dane_inst = models.CharField(max_length=20, null=True, blank=True, db_column='cod_dane_inst')
    dep_inst = models.CharField(max_length=50, null=True, blank=True, db_column='dep_inst')
    mun_inst = models.CharField(max_length=50, null=True, blank=True, db_column='mun_inst')
    dire_inst = models.CharField(max_length=100, null=True, blank=True, db_column='dire_inst')
    tel_inst = models.CharField(max_length=20, null=True, blank=True, db_column='tel_inst')
    ema_inst = models.CharField(max_length=100, null=True, blank=True, db_column='ema_inst')
    id_adm = models.ForeignKey('accounts.Administrativo', db_column='id_adm', on_delete=models.PROTECT)
    # allow duplicate assignment of same subject in same timeslot (institution-wide toggle)
    allow_duplicate_subject_slots = models.BooleanField(default=False, db_column='allow_dup_sub_slots')

    class Meta:
        db_table = 'institucion'

    def __str__(self):
        return self.nom_inst


class Curso(models.Model):
    id_cur = models.AutoField(primary_key=True, db_column='id_cur')
    grd_cur = models.CharField(max_length=10, db_column='grd_cur')
    num_alum_cur = models.IntegerField(default=0, db_column='num_alum_cur')
    cup_disp_cur = models.IntegerField(default=0, db_column='cup_disp_cur')
    id_inst = models.ForeignKey(Institucion, db_column='id_inst', on_delete=models.CASCADE)

    class Meta:
        db_table = 'curso'

    def __str__(self):
        return self.grd_cur


class Matricula(models.Model):
    id_mat = models.AutoField(primary_key=True, db_column='id_mat')
    fch_reg_mat = models.DateField(db_column='fch_reg_mat')
    est_mat = models.CharField(max_length=20, null=True, blank=True, db_column='est_mat')
    obs_mat = models.CharField(max_length=255, null=True, blank=True, db_column='obs_mat')
    # el curso puede ser asignado por el administrativo al aceptar la solicitud,
    # por eso permitimos que inicialmente sea nulo y almacenamos el grado solicitado.
    id_cur = models.ForeignKey(Curso, db_column='id_cur', on_delete=models.CASCADE, null=True, blank=True)
    grado_solicitado = models.IntegerField(null=True, blank=True, db_column='grado_solicitado')
    id_est = models.ForeignKey('people.Estudiante', db_column='id_est', on_delete=models.CASCADE)

    class Meta:
        db_table = 'matricula'

    def __str__(self):
        return f"Matricula {self.id_mat}"


class Documento(models.Model):
    id_doc = models.AutoField(primary_key=True, db_column='id_doc')
    reg_civil_doc = models.CharField(max_length=100, null=True, blank=True, db_column='reg_civil_doc')
    doc_idn_acu = models.CharField(max_length=100, null=True, blank=True, db_column='doc_idn_acu')
    doc_idn_alum = models.CharField(max_length=100, null=True, blank=True, db_column='doc_idn_alum')
    cnt_vac_doc = models.CharField(max_length=100, null=True, blank=True, db_column='cnt_vac_doc')
    adres_doc = models.CharField(max_length=100, null=True, blank=True, db_column='adres_doc')
    fot_alum_doc = models.CharField(max_length=100, null=True, blank=True, db_column='fot_alum_doc')
    visa_extr_doc = models.CharField(max_length=100, null=True, blank=True, db_column='visa_extr_doc')
    cer_med_disca_doc = models.CharField(max_length=100, null=True, blank=True, db_column='cer_med_disca_doc')
    cer_esc_doc = models.CharField(max_length=100, null=True, blank=True, db_column='cer_esc_doc')
    # permitimos vincular documento directamente al estudiante (antes solo a matrícula)
    id_mat = models.ForeignKey(Matricula, db_column='id_mat', on_delete=models.CASCADE, null=True, blank=True)
    id_est = models.ForeignKey('people.Estudiante', db_column='id_est', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'documento'

    def __str__(self):
        return f"Documento {self.id_doc}"


class MatriculaRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('needs_docs', 'Faltan documentos'),
    ]

    id_req = models.AutoField(primary_key=True, db_column='id_req')
    id_acu = models.ForeignKey('people.Acudiente', db_column='id_acu', on_delete=models.CASCADE)
    id_est = models.ForeignKey('people.Estudiante', db_column='id_est', on_delete=models.CASCADE)
    id_inst = models.ForeignKey(Institucion, db_column='id_inst', on_delete=models.CASCADE)
    id_cur = models.ForeignKey(Curso, db_column='id_cur', on_delete=models.CASCADE, null=True, blank=True)
    grado_solicitado = models.IntegerField(null=True, blank=True, db_column='grado_solicitado')
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_column='estado')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    expires_at = models.DateTimeField(null=True, blank=True, db_column='expires_at')
    obs = models.CharField(max_length=255, null=True, blank=True, db_column='obs')

    class Meta:
        db_table = 'matricula_request'

    def __str__(self):
        return f"Solicitud {self.id_req} - {self.id_inst} - {self.id_est}"


class Notificacion(models.Model):
    """Notificaciones internas para administrativos e interfaces.

    Se vincula opcionalmente a un administrativo (id_adm) y a una solicitud de matrícula.
    """
    id_not = models.AutoField(primary_key=True, db_column='id_not')
    id_admin = models.ForeignKey('accounts.Administrativo', db_column='id_adm', on_delete=models.CASCADE, null=True, blank=True)
    id_req = models.ForeignKey(MatriculaRequest, db_column='id_req', on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=150, db_column='titulo')
    mensaje = models.TextField(db_column='mensaje')
    leida = models.BooleanField(default=False, db_column='leida')
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        db_table = 'school_notificacion'

    def __str__(self):
        return f"Notificacion {self.id_not} - {self.titulo}"


class Asignatura(models.Model):
    id_asig = models.AutoField(primary_key=True, db_column='id_asig')
    nombre = models.CharField(max_length=150, db_column='nom_asig', unique=True)

    class Meta:
        db_table = 'asignatura'

    def __str__(self):
        return self.nombre


class Horario(models.Model):
    DAY_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
    ]
    id_hor = models.AutoField(primary_key=True, db_column='id_hor')
    id_asig = models.ForeignKey(Asignatura, db_column='id_asig', on_delete=models.CASCADE)
    id_cur = models.ForeignKey(Curso, db_column='id_cur', on_delete=models.CASCADE)
    id_mae = models.ForeignKey('people.Maestro', db_column='id_mae', on_delete=models.SET_NULL, null=True, blank=True)
    dia = models.IntegerField(choices=DAY_CHOICES, db_column='dia')
    hora_inicio = models.TimeField(null=True, blank=True, db_column='hora_inicio')
    hora_fin = models.TimeField(null=True, blank=True, db_column='hora_fin')
    aula = models.CharField(max_length=50, null=True, blank=True, db_column='aula')

    class Meta:
        db_table = 'horario'

    def __str__(self):
        return f"{self.id_asig.nombre} - {self.get_dia_display()} {self.hora_inicio or ''}-{self.hora_fin or ''}"

urlpatterns = [
    # ... tus rutas ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
