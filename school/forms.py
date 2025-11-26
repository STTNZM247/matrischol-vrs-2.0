from django import forms


class DocumentoUploadForm(forms.Form):
    reg_civil_doc = forms.FileField(required=False, label='Registro civil')
    doc_idn_acu = forms.FileField(required=False, label='Documento acudiente')
    doc_idn_alum = forms.FileField(required=False, label='Documento alumno')
    cnt_vac_doc = forms.FileField(required=False, label='Constancia de vacunas')
    fot_alum_doc = forms.FileField(required=False, label='Foto del alumno')
    visa_extr_doc = forms.FileField(required=False, label='Visa o permiso (opcional)')
    cer_med_disca_doc = forms.FileField(required=False, label='Certificado médico/discapacidad')
    cer_esc_doc = forms.FileField(required=False, label='Certificado escolar')
    # permitir también enviar la dirección como texto (comprobante o solo texto)
    adres_text = forms.CharField(required=False, label='Dirección (texto)', max_length=200)

    def files_present(self):
        """Return a dict of uploaded files (only the ones present)."""
        return {k: v for k, v in self.files.items() if v}
