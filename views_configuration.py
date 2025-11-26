from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .roles import obtener_rol_usuario, obtener_permisos_usuario, MODULOS, ROLES
from .auth_decorators import solo_admin
from .auth_decorators import rol_requerido
from .models import AsignacionMotoristaFarmacia, Motorista, Localfarmacia, Rol, Usuario
from .forms import AsignacionMotoristaFarmaciaForm
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command
import os, io, datetime as dt


@login_required(login_url='login')
def configuracion(request):
    """Panel principal de configuración"""
    rol_usuario = obtener_rol_usuario(request.user)
    permisos = obtener_permisos_usuario(request.user)
    
    # Contar módulos accesibles
    modulos_accesibles = {}
    for modulo, nombre in MODULOS.items():
        if modulo in permisos and permisos[modulo]:
            modulos_accesibles[modulo] = nombre
    
    context = {
        'rol_usuario': rol_usuario,
        'permisos': permisos,
        'modulos_accesibles': modulos_accesibles,
        'total_modulos': len(modulos_accesibles),
    }
    
    return render(request, 'auth/modificar-contrasenia.html', context)


@login_required(login_url='login')
def mis_permisos(request):
    """Ver los permisos del usuario actual"""
    rol_usuario = obtener_rol_usuario(request.user)
    permisos = obtener_permisos_usuario(request.user)
    
    # Formatear permisos para mostrar
    permisos_formateados = {}
    for modulo, acciones in permisos.items():
        if acciones:
            permisos_formateados[MODULOS.get(modulo, modulo)] = acciones
    
    context = {
        'rol_usuario': rol_usuario,
        'permisos': permisos_formateados,
    }
    
    return render(request, 'admin/panel-admin.html', context)


@solo_admin
def gestionar_usuarios(request):
    """Gestionar usuarios y roles (solo admin)"""
    usuarios = User.objects.all().order_by('-date_joined')
    
    context = {
        'usuarios': usuarios,
    }
    
    return render(request, 'admin/gestionar-usuarios.html', context)


@solo_admin
def asignar_rol(request, user_id):
    """Asignar rol a un usuario"""
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        rol = request.POST.get('rol')
        
        # Remover grupos anteriores
        usuario.groups.clear()
        
        # Asignar nuevo grupo
        if rol and rol != 'admin':
            grupo, created = Group.objects.get_or_create(name=rol)
            usuario.groups.add(grupo)
            usuario.is_staff = False
            usuario.is_superuser = False
        elif rol == 'admin':
            usuario.is_staff = True
            usuario.is_superuser = True
        else:
            usuario.is_staff = False
            usuario.is_superuser = False
        
        usuario.save()
        messages.success(request, f'Rol asignado a {usuario.username} exitosamente.')
        return redirect('gestionar_usuarios')
    
    # Obtener rol actual
    rol_actual = obtener_rol_usuario(usuario)
    
    context = {
        'usuario': usuario,
        'rol_actual': rol_actual,
        'roles': ROLES,
    }
    
    return render(request, 'admin/asignar-rol.html', context)


@login_required(login_url='login')
def cambiar_contrasena(request):
    """Cambiar contraseña del usuario"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Tu contraseña ha sido cambiada exitosamente.')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores.')
    else:
        form = PasswordChangeForm(request.user)
    
    # Personalizar widgets del formulario
    for field in form.fields.values():
        field.widget.attrs.update({'class': 'form-control'})
    
    context = {
        'form': form,
    }
    
    return render(request, 'admin/panel-admin.html', context)


@login_required(login_url='login')
def preferencias(request):
    """Gestionar preferencias del usuario usando sesión"""
    
    # Si no existen preferencias en la sesión, inicializamos valores por defecto
    if 'preferencias' not in request.session:
        request.session['preferencias'] = {
            'tema': 'claro',
            'notif_email': True,
            'notif_sms': False,
            'idioma': 'es',
        }

    preferencias = request.session['preferencias']

    if request.method == 'POST':
        preferencias['tema'] = request.POST.get('tema', 'claro')
        preferencias['notif_email'] = 'notif_email' in request.POST
        preferencias['notif_sms'] = 'notif_sms' in request.POST
        preferencias['idioma'] = request.POST.get('idioma', 'es')

        request.session['preferencias'] = preferencias  # Guardar cambios en la sesión
        messages.success(request, 'Preferencias guardadas exitosamente.')
        return redirect('preferencias')

    context = {
        'preferencias': preferencias,
    }

    return render(request, 'admin/panel-admin.html', context)


@rol_requerido('supervisor')
def panel_supervisor(request):
    """Panel principal del Supervisor"""
    # Datos básicos para acceso rápido
    total_motoristas = Motorista.objects.count()
    total_asignaciones = AsignacionMotoristaFarmacia.objects.count()
    total_farmacias = 0
    total_motos = 0
    try:
        from .models import Localfarmacia, Moto
        total_farmacias = Localfarmacia.objects.count()
        total_motos = Moto.objects.count()
    except Exception:
        total_farmacias = 0
        total_motos = 0
    # Fallback con JSON si la BD está vacía
    try:
        import json, pathlib
        data_path = pathlib.Path(__file__).resolve().parent.parent / 'static' / 'data'
        if total_farmacias == 0 or total_motos < 56 or total_motoristas == 0 or total_asignaciones == 0:
            try:
                call_command('load_samples')
            except Exception:
                pass
            try:
                from .models import Localfarmacia, Moto
                total_farmacias = Localfarmacia.objects.count()
                total_motos = Moto.objects.count()
            except Exception:
                pass
            if total_farmacias == 0:
                with open(data_path / 'farmacias.json', 'r', encoding='utf-8') as f:
                    total_farmacias = len(json.load(f))
            if total_motos == 0:
                with open(data_path / 'motos.json', 'r', encoding='utf-8') as f:
                    total_motos = len(json.load(f))
            if total_motoristas == 0:
                with open(data_path / 'motoristas.json', 'r', encoding='utf-8') as f:
                    total_motoristas = len(json.load(f))
            if total_asignaciones == 0:
                with open(data_path / 'asignaciones_motorista_farmacia.json', 'r', encoding='utf-8') as f:
                    total_asignaciones = len(json.load(f))
    except Exception:
        pass
    # Incidencias no leídas (AVISO_MOV sin AVISO_MOV_LEIDO asociado)
    avisos_no_leidos = 0
    try:
        from .models import AuditoriaGeneral
        avisos = AuditoriaGeneral.objects.filter(tipo_operacion='AVISO_MOV').values('id')
        leidos = set(AuditoriaGeneral.objects.filter(tipo_operacion='AVISO_MOV_LEIDO').values_list('id_registro_afectado', flat=True))
        avisos_no_leidos = sum(1 for a in avisos if str(a['id']) not in leidos)
    except Exception:
        avisos_no_leidos = 0

    context = {
        'total_motoristas': total_motoristas,
        'total_asignaciones': total_asignaciones,
        'total_farmacias': total_farmacias,
        'total_motos': total_motos,
        'avisos_no_leidos': avisos_no_leidos,
    }
    return render(request, 'supervisor/panel-supervisor.html', context)

@solo_admin
def backup_datos(request):
    from django.conf import settings
    ts = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    base = os.path.join(settings.MEDIA_ROOT, 'backups')
    try:
        os.makedirs(base, exist_ok=True)
        out = io.StringIO()
        call_command('dumpdata', 'appnproylogico', format='json', indent=2, stdout=out)
        data = out.getvalue()
        path = os.path.join(base, f'backup_{ts}.json')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(data)
        url = settings.MEDIA_URL + 'backups/' + os.path.basename(path)
        messages.success(request, f'Respaldo generado: {url}')
    except Exception as e:
        messages.error(request, f'Error al respaldar: {e}')
    return redirect('panel_configuracion')


@rol_requerido('supervisor')
def asignaciones_motorista_farmacia(request):
    search_query = request.GET.get('search', '').strip()
    filtro_estado = request.GET.get('estado', '')

    asignaciones = AsignacionMotoristaFarmacia.objects.all().select_related('motorista', 'farmacia')

    if search_query:
        asignaciones = asignaciones.filter(
            Q(motorista__usuario__nombre__icontains=search_query) |
            Q(motorista__usuario__apellido__icontains=search_query) |
            Q(farmacia__local_nombre__icontains=search_query) |
            Q(observaciones__icontains=search_query)
        )

    if filtro_estado == 'activa':
        asignaciones = asignaciones.filter(activa=1)
    elif filtro_estado == 'inactiva':
        asignaciones = asignaciones.filter(activa=0)

    asignaciones = asignaciones.order_by('-fecha_asignacion')

    paginator = Paginator(asignaciones, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    samples = []
    if page_obj.paginator.count == 0:
        try:
            import json, pathlib
            data_path = pathlib.Path(__file__).resolve().parent.parent / 'static' / 'data' / 'asignaciones_motorista_farmacia.json'
            with open(data_path, 'r', encoding='utf-8') as f:
                samples = json.load(f)
        except Exception:
            samples = []
    incidencias = []
    try:
        from django.db import connection
        with connection.cursor() as cur:
            cur.execute("SELECT codigo_despacho, motorista_nombre, tipo_incidencia, fecha_registro FROM vista_incidencias_recientes ORDER BY fecha_registro DESC LIMIT 20")
            incidencias = cur.fetchall()
    except Exception:
        incidencias = []
    if not incidencias:
        try:
            import json, pathlib
            data_path = pathlib.Path(__file__).resolve().parent.parent / 'static' / 'data' / 'incidencias.json'
            with open(data_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            incidencias = [(d.get('codigo_despacho'), d.get('motorista'), d.get('tipo_incidencia'), d.get('fecha_registro')) for d in raw]
        except Exception:
            incidencias = []
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'filtro_estado': filtro_estado,
        'samples': samples,
        'incidencias': incidencias,
    }

    return render(request, 'asignaciones/listar-asignaciones-mf.html', context)


@rol_requerido('supervisor')
def agregar_asignacion_mf(request):
    if request.method == 'POST':
        form = AsignacionMotoristaFarmaciaForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, 'Asignación creada exitosamente.')
            return redirect('detalle_asignacion_mf', pk=obj.id)
        else:
            messages.error(request, 'Corrige los errores del formulario')
            return render(request, 'asignaciones/editar-asignacion-mf.html', {'form': form, 'asignacion': None})
    else:
        initial = {}
        mot = request.GET.get('motorista')
        far = request.GET.get('farmacia')
        try:
            if mot:
                initial['motorista'] = int(mot)
        except Exception:
            pass
        try:
            if far:
                initial['farmacia'] = far
        except Exception:
            pass
        form = AsignacionMotoristaFarmaciaForm(initial=initial)
        return render(request, 'asignaciones/editar-asignacion-mf.html', {'form': form, 'asignacion': None})


@rol_requerido('supervisor')
def detalle_asignacion_mf(request, pk):
    a = get_object_or_404(AsignacionMotoristaFarmacia, pk=pk)
    return render(request, 'asignaciones/detalle-asignacion-mf.html', {'asignacion': a})


@rol_requerido('supervisor')
def modificar_asignacion_mf(request, pk):
    a = get_object_or_404(AsignacionMotoristaFarmacia, pk=pk)
    if request.method == 'POST':
        form = AsignacionMotoristaFarmaciaForm(request.POST, instance=a)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asignación actualizada.')
            return redirect('detalle_asignacion_mf', pk=a.id)
        else:
            messages.error(request, 'Corrige los errores')
    else:
        form = AsignacionMotoristaFarmaciaForm(instance=a)
    return render(request, 'asignaciones/editar-asignacion-mf.html', {'form': form, 'asignacion': a})


@rol_requerido('supervisor')
def remover_asignacion_mf(request, pk):
    a = get_object_or_404(AsignacionMotoristaFarmacia, pk=pk)
    if request.method == 'POST':
        try:
            a.activa = 1 if a.activa == 0 else 0
            a.save()
            estado = 'activada' if a.activa == 1 else 'desactivada'
            messages.success(request, f'Asignación {estado}.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('detalle_asignacion_mf', pk=a.id)
    return render(request, 'asignaciones/detalle-asignacion-mf.html', {'asignacion': a})


@solo_admin
def generar_cuentas_prueba(request):
    datos = [
        {
            'username': 'helena.diaz',
            'first_name': 'Helena',
            'last_name': 'Díaz',
            'password': 'Helena123!',
            'email': 'helena@example.com',
            'group': 'Motoristas',
            'rol': 'MOTORISTA',
            'motorista': True,
        },
        {
            'username': 'eren.yager',
            'first_name': 'Eren',
            'last_name': 'Yager',
            'password': 'Eren123!',
            'email': 'eren@example.com',
            'group': 'Supervisores',
            'rol': 'SUPERVISOR',
            'motorista': False,
        },
        {
            'username': 'carla.ortega',
            'first_name': 'Carla',
            'last_name': 'Ortega',
            'password': 'Carla123!',
            'email': 'carla@example.com',
            'group': 'Operadores',
            'rol': 'OPERADOR',
            'motorista': False,
        },
        {
            'username': 'levi.ackerman',
            'first_name': 'Levi',
            'last_name': 'Ackerman',
            'password': 'Levi123!',
            'email': 'levi@example.com',
            'group': 'Gerentes',
            'rol': 'GERENTE',
            'motorista': False,
        },
        {
            'username': 'shingeki.kyojin',
            'first_name': 'Shingeki',
            'last_name': 'Kyojin',
            'password': 'Admin123!',
            'email': 'admin@example.com',
            'group': None,
            'rol': 'ADMIN',
            'motorista': False,
            'is_staff': True,
            'is_superuser': True,
        },
    ]

    creados = []
    for d in datos:
        user, _ = User.objects.get_or_create(
            username=d['username'],
            defaults={
                'first_name': d['first_name'],
                'last_name': d['last_name'],
                'email': d['email'],
                'is_staff': d.get('is_staff', False),
                'is_superuser': d.get('is_superuser', False),
            }
        )
        user.set_password(d['password'])
        user.is_staff = d.get('is_staff', False)
        user.is_superuser = d.get('is_superuser', False)
        user.save()

        if d.get('group'):
            g, _ = Group.objects.get_or_create(name=d['group'])
            user.groups.set([g])
        rol = Rol.objects.get(codigo=d['rol'])
        u, _ = Usuario.objects.get_or_create(
            django_user_id=user.id,
            defaults={
                'rol': rol,
                'tipo_documento': 'RUT',
                'documento_identidad': f"{d['username']}-doc",
                'nombre': d['first_name'],
                'apellido': d['last_name'],
                'telefono': '000000000',
                'activo': 1,
                'consiente_datos_salud': 0,
                'fecha_consentimiento_salud': None,
                'fecha_creacion': timezone.now(),
                'fecha_modificacion': timezone.now(),
                'usuario_modificacion': None,
            }
        )
        if d['motorista']:
            Motorista.objects.get_or_create(
                usuario=u,
                defaults={
                    'licencia_numero': 'LIC-' + d['username'][:8].upper(),
                    'licencia_clase': 'A',
                    'fecha_vencimiento_licencia': timezone.now().date() + timedelta(days=365),
                    'emergencia_nombre': 'Contacto',
                    'emergencia_telefono': '000000000',
                    'emergencia_parentesco': 'Otro',
                    'total_entregas_completadas': 0,
                    'total_entregas_fallidas': 0,
                    'activo': 1,
                    'disponible_hoy': 1,
                    'fecha_creacion': timezone.now(),
                    'fecha_modificacion': timezone.now(),
                    'usuario_modificacion': None,
                }
            )
        creados.append(d['username'])

    messages.success(request, 'Cuentas de prueba generadas: ' + ', '.join(creados))
    return redirect('gestionar_usuarios')


@solo_admin
def cargar_datos_demo(request):
    try:
        call_command('load_samples')
        messages.success(request, 'Datos de ejemplo cargados correctamente desde static/data/*.json')
    except Exception as e:
        messages.error(request, f'Error al cargar datos de ejemplo: {e}')
    return redirect('panel_supervisor')
