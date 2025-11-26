from django.apps import AppConfig
import sys


class AppnproylogicoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appnproylogico'

    def ready(self):
        try:
            args = set(sys.argv or [])
            if any(a in args for a in {'makemigrations','migrate','collectstatic','test'}):
                return
            from django.core.management import call_command
            from django.apps import apps
            Moto = apps.get_model('appnproylogico','Moto')
            Localfarmacia = apps.get_model('appnproylogico','Localfarmacia')
            Motorista = apps.get_model('appnproylogico','Motorista')
            from django.db import OperationalError
            try:
                motos = Moto.objects.count()
                farm = Localfarmacia.objects.count()
                mots = Motorista.objects.count()
            except OperationalError:
                return
            if motos < 56 or farm == 0 or mots == 0:
                try:
                    call_command('load_samples')
                except Exception:
                    pass
        except Exception:
            pass
