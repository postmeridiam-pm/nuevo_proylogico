from django.contrib.auth.models import Group


MODULOS = {
    'farmacias': 'Farmacias',
    'motoristas': 'Motoristas',
    'motos': 'Motos',
    'asignaciones': 'Asignaciones',
    'movimientos': 'Movimientos',
    'despachos': 'Despachos',
}


ROLES = (
    ('admin', 'Administrador'),
    ('operador', 'Operador'),
    ('supervisor', 'Supervisor'),
    ('gerente', 'Gerente'),
    ('motorista', 'Motorista'),
)


def obtener_rol_usuario(user):
    if user.is_superuser:
        return 'admin'
    grupos = {g.name for g in user.groups.all()}
    if 'Motoristas' in grupos:
        return 'motorista'
    if 'Operadores' in grupos:
        return 'operador'
    if 'Supervisores' in grupos:
        return 'supervisor'
    if 'Gerentes' in grupos:
        return 'gerente'
    return 'usuario'


def obtener_permisos_usuario(user):
    rol = obtener_rol_usuario(user)
    if rol == 'admin':
        return {k: {'all'} for k in MODULOS.keys()}
    if rol == 'operador':
        return {
            'farmacias': {'view'},
            'motoristas': {'view'},
            'motos': {'view'},
            'asignaciones': {'view'},
            'movimientos': {'view', 'add'},
            'despachos': {'view', 'add', 'change'},
        }
    if rol == 'supervisor':
        return {
            'farmacias': {'view'},
            'motoristas': {'view', 'change'},
            'motos': {'view'},
            'asignaciones': {'view', 'change'},
            'movimientos': {'view', 'add'},
            'despachos': {'view', 'change'},
        }
    if rol == 'gerente':
        return {k: {'view'} for k in MODULOS.keys()}
    if rol == 'motorista':
        return {
            'farmacias': {'view'},
            'motoristas': {'view'},
            'motos': {'view'},
            'asignaciones': {'view'},
            'movimientos': {'view'},
            'despachos': {'view'},
        }
    return {k: set() for k in MODULOS.keys()}
