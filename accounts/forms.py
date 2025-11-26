from django import forms
from .models import Registro
from django.forms import ClearableFileInput
import re


class RegistroForm(forms.ModelForm):
    con_usu = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'password'}), label='Contraseña')
    con_usu_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'id': 'password_confirm'}), label='Confirmar contraseña')
    # Acudiente extra fields
    num_doc_acu = forms.CharField(max_length=20, required=True, label='Número de documento')
    tel_acu = forms.CharField(max_length=20, required=False, label='Teléfono')
    dir_acu = forms.CharField(max_length=100, required=False, label='Dirección')
    cedula_img = forms.ImageField(required=True, widget=ClearableFileInput, label='Foto de la cédula')
    foto_perfil = forms.ImageField(required=False, widget=ClearableFileInput, label='Foto de perfil')

    class Meta:
        model = Registro
        fields = ('nom_usu', 'ape_usu', 'ema_usu', 'con_usu')

    def clean(self):
        cleaned = super().clean()
        a = cleaned.get('con_usu')
        b = cleaned.get('con_usu_confirm')
        if a and b and a != b:
            raise forms.ValidationError('Las contraseñas no coinciden')
        # enforce password policy: min length 8 and at least one special character
        if a:
            if len(a) < 8:
                raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres')
            if not re.search(r"[!@#$%^&*()_+\-=[\]{};':\"\\|,.<>/?]+", a):
                raise forms.ValidationError('La contraseña debe incluir al menos un carácter especial (ej. !@#$%)')
        return cleaned


class LoginForm(forms.Form):
    # Accept either email or document number
    email = forms.CharField(label='Correo o documento', max_length=100)
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')


class StudentRegistrationForm(forms.Form):
    nom_usu = forms.CharField(label='Nombre', max_length=50,
                              widget=forms.TextInput(attrs={'placeholder': 'Nombres', 'autocomplete': 'given-name'}))
    ape_usu = forms.CharField(label='Apellidos', max_length=50,
                              widget=forms.TextInput(attrs={'placeholder': 'Apellidos', 'autocomplete': 'family-name'}))
    num_doc_est = forms.CharField(label='Número de documento', max_length=20,
                                  widget=forms.TextInput(attrs={'placeholder': 'Número de documento', 'autocomplete': 'off'}))
    fch_nac_estu = forms.DateField(label='Fecha de nacimiento', required=False,
                                   widget=forms.DateInput(attrs={'type': 'date', 'autocomplete': 'bday'}))
    tel_estu = forms.CharField(label='Teléfono', max_length=20, required=False,
                               widget=forms.TextInput(attrs={'placeholder': 'Teléfono', 'autocomplete': 'tel'}))
    ema_usu = forms.EmailField(label='Correo electrónico (opcional)', required=False,
                               widget=forms.EmailInput(attrs={'placeholder': 'Correo (opcional)', 'autocomplete': 'email'}))
    con_usu = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña', 'autocomplete': 'new-password', 'id': 'password'}))
    foto_perfil = forms.ImageField(label='Foto de perfil (opcional)', required=False,
                                   widget=ClearableFileInput(attrs={'accept': 'image/*'}))

    def clean_fch_nac_estu(self):
        # If provided, ensure age between 7 and 20
        f = self.cleaned_data.get('fch_nac_estu')
        if f:
            from datetime import date
            today = date.today()
            age = today.year - f.year - ((today.month, today.day) < (f.month, f.day))
            if age < 0:
                raise forms.ValidationError('Fecha de nacimiento inválida')
            if age < 7 or age > 20:
                raise forms.ValidationError('La edad del estudiante debe estar entre 7 y 20 años')
        return f


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label='Correo registrado', max_length=100, widget=forms.EmailInput(attrs={'placeholder': 'Tu correo', 'autocomplete': 'email'}))

    def clean_email(self):
        # No revelar si existe o no; devolver siempre normal
        return self.cleaned_data['email'].strip().lower()


class PasswordResetConfirmForm(forms.Form):
    new_password = forms.CharField(label='Nueva contraseña', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    confirm_password = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    def clean(self):
        cleaned = super().clean()
        a = cleaned.get('new_password')
        b = cleaned.get('confirm_password')
        if a and b and a != b:
            raise forms.ValidationError('Las contraseñas no coinciden')
        if a and len(a) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres')
        return cleaned
