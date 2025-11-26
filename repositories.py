from django.db import connection
from django.utils import timezone
from .models import Despacho, Localfarmacia

def fetchall(sql, params=None):
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        return cur.fetchall()

def get_despachos_activos():
    sql = (
        "SELECT id, codigo_despacho, estado, tipo_despacho, prioridad, farmacia_origen, motorista, "
        "moto_patente, cliente_nombre, cliente_telefono, destino_direccion, tiene_receta_retenida, "
        "requiere_aprobacion_operadora, aprobado_por_operadora, fecha_registro, fecha_asignacion, "
        "fecha_salida_farmacia, minutos_en_ruta, hubo_incidencia, tipo_incidencia, coordenadas_destino "
        "FROM vista_despachos_activos"
    )
    rows = fetchall(sql)
    if rows:
        return rows
    try:
        import json, pathlib
        data_path = pathlib.Path(__file__).resolve().parent.parent / 'static' / 'data' / 'despachos_activos.json'
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def get_resumen_operativo_hoy():
    sql = (
        "SELECT local_id, farmacia, comuna_nombre, total_despachos, entregados, fallidos, en_camino, "
        "pendientes, anulados, con_receta, con_incidencias, tiempo_promedio_minutos, valor_total "
        "FROM vista_resumen_operativo_hoy ORDER BY total_despachos DESC"
    )
    rows = fetchall(sql)
    if rows:
        return rows
    # Fallback por ORM
    hoy = timezone.now().date()
    qs = Despacho.objects.filter(fecha_registro__date=hoy)
    out = []
    if qs.count() == 0:
        return out
    # Agrupar por farmacia_origen_local_id
    by_farm = {}
    for d in qs:
        lid = d.farmacia_origen_local_id or ''
        by_farm.setdefault(lid, []).append(d)
    for lid, items in by_farm.items():
        farm = Localfarmacia.objects.filter(local_id=lid).first()
        nombre = farm.local_nombre if farm else lid
        comuna = farm.comuna_nombre if farm else ''
        total = len(items)
        entregados = sum(1 for x in items if x.estado == 'ENTREGADO')
        fallidos = sum(1 for x in items if x.estado == 'FALLIDO')
        en_camino = sum(1 for x in items if x.estado == 'EN_CAMINO')
        pendientes = sum(1 for x in items if x.estado == 'PENDIENTE')
        anulados = sum(1 for x in items if x.estado == 'ANULADO')
        con_receta = sum(1 for x in items if x.tiene_receta_retenida)
        con_incidencias = sum(1 for x in items if x.hubo_incidencia)
        domicilio = sum(1 for x in items if x.tipo_despacho == 'DOMICILIO')
        reenvio = sum(1 for x in items if x.tipo_despacho == 'REENVIO_RECETA')
        intercambio = sum(1 for x in items if x.tipo_despacho == 'INTERCAMBIO')
        error = sum(1 for x in items if x.tipo_despacho == 'ERROR_DESPACHO')
        tiempos = [x.tiempo_total_minutos for x in items if x.tiempo_total_minutos]
        prom_min = int(sum(tiempos)/len(tiempos)) if tiempos else 0
        valor_total = float(sum((x.valor_declarado or 0) for x in items))
        out.append([lid, nombre, comuna, total, entregados, fallidos, en_camino, pendientes, anulados, con_receta, con_incidencias, prom_min, valor_total, domicilio, reenvio, intercambio, error])
    # Ordenar por total desc
    out.sort(key=lambda r: r[3], reverse=True)
    return out

def get_resumen_operativo_mes(anio=None, mes=None):
    base = (
        "SELECT anio, mes, local_id, farmacia, comuna_nombre, total_despachos, entregados, fallidos, en_camino, "
        "pendientes, anulados, con_receta, con_incidencias, tiempo_promedio_minutos, valor_total "
        "FROM vista_resumen_operativo_mes"
    )
    params = []
    where = []
    if anio:
        where.append("anio = %s")
        params.append(int(anio))
    if mes:
        where.append("mes = %s")
        params.append(int(mes))
    sql = base + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY anio DESC, mes DESC, total_despachos DESC"
    rows = fetchall(sql, params)
    if rows:
        return rows
    # Fallback por ORM
    qs = Despacho.objects.all()
    if anio:
        qs = qs.filter(fecha_registro__year=int(anio))
    if mes:
        qs = qs.filter(fecha_registro__month=int(mes))
    out = []
    if qs.count() == 0:
        return out
    by_farm = {}
    for d in qs:
        lid = d.farmacia_origen_local_id or ''
        key = (d.fecha_registro.year, d.fecha_registro.month, lid)
        by_farm.setdefault(key, []).append(d)
    for (yy, mm, lid), items in by_farm.items():
        farm = Localfarmacia.objects.filter(local_id=lid).first()
        nombre = farm.local_nombre if farm else lid
        comuna = farm.comuna_nombre if farm else ''
        total = len(items)
        entregados = sum(1 for x in items if x.estado == 'ENTREGADO')
        fallidos = sum(1 for x in items if x.estado == 'FALLIDO')
        en_camino = sum(1 for x in items if x.estado == 'EN_CAMINO')
        pendientes = sum(1 for x in items if x.estado == 'PENDIENTE')
        anulados = sum(1 for x in items if x.estado == 'ANULADO')
        con_receta = sum(1 for x in items if x.tiene_receta_retenida)
        con_incidencias = sum(1 for x in items if x.hubo_incidencia)
        domicilio = sum(1 for x in items if x.tipo_despacho == 'DOMICILIO')
        reenvio = sum(1 for x in items if x.tipo_despacho == 'REENVIO_RECETA')
        intercambio = sum(1 for x in items if x.tipo_despacho == 'INTERCAMBIO')
        error = sum(1 for x in items if x.tipo_despacho == 'ERROR_DESPACHO')
        tiempos = [x.tiempo_total_minutos for x in items if x.tiempo_total_minutos]
        prom_min = int(sum(tiempos)/len(tiempos)) if tiempos else 0
        valor_total = float(sum((x.valor_declarado or 0) for x in items))
        out.append([yy, mm, lid, nombre, comuna, total, entregados, fallidos, en_camino, pendientes, anulados, con_receta, con_incidencias, prom_min, valor_total, domicilio, reenvio, intercambio, error])
    out.sort(key=lambda r: (r[0], r[1], r[5]), reverse=True)
    return out

def get_resumen_operativo_anual(anio=None):
    base = (
        "SELECT anio, local_id, farmacia, comuna_nombre, total_despachos, entregados, fallidos, en_camino, "
        "pendientes, anulados, con_receta, con_incidencias, tiempo_promedio_minutos, valor_total "
        "FROM vista_resumen_operativo_anual"
    )
    params = []
    sql = base + (" WHERE anio = %s" if anio else "") + " ORDER BY anio DESC, total_despachos DESC"
    rows = fetchall(sql, [int(anio)] if anio else [])
    if rows:
        return rows
    # Fallback por ORM
    qs = Despacho.objects.all()
    if anio:
        qs = qs.filter(fecha_registro__year=int(anio))
    out = []
    if qs.count() == 0:
        return out
    by_farm = {}
    for d in qs:
        lid = d.farmacia_origen_local_id or ''
        key = (d.fecha_registro.year, lid)
        by_farm.setdefault(key, []).append(d)
    for (yy, lid), items in by_farm.items():
        farm = Localfarmacia.objects.filter(local_id=lid).first()
        nombre = farm.local_nombre if farm else lid
        comuna = farm.comuna_nombre if farm else ''
        total = len(items)
        entregados = sum(1 for x in items if x.estado == 'ENTREGADO')
        fallidos = sum(1 for x in items if x.estado == 'FALLIDO')
        en_camino = sum(1 for x in items if x.estado == 'EN_CAMINO')
        pendientes = sum(1 for x in items if x.estado == 'PENDIENTE')
        anulados = sum(1 for x in items if x.estado == 'ANULADO')
        con_receta = sum(1 for x in items if x.tiene_receta_retenida)
        con_incidencias = sum(1 for x in items if x.hubo_incidencia)
        domicilio = sum(1 for x in items if x.tipo_despacho == 'DOMICILIO')
        reenvio = sum(1 for x in items if x.tipo_despacho == 'REENVIO_RECETA')
        intercambio = sum(1 for x in items if x.tipo_despacho == 'INTERCAMBIO')
        error = sum(1 for x in items if x.tipo_despacho == 'ERROR_DESPACHO')
        tiempos = [x.tiempo_total_minutos for x in items if x.tiempo_total_minutos]
        prom_min = int(sum(tiempos)/len(tiempos)) if tiempos else 0
        valor_total = float(sum((x.valor_declarado or 0) for x in items))
        out.append([yy, lid, nombre, comuna, total, entregados, fallidos, en_camino, pendientes, anulados, con_receta, con_incidencias, prom_min, valor_total, domicilio, reenvio, intercambio, error])
    out.sort(key=lambda r: (r[0], r[4]), reverse=True)
    return out

def normalize_from_normalizacion(limit=500):
    with connection.cursor() as cur:
        cur.execute("CALL sp_normalizar_despachos(%s)", [int(limit)])
        return True

def normalize_farmacia_headers(headers):
    mapping = {
        'local_id': ['local_id', 'id_local', 'id'],
        'local_nombre': ['local_nombre', 'nombre_local', 'farmacia', 'nombre'],
        'local_direccion': ['local_direccion', 'direccion', 'calle'],
        'comuna_nombre': ['comuna_nombre', 'comuna'],
        'localidad_nombre': ['localidad_nombre', 'localidad'],
        'fk_region': ['fk_region', 'region_id', 'id_region'],
        'fk_comuna': ['fk_comuna', 'comuna_id', 'id_comuna'],
        'fk_localidad': ['fk_localidad', 'localidad_id', 'id_localidad'],
        'funcionamiento_hora_apertura': ['funcionamiento_hora_apertura', 'hora_apertura', 'apertura'],
        'funcionamiento_hora_cierre': ['funcionamiento_hora_cierre', 'hora_cierre', 'cierre'],
        'funcionamiento_dia': ['funcionamiento_dia', 'dia_funcionamiento', 'dia'],
        'local_telefono': ['local_telefono', 'telefono', 'fono'],
        'local_lat': ['local_lat', 'lat', 'latitud'],
        'local_lng': ['local_lng', 'lng', 'longitud'],
        'fecha': ['fecha', 'date', 'f_registro'],
    }
    normalized = {}
    for canonical, aliases in mapping.items():
        for h in headers:
            hh = str(h).strip().lower()
            if hh in [a.lower() for a in aliases]:
                normalized[hh] = canonical
    return {h: normalized.get(str(h).strip().lower(), str(h).strip().lower()) for h in headers}

def validate_farmacias_import(rows):
    if not rows:
        return []
    headers = rows[0]
    header_map = normalize_farmacia_headers(headers)
    idx = {header_map.get(h, h): i for i, h in enumerate(headers)}
    seen = set()
    cleaned = []
    for r in rows[1:]:
        local_id = str(r[idx.get('local_id', 0)]).strip()
        key = (local_id or '').upper()
        if key in seen:
            continue
        seen.add(key)
        item = {
            'local_id': local_id,
            'local_nombre': str(r[idx.get('local_nombre', 1)]).strip(),
            'local_direccion': str(r[idx.get('local_direccion', 2)]).strip(),
            'comuna_nombre': str(r[idx.get('comuna_nombre', 3)]).strip(),
            'localidad_nombre': str(r[idx.get('localidad_nombre', 4)]).strip(),
            'fk_region': str(r[idx.get('fk_region', 5)]).strip(),
            'fk_comuna': str(r[idx.get('fk_comuna', 6)]).strip(),
            'fk_localidad': str(r[idx.get('fk_localidad', 7)]).strip(),
            'funcionamiento_hora_apertura': str(r[idx.get('funcionamiento_hora_apertura', 8)]).strip(),
            'funcionamiento_hora_cierre': str(r[idx.get('funcionamiento_hora_cierre', 9)]).strip(),
            'funcionamiento_dia': str(r[idx.get('funcionamiento_dia', 10)]).strip(),
            'local_telefono': str(r[idx.get('local_telefono', 11)]).strip(),
            'local_lat': str(r[idx.get('local_lat', 12)]).strip(),
            'local_lng': str(r[idx.get('local_lng', 13)]).strip(),
            'fecha': str(r[idx.get('fecha', 14)]).strip(),
        }
        cleaned.append(item)
    return cleaned
