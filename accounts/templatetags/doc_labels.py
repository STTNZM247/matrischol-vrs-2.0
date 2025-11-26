from django import template

register = template.Library()

LABELS = {
    'reg_civil_doc': 'Registro civil',
    'doc_idn_acu': 'Documento del acudiente',
    'doc_idn_alum': 'Documento del estudiante',
    'cnt_vac_doc': 'Constancia de vacunas',
    'adres_doc': 'Dirección / comprobante',
    'fot_alum_doc': 'Foto del estudiante',
    'visa_extr_doc': 'Visa o permiso de estancia',
    'cer_med_disca_doc': 'Certificado médico / discapacidad',
    'cer_esc_doc': 'Certificado escolar',
}

@register.filter
def doc_label(key):
    """Convierte el nombre interno del campo a una etiqueta legible para el usuario."""
    if not key:
        return ''
    return LABELS.get(key, key.replace('_', ' ').capitalize())

@register.filter
def doc_labels_list(keys):
    """Devuelve una lista de etiquetas legibles dada una lista de keys."""
    if not keys:
        return []
    return [LABELS.get(k, k.replace('_', ' ').capitalize()) for k in keys]
