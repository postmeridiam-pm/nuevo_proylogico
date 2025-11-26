import json
import pathlib
from datetime import date, time
from django.utils import timezone

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User

from ...models import Localfarmacia, Moto, Motorista, Usuario, Rol, AsignacionMotoMotorista, AsignacionMotoristaFarmacia, Despacho


class Command(BaseCommand):
    help = 'Carga datos de ejemplo desde static/data/*.json'

    def add_arguments(self, parser):
        parser.add_argument('--dir', type=str, default=None, help='Directorio de datos (por defecto static/data)')

    def handle(self, *args, **options):
        base = pathlib.Path(__file__).resolve().parents[3] / 'static' / 'data'
        if options.get('dir'):
            base = pathlib.Path(options['dir']).resolve()
        self.stdout.write(self.style.NOTICE(f'Usando carpeta de datos: {base}'))

        # Ejecutar por lote para evitar que un error anule todo
        farmacias_c = self._load_farmacias(base)
        motos_c = self._load_motos(base)
        motoristas_c = self._load_motoristas(base)
        asign_moto_c = self._load_asignaciones_moto_motorista(base)
        asign_farma_c = self._load_asignaciones_motorista_farmacia(base)
        despachos_c = self._load_despachos(base)
        movimientos_c = self._load_movimientos(base)

        self.stdout.write(self.style.SUCCESS(f'Farmacias creadas/actualizadas: {farmacias_c}'))
        self.stdout.write(self.style.SUCCESS(f'Motos creadas/actualizadas: {motos_c}'))
        self.stdout.write(self.style.SUCCESS(f'Motoristas creados/actualizados: {motoristas_c}'))
        self.stdout.write(self.style.SUCCESS(f'Asignaciones Moto–Motorista creadas/actualizadas: {asign_moto_c}'))
        self.stdout.write(self.style.SUCCESS(f'Asignaciones Motorista–Farmacia creadas/actualizadas: {asign_farma_c}'))
        self.stdout.write(self.style.SUCCESS(f'Despachos creados/actualizados: {despachos_c}'))
        self.stdout.write(self.style.SUCCESS(f'Movimientos creados: {movimientos_c}'))

    def _iter_files(self, base: pathlib.Path, prefix: str):
        for p in sorted(base.glob(f'{prefix}*.json')):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    yield p.name, json.load(f)
            except Exception:
                continue

    def _load_farmacias(self, base: pathlib.Path) -> int:
        count = 0
        for name, data in self._iter_files(base, 'farmacias'):
            for d in (data or []):
                lid = (d.get('local_id') or d.get('id') or '').strip()
                if not lid:
                    continue
                obj = Localfarmacia.objects.filter(local_id=lid).first()
                now_dt = timezone.now()
                defaults = {
                    'local_nombre': d.get('local_nombre') or d.get('nombre') or f'Farmacia {lid}',
                    'local_direccion': d.get('local_direccion') or d.get('direccion') or 'Por definir',
                    'comuna_nombre': d.get('comuna_nombre') or d.get('comuna') or '',
                    'localidad_nombre': d.get('localidad_nombre') or d.get('localidad') or '',
                    'funcionamiento_hora_apertura': self._parse_time(d.get('funcionamiento_hora_apertura')) or time(9, 0),
                    'funcionamiento_hora_cierre': self._parse_time(d.get('funcionamiento_hora_cierre')) or time(18, 0),
                    'funcionamiento_dia': d.get('funcionamiento_dia') or 'lun-vie',
                    'local_telefono': d.get('local_telefono') or '',
                    'local_lat': self._parse_decimal(d.get('local_lat')),
                    'local_lng': self._parse_decimal(d.get('local_lng')),
                    'geolocalizacion_validada': bool(d.get('geolocalizacion_validada') or False),
                    'fecha': self._parse_date(d.get('fecha') or d.get('fecha_actualizacion')) or date.today(),
                    'activo': bool(d.get('activo') if d.get('activo') is not None else True),
                    'fecha_creacion': now_dt,
                    'fecha_modificacion': now_dt,
                    'usuario_modificacion': None,
                }
                try:
                    if obj:
                        for k, v in defaults.items():
                            setattr(obj, k, v)
                        obj.save()
                    else:
                        obj = Localfarmacia(local_id=lid, **defaults)
                        obj.save()
                    count += 1
                except Exception as e:
                    try:
                        self.stdout.write(self.style.WARNING(f'Error creando/actualizando farmacia {lid}: {e}'))
                    except Exception:
                        pass
                    continue
        return count

    def _load_motos(self, base: pathlib.Path) -> int:
        count = 0
        for name, data in self._iter_files(base, 'motos'):
            for d in (data or []):
                pat = (str(d.get('patente') or '').upper()).strip()
                if not pat:
                    continue
                obj = Moto.objects.filter(patente=pat).first()
                now_dt = timezone.now()
                defaults = {
                    'propietario_nombre': d.get('propietario_nombre') or 'LOGICO SPA',
                    'propietario_tipo_documento': d.get('propietario_tipo_documento') or 'RUT',
                    'propietario_documento': d.get('propietario_documento') or f'RUT-{pat}',
                    'anio': int(d.get('anio') or 2020),
                    'cilindrada_cc': int(d.get('cilindrada_cc') or 150),
                    'color': d.get('color') or 'NEGRO',
                    'marca': d.get('marca') or 'GENERICA',
                    'modelo': d.get('modelo') or 'STD',
                    'tipo_combustible': (d.get('tipo_combustible') or 'GASOLINA').upper(),
                    'fecha_inscripcion': self._parse_date(d.get('fecha_inscripcion')) or date(2020, 1, 1),
                    'kilometraje_actual': int(d.get('kilometraje_actual') or 0),
                    'activo': bool(d.get('activo') if d.get('activo') is not None else True),
                    'estado': ('ACTIVO' if (d.get('activo') if d.get('activo') is not None else True) else 'INACTIVO'),
                    'numero_motor': d.get('numero_motor') or f'MOTOR-{pat}',
                    'numero_chasis': d.get('numero_chasis') or f'CHASIS-{pat}',
                    'fecha_creacion': now_dt,
                    'fecha_modificacion': now_dt,
                    'usuario_modificacion': None,
                }
                try:
                    if obj:
                        for k, v in defaults.items():
                            setattr(obj, k, v)
                        obj.save()
                    else:
                        obj = Moto(patente=pat, **defaults)
                        obj.save()
                    count += 1
                except Exception as e:
                    try:
                        self.stdout.write(self.style.WARNING(f'Error creando/actualizando moto {pat}: {e}'))
                    except Exception:
                        pass
                    continue
        # Asegurar al menos 56 motos (3 inactivas)
        try:
            existentes = Moto.objects.count()
            faltan = 56 - existentes
            if faltan > 0:
                now_dt = timezone.now()
                nuevos = []
                for i in range(faltan):
                    idx = existentes + i + 1
                    pat = f"PX{idx:04d}" if idx <= 9999 else f"PX{idx}"
                    if Moto.objects.filter(patente=pat).exists():
                        continue
                    activa_flag = i < max(faltan - 3, 0)
                    nuevos.append(Moto(
                        patente=pat,
                        marca='GENERICA', modelo='STD', tipo_combustible='GASOLINA',
                        fecha_inscripcion=date(2020,1,1), kilometraje_actual=0, activo=activa_flag, estado=('ACTIVO' if activa_flag else 'INACTIVO'),
                        numero_motor=f'MOTOR-{pat}', numero_chasis=f'CHASIS-{pat}',
                        propietario_nombre='LOGICO SPA', propietario_tipo_documento='RUT', propietario_documento=f'RUT-{pat}',
                        anio=2020, cilindrada_cc=150, color='NEGRO', fecha_creacion=now_dt, fecha_modificacion=now_dt,
                        usuario_modificacion=None,
                    ))
                if nuevos:
                    try:
                        Moto.objects.bulk_create(nuevos, ignore_conflicts=True)
                        count += len(nuevos)
                    except Exception:
                        for m in nuevos:
                            try:
                                m.save()
                                count += 1
                            except Exception:
                                pass
        except Exception:
            pass
        return count

    def _load_motoristas(self, base: pathlib.Path) -> int:
        count = 0
        rol = Rol.objects.filter(codigo='motorista').first()
        if not rol:
            now = timezone.now()
            rol = Rol(
                codigo='motorista', nombre='Motorista', django_group_name='Motoristas',
                descripcion='Rol de motorista', activo=1,
                fecha_creacion=now, fecha_modificacion=now,
            )
            try:
                rol.save()
            except Exception:
                pass
        for name, data in self._iter_files(base, 'motoristas'):
            for d in (data or []):
                mid = d.get('id') or d.get('usuario_id') or None
                nombre = d.get('nombre') or 'Motorista'
                apellido = d.get('apellido') or str(mid or '')
                username = f"motorista{mid or ''}" or None
                if not username:
                    continue
                user = User.objects.filter(username=username).first()
                if not user:
                    user = User.objects.create_user(username=username, password='TempPass123!', first_name=nombre, last_name=apellido)
                usuario = Usuario.objects.filter(django_user_id=user.id).first()
                if not usuario:
                    now = timezone.now()
                    usuario = Usuario(
                        rol=rol,
                        django_user_id=user.id,
                        tipo_documento='DNI',
                        documento_identidad=f'MOT-{user.id}',
                        nombre=user.first_name or nombre,
                        apellido=user.last_name or apellido,
                        telefono=None,
                        activo=1,
                        fecha_creacion=now,
                        fecha_modificacion=now,
                        usuario_modificacion=None,
                        )
                    usuario.save()
                mot = Motorista.objects.filter(usuario=usuario).first()
                now_dt = timezone.now()
                defaults = {
                    'licencia_numero': d.get('licencia_numero') or f'L-{user.id}',
                    'licencia_clase': d.get('licencia_clase') or 'A',
                    'fecha_vencimiento_licencia': self._parse_date(d.get('fecha_vencimiento_licencia')) or date(2026, 1, 1),
                    'emergencia_nombre': d.get('emergencia_nombre') or 'Contacto',
                    'emergencia_telefono': d.get('emergencia_telefono') or '+56900000000',
                    'emergencia_parentesco': d.get('emergencia_parentesco') or 'Otro',
                    'total_entregas_completadas': int(d.get('total_entregas_completadas') or 0),
                    'total_entregas_fallidas': int(d.get('total_entregas_fallidas') or 0),
                    'activo': 1 if (d.get('activo') is None or d.get('activo')) else 0,
                    'disponible_hoy': 1 if d.get('disponible_hoy') else 0,
                }
                try:
                    if mot:
                        for k, v in defaults.items():
                            setattr(mot, k, v)
                        mot.fecha_modificacion = now_dt
                        mot.save()
                    else:
                        mot = Motorista(usuario=usuario, fecha_creacion=now_dt, fecha_modificacion=now_dt, usuario_modificacion=None, **defaults)
                        mot.save()
                    count += 1
                except Exception as e:
                    try:
                        self.stdout.write(self.style.WARNING(f'Error creando/actualizando motorista {username}: {e}'))
                    except Exception:
                        pass
                    continue
        return count

    def _load_asignaciones_moto_motorista(self, base: pathlib.Path) -> int:
        count = 0
        # Crea motoristas y motos faltantes basados en asignaciones
        for name, data in self._iter_files(base, 'asignaciones_moto_motorista'):
            for d in (data or []):
                try:
                    mot_nombre = str(d.get('motorista') or '').strip()
                    pat = (str(d.get('moto') or '').upper()).strip()
                    if not mot_nombre or not pat:
                        continue
                    # Asegurar moto
                    moto = Moto.objects.filter(patente=pat).first()
                    if not moto:
                        now_dt = timezone.now()
                        moto = Moto(
                            patente=pat,
                            marca='GENERICA', modelo='STD', tipo_combustible='BENCINA',
                            fecha_inscripcion=date(2020,1,1), kilometraje_actual=0, activo=True,
                            numero_motor=f'MOTOR-{pat}', numero_chasis=f'CHASIS-{pat}',
                            propietario_nombre='LOGICO SPA', propietario_tipo_documento='RUT', propietario_documento=f'RUT-{pat}',
                            anio=2020, cilindrada_cc=150, color='NEGRO', fecha_creacion=now_dt, fecha_modificacion=now_dt,
                            usuario_modificacion=None,
                        )
                        moto.save()
                    # Asegurar motorista
                    parts = mot_nombre.split()
                    nombre = parts[0]
                    apellido = ' '.join(parts[1:]) if len(parts) > 1 else 'Demo'
                    user = User.objects.filter(first_name=nombre, last_name=apellido).first()
                    if not user:
                        uname = f"mot_{nombre.lower()}_{apellido.lower().replace(' ','_')}"
                        user = User.objects.create_user(username=uname, password='TempPass123!', first_name=nombre, last_name=apellido)
                    rol = Rol.objects.filter(codigo='motorista').first()
                    if not rol:
                        now = timezone.now()
                        rol = Rol(codigo='motorista', nombre='Motorista', django_group_name='Motoristas', descripcion='Rol de motorista', activo=1, fecha_creacion=now, fecha_modificacion=now)
                        try:
                            rol.save()
                        except Exception:
                            pass
                    usuario = Usuario.objects.filter(django_user_id=user.id).first()
                    if not usuario:
                        now = timezone.now()
                        usuario = Usuario(rol=rol, django_user_id=user.id, tipo_documento='DNI', documento_identidad=f'MOT-{user.id}', nombre=nombre, apellido=apellido, activo=1, fecha_creacion=now, fecha_modificacion=now)
                        usuario.save()
                    motorista = Motorista.objects.filter(usuario=usuario).first()
                    if not motorista:
                        now_dt = timezone.now()
                        motorista = Motorista(usuario=usuario, licencia_numero=f'L-{user.id}', licencia_clase='A', fecha_vencimiento_licencia=date(2026,1,1), emergencia_nombre='Contacto', emergencia_telefono='+56900000000', emergencia_parentesco='Otro', total_entregas_completadas=0, total_entregas_fallidas=0, activo=1, disponible_hoy=1, fecha_creacion=now_dt, fecha_modificacion=now_dt)
                        motorista.save()
                    # Crear/actualizar asignación
                    fecha_asig = self._parse_date(d.get('fecha_asignacion')) or date.today()
                    activa = 1 if d.get('activa') else 0
                    asign = AsignacionMotoMotorista.objects.filter(motorista=motorista, moto=moto, fecha_asignacion__date=fecha_asig).first()
                    if asign:
                        asign.activa = activa
                        asign.save()
                    else:
                        asign = AsignacionMotoMotorista(motorista=motorista, moto=moto, fecha_asignacion=timezone.make_aware(timezone.datetime.combine(fecha_asig, time(8,0))), activa=activa, kilometraje_inicio=0, observaciones=None)
                        asign.save()
                    count += 1
                except Exception:
                    continue
        return count

    def _load_asignaciones_motorista_farmacia(self, base: pathlib.Path) -> int:
        count = 0
        for name, data in self._iter_files(base, 'asignaciones_motorista_farmacia'):
            for d in (data or []):
                try:
                    mot_nombre = str(d.get('motorista') or '').strip()
                    farm_str = str(d.get('farmacia') or '').strip()
                    if not mot_nombre or not farm_str:
                        continue
                    # Extraer local_id desde paréntesis: "Nombre (F001)"
                    local_id = None
                    if '(' in farm_str and ')' in farm_str:
                        try:
                            local_id = farm_str.split('(')[-1].split(')')[0].strip()
                        except Exception:
                            local_id = None
                    farmacia = None
                    if local_id:
                        farmacia = Localfarmacia.objects.filter(local_id=local_id).first()
                    if not farmacia:
                        farmacia = Localfarmacia.objects.filter(local_nombre__icontains=farm_str.split('(')[0].strip()).first()
                    if not farmacia:
                        now_dt = timezone.now()
                        farmacia = Localfarmacia(
                            local_id=local_id or f'F-{abs(hash(farm_str)) % 10000}',
                            local_nombre=farm_str.split('(')[0].strip() or 'Farmacia Demo',
                            local_direccion='Por definir',
                            comuna_nombre='',
                            localidad_nombre='',
                            funcionamiento_hora_apertura=time(9,0),
                            funcionamiento_hora_cierre=time(18,0),
                            funcionamiento_dia='lun-vie',
                            local_telefono='',
                            local_lat=None,
                            local_lng=None,
                            geolocalizacion_validada=False,
                            fecha=date.today(),
                            activo=True,
                            fecha_creacion=now_dt,
                            fecha_modificacion=now_dt,
                            usuario_modificacion=None,
                        )
                        farmacia.save()
                    # Asegurar motorista
                    parts = mot_nombre.split()
                    nombre = parts[0]
                    apellido = ' '.join(parts[1:]) if len(parts) > 1 else 'Demo'
                    user = User.objects.filter(first_name=nombre, last_name=apellido).first()
                    if not user:
                        uname = f"mot_{nombre.lower()}_{apellido.lower().replace(' ','_')}"
                        user = User.objects.create_user(username=uname, password='TempPass123!', first_name=nombre, last_name=apellido)
                    rol = Rol.objects.filter(codigo='motorista').first()
                    if not rol:
                        now = timezone.now()
                        rol = Rol(codigo='motorista', nombre='Motorista', django_group_name='Motoristas', descripcion='Rol de motorista', activo=1, fecha_creacion=now, fecha_modificacion=now)
                        try:
                            rol.save()
                        except Exception:
                            pass
                    usuario = Usuario.objects.filter(django_user_id=user.id).first()
                    if not usuario:
                        now = timezone.now()
                        usuario = Usuario(rol=rol, django_user_id=user.id, tipo_documento='DNI', documento_identidad=f'MOT-{user.id}', nombre=nombre, apellido=apellido, activo=1, fecha_creacion=now, fecha_modificacion=now)
                        usuario.save()
                    motorista = Motorista.objects.filter(usuario=usuario).first()
                    if not motorista:
                        now_dt = timezone.now()
                        motorista = Motorista(usuario=usuario, licencia_numero=f'L-{user.id}', licencia_clase='A', fecha_vencimiento_licencia=date(2026,1,1), emergencia_nombre='Contacto', emergencia_telefono='+56900000000', emergencia_parentesco='Otro', total_entregas_completadas=0, total_entregas_fallidas=0, activo=1, disponible_hoy=1, fecha_creacion=now_dt, fecha_modificacion=now_dt)
                        motorista.save()
                    # Crear/actualizar asignación Motorista–Farmacia
                    fecha_asig_dt = self._parse_datetime(d.get('fecha_asignacion')) or timezone.now()
                    activa = 1 if d.get('activa') else 0
                    asign = AsignacionMotoristaFarmacia.objects.filter(motorista=motorista, farmacia=farmacia).order_by('-fecha_asignacion').first()
                    if asign:
                        asign.activa = activa
                        asign.fecha_desasignacion = None
                        asign.observaciones = None
                        asign.save()
                    else:
                        asign = AsignacionMotoristaFarmacia(motorista=motorista, farmacia=farmacia, fecha_asignacion=fecha_asig_dt, activa=activa, observaciones=None)
                        asign.save()
                    count += 1
                except Exception:
                    continue
        return count

    def _load_despachos(self, base: pathlib.Path) -> int:
        count = 0
        for name, data in self._iter_files(base, 'despachos'):
            for d in (data or []):
                try:
                    codigo = (d.get('codigo_despacho') or '').strip()
                    if not codigo:
                        continue
                    mot = None
                    mid = d.get('motorista_id')
                    if mid:
                        mot = Motorista.objects.filter(id=int(mid)).first()
                    if not mot:
                        # Intentar por nombre anidado {motorista:{nombre,apellido}}
                        try:
                            mn = str((d.get('motorista') or {}).get('nombre') or '').strip()
                            ma = str((d.get('motorista') or {}).get('apellido') or '').strip()
                            if mn:
                                user = User.objects.filter(first_name=mn, last_name=ma).first()
                                if not user:
                                    uname = f"mot_{mn.lower()}_{ma.lower().replace(' ','_')}" if ma else f"mot_{mn.lower()}"
                                    user = User.objects.create_user(username=uname, password='TempPass123!', first_name=mn, last_name=ma)
                                usuario = Usuario.objects.filter(django_user_id=user.id).first()
                                if not usuario:
                                    now = timezone.now()
                                    rol = Rol.objects.filter(codigo='motorista').first()
                                    if not rol:
                                        rol = Rol(codigo='motorista', nombre='Motorista', django_group_name='Motoristas', descripcion='Rol de motorista', activo=1, fecha_creacion=now, fecha_modificacion=now)
                                        try:
                                            rol.save()
                                        except Exception:
                                            pass
                                    usuario = Usuario(rol=rol, django_user_id=user.id, tipo_documento='DNI', documento_identidad=f'MOT-{user.id}', nombre=mn, apellido=ma or 'Demo', activo=1, fecha_creacion=now, fecha_modificacion=now)
                                    usuario.save()
                                mot = Motorista.objects.filter(usuario=usuario).first()
                                if not mot:
                                    now_dt = timezone.now()
                                    mot = Motorista(usuario=usuario, licencia_numero=f'L-{user.id}', licencia_clase='A', fecha_vencimiento_licencia=date(2026,1,1), emergencia_nombre='Contacto', emergencia_telefono='+56900000000', emergencia_parentesco='Otro', total_entregas_completadas=0, total_entregas_fallidas=0, activo=1, disponible_hoy=1, fecha_creacion=now_dt, fecha_modificacion=now_dt)
                                    mot.save()
                        except Exception:
                            pass
                    if not mot:
                        mot = Motorista.objects.order_by('id').first()
                        if not mot:
                            continue
                    # Asegurar usuario_registro
                    usuario_reg = Usuario.objects.order_by('id').first()
                    if not usuario_reg:
                        # Crear usuario operadora demo
                        user = User.objects.filter(username='operadora_demo').first()
                        if not user:
                            user = User.objects.create_user(username='operadora_demo', password='TempPass123!', first_name='Operadora', last_name='Demo')
                        rol_op = Rol.objects.filter(codigo='operador').first()
                        if not rol_op:
                            now = timezone.now()
                            rol_op = Rol(codigo='operador', nombre='Operador', django_group_name='Operadores', descripcion='Rol de operador', activo=1, fecha_creacion=now, fecha_modificacion=now)
                            try:
                                rol_op.save()
                            except Exception:
                                pass
                        usuario_reg = Usuario.objects.filter(django_user_id=user.id).first()
                        if not usuario_reg:
                            now = timezone.now()
                            usuario_reg = Usuario(rol=rol_op, django_user_id=user.id, tipo_documento='DNI', documento_identidad=f'OP-{user.id}', nombre='Operadora', apellido='Demo', activo=1, fecha_creacion=now, fecha_modificacion=now)
                            usuario_reg.save()
                    # Crear/actualizar despacho
                    obj = Despacho.objects.filter(codigo_despacho=codigo).first()
                    now_dt = timezone.now()
                    defaults = {
                        'farmacia_origen_local_id': (d.get('farmacia_origen_local_id') or 'F001'),
                        'farmacia_destino_local_id': d.get('farmacia_destino_local_id') or None,
                        'motorista': mot,
                        'estado': (d.get('estado') or 'PENDIENTE').upper(),
                        'tipo_despacho': (d.get('tipo_despacho') or 'DOMICILIO').upper(),
                        'prioridad': (d.get('prioridad') or 'MEDIA').upper(),
                        'cliente_nombre': d.get('cliente_nombre') or None,
                        'cliente_telefono': d.get('cliente_telefono') or None,
                        'destino_direccion': d.get('destino_direccion') or 'Por definir',
                        'destino_referencia': d.get('destino_referencia') or None,
                        'destino_lat': self._parse_decimal(d.get('destino_lat')),
                        'destino_lng': self._parse_decimal(d.get('destino_lng')),
                        'destino_geolocalizacion_validada': bool(d.get('destino_geolocalizacion_validada') or False),
                        'tiene_receta_retenida': bool(d.get('tiene_receta_retenida') or False),
                        'numero_receta': d.get('numero_receta') or None,
                        'requiere_devolucion_receta': bool(d.get('requiere_devolucion_receta') or False),
                        'receta_devuelta_farmacia': bool(d.get('receta_devuelta_farmacia') or False),
                        'observaciones_receta': d.get('observaciones_receta') or None,
                        'descripcion_productos': d.get('descripcion_productos') or 'Sin detalle',
                        'valor_declarado': self._parse_decimal(d.get('valor_declarado')),
                        'requiere_aprobacion_operadora': bool(d.get('requiere_aprobacion_operadora') or False),
                        'aprobado_por_operadora': bool(d.get('aprobado_por_operadora') or False),
                        'firma_digital': bool(d.get('firma_digital') or False),
                        'hubo_incidencia': bool(d.get('hubo_incidencia') or False),
                        'usuario_aprobador': None,
                        'fecha_aprobacion': None,
                        'fecha_registro': self._parse_datetime(d.get('fecha_registro')) or now_dt,
                        'fecha_modificacion': now_dt,
                        'usuario_registro': usuario_reg,
                        'usuario_modificacion': usuario_reg,
                    }
                    try:
                        if obj:
                            for k, v in defaults.items():
                                setattr(obj, k, v)
                            obj.save()
                        else:
                            obj = Despacho(codigo_despacho=codigo, **defaults)
                            obj.save()
                        count += 1
                    except Exception as e:
                        try:
                            self.stdout.write(self.style.WARNING(f'Error creando/actualizando despacho {codigo}: {e}'))
                        except Exception:
                            pass
                        continue
                except Exception:
                    continue
        return count

        # Generar datos sintéticos si hay pocos despachos
        try:
            total = Despacho.objects.count()
            objetivo = 30
            if total < objetivo:
                farmacias = list(Localfarmacia.objects.all()[:5])
                motoristas = list(Motorista.objects.all()[:10])
                if not farmacias or not motoristas:
                    return count
                now_dt = timezone.now()
                estados = ['PENDIENTE','EN_CAMINO','ENTREGADO','FALLIDO','ANULADO']
                tipos = ['DOMICILIO','REENVIO_RECETA','INTERCAMBIO','ERROR_DESPACHO']
                prioridad = ['ALTA','MEDIA','BAJA']
                gen = 0
                for i in range(objetivo - total):
                    f = farmacias[i % len(farmacias)]
                    m = motoristas[i % len(motoristas)]
                    est = estados[i % len(estados)]
                    t = tipos[i % len(tipos)]
                    pr = prioridad[i % len(prioridad)]
                    codigo = f"DSP-{now_dt.strftime('%Y%m%d')}-{i:04d}"
                    try:
                        if not Despacho.objects.filter(codigo_despacho=codigo).exists():
                            obj = Despacho(
                                codigo_despacho=codigo,
                                numero_orden_farmacia=f"ORD-{i:05d}",
                                farmacia_origen_local_id=f.local_id,
                                farmacia_destino_local_id=farmacias[(i+1) % len(farmacias)].local_id if t == 'INTERCAMBIO' else None,
                                motorista=m,
                                estado=est,
                                tipo_despacho=t,
                                prioridad=pr,
                                cliente_nombre=f"Cliente {i}",
                                cliente_telefono='+56900000000',
                                destino_direccion=f"Calle {i} #123",
                                destino_referencia='Frente a plaza',
                                destino_geolocalizacion_validada=False,
                                tiene_receta_retenida=True if t == 'REENVIO_RECETA' else False,
                                numero_receta=f"REC-{i:05d}" if t == 'REENVIO_RECETA' else None,
                                requiere_devolucion_receta=True if t == 'REENVIO_RECETA' else False,
                                receta_devuelta_farmacia=False,
                                observaciones_receta=None,
                                descripcion_productos='Demo productos',
                                valor_declarado=10000 + (i * 100),
                                requiere_aprobacion_operadora=False,
                                aprobado_por_operadora=False,
                                firma_digital=(est == 'ENTREGADO'),
                                hubo_incidencia=(t == 'ERROR_DESPACHO'),
                                usuario_aprobador=None,
                                fecha_aprobacion=None,
                                fecha_registro=now_dt,
                                fecha_asignacion=now_dt,
                                fecha_salida_farmacia=None,
                                fecha_modificacion=now_dt,
                                usuario_registro=Usuario.objects.order_by('id').first(),
                                usuario_modificacion=Usuario.objects.order_by('id').first(),
                            )
                            obj.save()
                            gen += 1
                count += gen
        except Exception:
            pass
        return count

    def _load_movimientos(self, base: pathlib.Path) -> int:
        count = 0
        for name, data in self._iter_files(base, 'movimientos'):
            for d in (data or []):
                try:
                    did = d.get('despacho_id')
                    if not did:
                        continue
                    despacho = Despacho.objects.filter(id=int(did)).first()
                    if not despacho:
                        continue
                    usuario = Usuario.objects.order_by('id').first()
                    if not usuario:
                        # Crear operadora demo si no existe
                        user = User.objects.filter(username='operadora_demo').first()
                        if not user:
                            user = User.objects.create_user(username='operadora_demo', password='TempPass123!', first_name='Operadora', last_name='Demo')
                        rol_op = Rol.objects.filter(codigo='operador').first()
                        if not rol_op:
                            now = timezone.now()
                            rol_op = Rol(codigo='operador', nombre='Operador', django_group_name='Operadores', descripcion='Rol de operador', activo=1, fecha_creacion=now, fecha_modificacion=now)
                            try:
                                rol_op.save()
                            except Exception:
                                pass
                        usuario = Usuario.objects.filter(django_user_id=user.id).first()
                        if not usuario:
                            now = timezone.now()
                            usuario = Usuario(rol=rol_op, django_user_id=user.id, tipo_documento='DNI', documento_identidad=f'OP-{user.id}', nombre='Operadora', apellido='Demo', activo=1, fecha_creacion=now, fecha_modificacion=now)
                            usuario.save()
                    from ...models import MovimientoDespacho
                    obj = MovimientoDespacho(despacho=despacho, estado_nuevo=(d.get('estado_nuevo') or '').upper()[:9] or 'PENDIENTE', fecha_movimiento=self._parse_datetime(d.get('fecha_movimiento')) or timezone.now(), usuario=usuario)
                    obj.save()
                    count += 1
                except Exception:
                    continue
        return count

    def _parse_date(self, s):
        try:
            if not s:
                return None
            return date.fromisoformat(str(s).split('T')[0])
        except Exception:
            return None

    def _parse_time(self, s):
        try:
            if not s:
                return None
            parts = str(s).split(':')
            return time(int(parts[0]), int(parts[1]))
        except Exception:
            return None

    def _parse_decimal(self, s):
        try:
            if s is None:
                return None
            return float(s)
        except Exception:
            return None

    def _parse_datetime(self, s):
        try:
            if not s:
                return None
            # Aware datetime
            dt = timezone.datetime.fromisoformat(str(s).replace('Z',''))
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            return dt
        except Exception:
            return None
