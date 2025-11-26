import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 3306))
server_socket.listen(1)
print("Servidor escuchando en puerto 3600...")

conn, addr = server_socket.accept()
print(f"Conexión establecida desde {addr}")




import openai
from django.conf import settings
from django.core.cache import cache

import os
import sys
import django

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from django.apps import AppConfig
from django.db.models.signals import post_migrate

def cargar_datos(sender, **kwargs):
    # Código que accede a la DB aquí, seguro porque se llama luego de migraciones
    pass

class MiAppConfig(AppConfig):
    name = 'appnproylogico'

    def ready(self):
        post_migrate.connect(cargar_datos, sender=self)


# Define la variable de entorno con el módulo de settings de tu proyecto Django
#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nproylogico.settings')  # Cambia con el path correcto

# Inicializa Django para que settings esté disponible
django.setup()

openai.api_key = settings.OPENAI_API_KEY

def analizar_incidencia(despacho, horario_cierre="20:00"):
    cache_key = f'ia_analisis_{despacho.id}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    estado = despacho.estado_actual or "Desconocido"
    prioridad = despacho.prioridad or "No definida"
    tiempo = despacho.tiempo_transcurrido or "No disponible"
    ultima_incidencia = despacho.ultima_incidencia or "Sin detalles"

    prompt = f"""
Eres un asistente especializado en gestión logística de despachos farmacéuticos.

Datos del despacho:
- ID despacho: {despacho.id}
- Estado actual: {estado}
- Prioridad: {prioridad}
- Tiempo transcurrido en ruta: {tiempo}
- Descripción de la incidencia: {ultima_incidencia}

Importante:
La farmacia cierra a las {horario_cierre} horas.

Tarea:
1. Resume en dos líneas la situación actual del despacho.
2. Basado en la descripción y tiempo, elige UNA y solo UNA acción recomendada según las siguientes reglas:
   - "Reasignar/Reenviar": si es factible realizar la acción antes del horario de cierre para garantizar la entrega a tiempo.
   - "Postergar": si no hay tiempo suficiente para reenviar hoy y debe realizarse después del horario de cierre o al día siguiente.

Formato de respuesta:
Resumen: <tu resumen>
Sugerencia: <Reasignar/Reenviar o Postergar>

Solo devuelve la respuesta en ese formato.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            request_timeout=10
        )
        resultado = response.choices[0].message.content.strip()
        cache.set(cache_key, resultado, 3600)  # cache 1 hora
        return resultado
    except Exception as e:
        return f"Error al analizar: {str(e)}"


