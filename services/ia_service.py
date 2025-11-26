from openai import OpenAI
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, time

class AnalizadorDespachoIA:
    """Servicio simple de IA para analizar despachos con incidencias"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def analizar_incidencia(self, despacho):
        """
        Analiza un despacho con incidencia y sugiere acción
        
        Args:
            despacho: Objeto Despacho de Django
            
        Returns:
            dict con 'resumen' y 'sugerencia'
        """
        # Verificar cache
        cache_key = f'ia_despacho_{despacho.id}'
        resultado_cache = cache.get(cache_key)
        if resultado_cache:
            return resultado_cache
        
        # Preparar datos del despacho
        estado = despacho.estado or "Desconocido"
        prioridad = despacho.prioridad or "media"
        tipo_incidencia = despacho.tipo_incidencia or "Sin especificar"
        descripcion_incidencia = despacho.descripcion_incidencia or "Sin detalles"
        
        # Calcular tiempo transcurrido
        tiempo_transcurrido = self._calcular_tiempo_transcurrido(despacho)
        
        # Obtener horario de cierre de la farmacia origen
        horario_cierre = self._obtener_horario_cierre(despacho)
        hora_actual = datetime.now().time()
        
        # Construir prompt
        prompt = f"""Eres un asistente de logística farmacéutica. Analiza esta situación:

DESPACHO: {despacho.codigo_despacho}
Estado: {estado}
Prioridad: {prioridad}
Tipo de incidencia: {tipo_incidencia}
Descripción: {descripcion_incidencia}
Tiempo en ruta: {tiempo_transcurrido}
Hora actual: {hora_actual.strftime('%H:%M')}
Farmacia cierra: {horario_cierre.strftime('%H:%M')}

TAREA:
1. Resume la situación en máximo 2 líneas
2. Sugiere UNA acción: "Reasignar" si hay tiempo antes del cierre, o "Postergar" si no alcanza

FORMATO (usa exactamente este):
Resumen: [tu resumen aquí]
Sugerencia: [Reasignar o Postergar]"""

        try:
            # Llamar a OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Modelo más económico para beta
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            # Procesar respuesta
            contenido = response.choices[0].message.content.strip()
            resultado = self._parsear_respuesta(contenido)
            
            # Guardar en cache por 1 hora
            cache.set(cache_key, resultado, 3600)
            
            return resultado
            
        except Exception as e:
            return {
                'resumen': f'Error al analizar con IA: {str(e)}',
                'sugerencia': 'Error',
                'error': True
            }
    
    def _calcular_tiempo_transcurrido(self, despacho):
        """Calcula el tiempo transcurrido del despacho"""
        if despacho.fecha_salida_farmacia:
            delta = datetime.now() - despacho.fecha_salida_farmacia.replace(tzinfo=None)
            minutos = int(delta.total_seconds() / 60)
            if minutos < 60:
                return f"{minutos} minutos"
            else:
                horas = minutos // 60
                mins = minutos % 60
                return f"{horas}h {mins}min"
        return "Tiempo no disponible"
    
    def _obtener_horario_cierre(self, despacho):
        """Obtiene el horario de cierre de la farmacia origen"""
        try:
            from ..models import Localfarmacia
            farmacia = Localfarmacia.objects.get(local_id=despacho.farmacia_origen_local_id)
            return farmacia.funcionamiento_hora_cierre
        except:
            return time(20, 0)  # Default 20:00
    
    def _parsear_respuesta(self, contenido):
        """Parsea la respuesta de la IA al formato esperado"""
        lineas = contenido.split('\n')
        resumen = ""
        sugerencia = ""
        
        for linea in lineas:
            if linea.startswith('Resumen:'):
                resumen = linea.replace('Resumen:', '').strip()
            elif linea.startswith('Sugerencia:'):
                sugerencia = linea.replace('Sugerencia:', '').strip()
        
        return {
            'resumen': resumen or contenido,
            'sugerencia': sugerencia or 'Revisar manualmente',
            'error': False
        }