import json
import pathlib
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Genera archivos JSON masivos en static/data para motoristas, motos y asignaciones'

    def handle(self, *args, **options):
        base = pathlib.Path(__file__).resolve().parents[3] / 'static' / 'data'
        base.mkdir(parents=True, exist_ok=True)
        now = timezone.now()

        nombres_fuente = [
            'Hayley Williams','Jeremy Davis','Taylor York','Josh Farro','Zac Farro','Thom Yorke','Jonny Greenwood','Colin Greenwood','Ed Obrien','Phil Selway',
            'Chester Bennington','Mike Shinoda','Brad Delson','Dave Farrell','Rob Bourdon','Joe Hahn','Billie Joe Armstrong','Mike Dirnt','Tre Cool',
            'Mark Hoppus','Tom DeLonge','Travis Barker','Timo Kotipelto','Jens Johansson','Matias Kupiainen','Jorg Michael','Corey Taylor','Jim Root',
            'Mick Thomson','Shawn Crahan','Sid Wilson','Alessandro Venturella','Jay Weinberg','Roberto Musso','Santiago Tavella','Alvaro Pintos','Gustavo Antuna',
            'Yamilet Safdie','Camilo Echeverry','Juan Pablo Isaza','Martin Vargas','Simon Vargas','Amaia Montero','Pablo Benegas','Alvaro Fuentes','Haritz Garde',
            'Pablo Holman','Barbaro Gatica','Kuky Neira','Jorge Gonzalez','Claudio Narea','Miguel Tapia','Omar Montes','Victor Elias','Royel Otis','Benson Boone',
            'Balu Brigada','Myles Smith','Sawyer Hill','Flipturn','Black Mountain','Brian Jonestown','BadBadNotGood','Blues Pills','Ben Harper','Bauhaus Ness',
            'Jon Bon Jovi','Bruce Springsteen','Kele Okereke','Stuart Braithwaite','Courtney Barnett','Camila Moreno','Chris Martin','Jason Newsted','Lars Ulrich',
            'Dave Mustaine','Matt Bellamy','Josh Homme','Dave Grohl'
        ]

        # Motoristas.json (200)
        motoristas = []
        for i in range(200):
            nombre_completo = nombres_fuente[i % len(nombres_fuente)]
            partes = nombre_completo.split()
            nombre = partes[0]
            apellido = ' '.join(partes[1:]) if len(partes) > 1 else 'Demo'
            motoristas.append({
                "nombre": nombre,
                "apellido": apellido,
                "activo": 1
            })
        (base / 'motoristas.json').write_text(json.dumps(motoristas, ensure_ascii=False, indent=2), encoding='utf-8')

        # Motos.json (210: 200 activas, 10 inactivas)
        motos = []
        for i in range(210):
            idx = i + 1
            patente = f"PX{idx:04d}"
            activo = True if i < 200 else False
            motos.append({
                "patente": patente,
                "marca": "GENERICA",
                "modelo": "STD",
                "activo": activo
            })
        (base / 'motos.json').write_text(json.dumps(motos, ensure_ascii=False, indent=2), encoding='utf-8')

        # Asignaciones moto-motorista (200 activas)
        asign = []
        fecha_iso = now.strftime('%Y-%m-%dT08:00:00')
        for i in range(200):
            nombre_completo = nombres_fuente[i % len(nombres_fuente)]
            patente = f"PX{(i+1):04d}"
            asign.append({
                "motorista": nombre_completo,
                "moto": patente,
                "fecha_asignacion": fecha_iso,
                "activa": 1
            })
        (base / 'asignaciones_moto_motorista.json').write_text(json.dumps(asign, ensure_ascii=False, indent=2), encoding='utf-8')

        self.stdout.write(self.style.SUCCESS(f'Archivos JSON generados en {base}'))
