from django.core.management.base import BaseCommand
from appnproylogico.models import Despacho
from appnproylogico.services.ia_service import AnalizadorDespachoIA

class Command(BaseCommand):
    help = 'Prueba el servicio de IA con despachos que tienen incidencia'

    def handle(self, *args, **options):
        # Buscar despachos con incidencia
        despachos = Despacho.objects.filter(hubo_incidencia=True)[:3]
        
        if not despachos.exists():
            self.stdout.write(self.style.WARNING('No hay despachos con incidencia para analizar'))
            return
        
        analizador = AnalizadorDespachoIA()
        
        for despacho in despachos:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'Analizando: {despacho.codigo_despacho}')
            self.stdout.write(f'Estado: {despacho.estado}')
            self.stdout.write(f'Incidencia: {despacho.tipo_incidencia}')
            
            resultado = analizador.analizar_incidencia(despacho)
            
            if resultado.get('error'):
                self.stdout.write(self.style.ERROR(f"Error: {resultado['resumen']}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"\nResumen: {resultado['resumen']}"))
                self.stdout.write(self.style.SUCCESS(f"Sugerencia: {resultado['sugerencia']}"))
        
        self.stdout.write(f'\n{"="*60}\n')
        self.stdout.write(self.style.SUCCESS('Análisis completado'))