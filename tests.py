from django.test import TestCase
from appnproylogico.forms import RegistroForm, DespachoForm


class RegistroFormEmailTest(TestCase):
    def test_email_requires_corporate_for_non_admin(self):
        data = {
            'username': 'usuario1',
            'email': 'user@example.com',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'tipo_documento': 'DNI_EXTRANJERO',
            'documento_identidad': 'ABC12345',
            'consiente_datos_salud': True,
        }
        form = RegistroForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_email_corporate_valid(self):
        data = {
            'username': 'usuario2',
            'email': 'user@discopro.cl',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'tipo_documento': 'DNI_EXTRANJERO',
            'documento_identidad': 'ABC12345',
            'consiente_datos_salud': True,
        }
        form = RegistroForm(data=data)
        # Puede fallar por otros campos (p.ej. username duplicado), pero email no debe fallar
        form.is_valid()
        assert 'email' not in form.errors


class DespachoFormChoicesTest(TestCase):
    def test_estado_choices_include_preparacion(self):
        form = DespachoForm()
        estados = [c[0] for c in form.fields['estado'].widget.choices]
        assert 'PREPARANDO' in estados
        assert 'PREPARADO' in estados
