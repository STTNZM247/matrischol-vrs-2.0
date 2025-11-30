from django import forms
from django.contrib.auth.hashers import make_password
from accounts.models import Registro, Rol


class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['nom_rol']
        labels = {
            'nom_rol': 'Nombre del rol nuevo',
        }


class RegistroCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')

    class Meta:
        model = Registro
        fields = ['nom_usu', 'ape_usu', 'ema_usu', 'id_rol']
        labels = {
            'nom_usu': 'Nombre',
            'ape_usu': 'Apellido',
            'ema_usu': 'Correo',
            'id_rol': 'Rol',
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password_confirm')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        pwd = self.cleaned_data.get('password')
        if pwd:
            instance.con_usu = make_password(pwd)
        if commit:
            instance.save()
        return instance


class RegistroEditForm(forms.ModelForm):
    class Meta:
        model = Registro
        fields = ['nom_usu', 'ape_usu', 'ema_usu', 'id_rol']
        labels = {
            'nom_usu': 'Nombre',
            'ape_usu': 'Apellido',
            'ema_usu': 'Correo',
            'id_rol': 'Rol',
        }


class PasswordChangeForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, label='Nueva contraseña')
    confirm_password = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('new_password')
        p2 = cleaned.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return cleaned


# Forms for school models
from school.models import Institucion, Curso


class InstitucionForm(forms.ModelForm):
    class Meta:
        model = Institucion
        fields = ['nom_inst', 'tip_inst', 'cod_dane_inst', 'dep_inst', 'mun_inst', 'dire_inst', 'tel_inst', 'ema_inst', 'img_inst', 'id_adm']
        labels = {
            'nom_inst': 'Nombre',
            'tip_inst': 'Tipo de institución',
            'cod_dane_inst': 'Código DANE',
            'dep_inst': 'Departamento',
            'mun_inst': 'Municipio',
            'dire_inst': 'Dirección',
            'tel_inst': 'Teléfono',
            'ema_inst': 'Correo',
            'img_inst': 'Imagen/Logo de la institución',
            'id_adm': 'Administrativo',
        }


class InstitucionImageForm(forms.ModelForm):
    class Meta:
        model = Institucion
        fields = ['img_inst']
        labels = {
            'img_inst': 'Imagen/Logo de la institución',
        }


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['grd_cur', 'num_alum_cur', 'cup_disp_cur', 'id_inst']
        labels = {
            'grd_cur': 'Grado',
            'num_alum_cur': 'Número de alumnos',
            'cup_disp_cur': 'Cupos disponibles',
            'id_inst': 'Institución',
        }


from .models import InstitucionRequest


class InstitucionRequestForm(forms.ModelForm):
    class Meta:
        model = InstitucionRequest
        fields = ['nom_inst', 'tip_inst', 'cod_dane_inst', 'dep_inst', 'mun_inst', 'dire_inst', 'tel_inst', 'ema_inst']
        labels = {
            'nom_inst': 'Nombre',
            'tip_inst': 'Tipo de institución',
            'cod_dane_inst': 'Código DANE',
            'dep_inst': 'Departamento',
            'mun_inst': 'Municipio',
            'dire_inst': 'Dirección',
            'tel_inst': 'Teléfono',
            'ema_inst': 'Correo',
        }


class CursoRequestForm(forms.Form):
    MODE_CHOICES = (
        ('primaria', 'Primaria (1-5)'),
        ('secundaria', 'Secundaria (6-11)'),
        ('ambos', 'Ambos (1-11)'),
        ('custom', 'Personalizado'),
    )
    mode = forms.ChoiceField(choices=MODE_CHOICES, initial='primaria')
    sections = forms.IntegerField(min_value=1, max_value=6, initial=3)
    cupos = forms.IntegerField(min_value=0, max_value=500, initial=30)
    start_grade = forms.IntegerField(required=False, min_value=1, max_value=11)
    end_grade = forms.IntegerField(required=False, min_value=1, max_value=11)

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('mode')
        if mode == 'custom':
            if cleaned.get('start_grade') is None or cleaned.get('end_grade') is None:
                raise forms.ValidationError('Para modo personalizado debes indicar grado inicio y fin')
            if cleaned.get('start_grade') > cleaned.get('end_grade'):
                raise forms.ValidationError('Grado inicio no puede ser mayor que grado fin')
        return cleaned


from django.contrib.auth.hashers import make_password
from accounts.models import Administrativo


class AdministrativoForm(forms.ModelForm):
    class Meta:
        model = Administrativo
        fields = ['id_usu', 'num_doc_adm', 'tel_adm', 'dir_adm', 'tip_carg_adm', 'cedula_img', 'foto_perfil']
        labels = {
            'id_usu': 'Usuario (registro)',
            'num_doc_adm': 'Número de documento',
            'tel_adm': 'Teléfono',
            'dir_adm': 'Dirección',
            'tip_carg_adm': 'Cargo/Tipo',
            'cedula_img': 'Cédula (imagen)',
            'foto_perfil': 'Foto de perfil',
        }


class BulkCursoForm(forms.Form):
    MODE_CHOICES = (
        ('primaria', 'Primaria (1-5)'),
        ('secundaria', 'Secundaria (6-11)'),
        ('ambos', 'Ambos (1-11)'),
        ('custom', 'Personalizado'),
    )
    mode = forms.ChoiceField(choices=MODE_CHOICES, label='Modo', initial='primaria')
    sections = forms.IntegerField(label='Secciones por grado', min_value=1, max_value=5, initial=3,
                                  help_text='Número de paralelos por grado (ej: 3 crea -01, -02, -03)')
    cupos = forms.IntegerField(label='Cupos por curso', min_value=0, max_value=500, initial=30,
                               help_text='Número de cupos disponibles que tendrá cada curso creado')
    start_grade = forms.IntegerField(required=False, label='Grado inicio', min_value=1, max_value=11)
    end_grade = forms.IntegerField(required=False, label='Grado fin', min_value=1, max_value=11)

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get('mode')
        start = cleaned.get('start_grade')
        end = cleaned.get('end_grade')
        if mode == 'custom':
            if start is None or end is None:
                raise forms.ValidationError('Para modo personalizado debes indicar grado inicio y fin')
            if start > end:
                raise forms.ValidationError('Grado inicio no puede ser mayor que grado fin')
        return cleaned


class AdminRegistroCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirmar contraseña')
    # Campos administrativos: se permiten subir documentos y datos de contacto
    num_doc_adm = forms.CharField(required=False, label='Número de documento (administrativo)')
    tel_adm = forms.CharField(required=False, label='Teléfono administrativo')
    dir_adm = forms.CharField(required=False, label='Dirección administrativo')
    tip_carg_adm = forms.CharField(required=False, label='Cargo/Tipo')
    cedula_img = forms.ImageField(required=False, label='Imagen de cédula')
    foto_perfil = forms.ImageField(required=False, label='Foto perfil')

    # Campos de acudiente: se usan cuando el rol seleccionado es "acudiente"
    acu_num_doc = forms.CharField(required=False, label='Número de documento (acudiente)')
    acu_tel = forms.CharField(required=False, label='Teléfono acudiente')
    acu_dir = forms.CharField(required=False, label='Dirección acudiente')
    acu_cedula_img = forms.ImageField(required=False, label='Cédula (imagen) acudiente')
    acu_foto_perfil = forms.ImageField(required=False, label='Foto de perfil (acudiente)')

    class Meta:
        model = Registro
        fields = ['nom_usu', 'ape_usu', 'ema_usu', 'id_rol']
        labels = {
            'nom_usu': 'Nombre',
            'ape_usu': 'Apellido',
            'ema_usu': 'Correo',
            'id_rol': 'Rol',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # En edición, no requerir contraseña
        if getattr(self, 'instance', None) and getattr(self.instance, 'pk', None):
            self.fields['password'].required = False
            self.fields['password_confirm'].required = False

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password_confirm')
        # Si se proporciona al menos una, ambas deben existir y coincidir
        if p1 or p2:
            if not p1 or not p2:
                raise forms.ValidationError('Para cambiar la contraseña, completa ambos campos')
            if p1 != p2:
                raise forms.ValidationError('Las contraseñas no coinciden')

        # Validación condicional para acudiente: se requiere número de documento
        rol_obj = cleaned.get('id_rol')
        rol_name = (rol_obj.nom_rol or '').strip().lower() if rol_obj else ''
        if rol_name == 'acudiente':
            if not cleaned.get('acu_num_doc'):
                raise forms.ValidationError('Para rol acudiente, el número de documento es obligatorio')
        return cleaned

    def save(self, commit=True, files=None):
        instance = super().save(commit=False)
        pwd = self.cleaned_data.get('password')
        if pwd:
            instance.con_usu = make_password(pwd)
        if commit:
            instance.save()
            # If selected role is administrativo (by name), create Administrativo record
            role = instance.id_rol.nom_rol.lower() if instance.id_rol and instance.id_rol.nom_rol else ''
            if role == 'administrativo' or role == 'administrador':
                # if an Administrativo already exists for this Registro, update it; otherwise create
                adm = Administrativo.objects.filter(id_usu=instance).first()
                if adm:
                    adm.num_doc_adm = self.cleaned_data.get('num_doc_adm') or adm.num_doc_adm
                    adm.tel_adm = self.cleaned_data.get('tel_adm') or adm.tel_adm
                    adm.dir_adm = self.cleaned_data.get('dir_adm') or adm.dir_adm
                    adm.tip_carg_adm = self.cleaned_data.get('tip_carg_adm') or adm.tip_carg_adm
                else:
                    adm = Administrativo(
                        num_doc_adm=self.cleaned_data.get('num_doc_adm') or '',
                        tel_adm=self.cleaned_data.get('tel_adm') or '',
                        dir_adm=self.cleaned_data.get('dir_adm') or '',
                        tip_carg_adm=self.cleaned_data.get('tip_carg_adm') or '',
                        id_usu=instance,
                    )
                # handle uploaded files if provided
                if files:
                    ced = files.get('cedula_img')
                    foto = files.get('foto_perfil')
                    if ced:
                        adm.cedula_img = ced
                    if foto:
                        adm.foto_perfil = foto
                adm.save()

            # Si el rol seleccionado es acudiente, crear/actualizar su objeto Acudiente
            if role == 'acudiente':
                from people.models import Acudiente
                acu = Acudiente.objects.filter(id_usu=instance).first()
                if acu:
                    acu.num_doc_acu = self.cleaned_data.get('acu_num_doc') or acu.num_doc_acu
                    acu.tel_acu = self.cleaned_data.get('acu_tel') or acu.tel_acu
                    acu.dir_acu = self.cleaned_data.get('acu_dir') or acu.dir_acu
                else:
                    # num_doc_acu es obligatorio para crear
                    acu = Acudiente(
                        num_doc_acu=self.cleaned_data.get('acu_num_doc') or '',
                        tel_acu=self.cleaned_data.get('acu_tel') or '',
                        dir_acu=self.cleaned_data.get('acu_dir') or '',
                        id_usu=instance,
                    )
                if files:
                    ced_a = files.get('acu_cedula_img')
                    foto_a = files.get('acu_foto_perfil')
                    if ced_a:
                        acu.cedula_img = ced_a
                    if foto_a:
                        acu.foto_perfil = foto_a
                acu.save()
        return instance
