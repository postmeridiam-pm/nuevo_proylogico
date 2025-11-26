from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .roles import obtener_permisos_usuario, obtener_rol_usuario
from django.conf import settings
from oauth2_provider.models import AccessToken
from django.utils import timezone


def permiso_requerido(modulo, accion):
    def decorator(view_func):
        @login_required(login_url='login')
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)
            token = request.COOKIES.get('access_token')
            if not _verify_oauth(token, request.user, request.method):
                messages.error(request, 'Acceso denegado')
                return redirect('acceso_denegado')
            if not request.user.is_active:
                messages.error(request, 'Cuenta inactiva')
                return redirect('acceso_denegado')
            permisos = obtener_permisos_usuario(request.user)
            acciones = permisos.get(modulo) or set()
            if accion in acciones or 'all' in acciones:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'Acceso denegado')
            return redirect('acceso_denegado')
        return _wrapped_view
    return decorator


def rol_requerido(rol):
    def decorator(view_func):
        @login_required(login_url='login')
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser or request.user.is_staff:
                return view_func(request, *args, **kwargs)
            token = request.COOKIES.get('access_token')
            if not _verify_oauth(token, request.user, request.method):
                messages.error(request, 'Acceso denegado')
                return redirect('acceso_denegado')
            if not request.user.is_active:
                messages.error(request, 'Cuenta inactiva')
                return redirect('acceso_denegado')
            if obtener_rol_usuario(request.user) == rol:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'Acceso denegado')
            return redirect('acceso_denegado')
        return _wrapped_view
    return decorator


def solo_admin(view_func):
    @login_required(login_url='login')
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'Acceso denegado')
        return redirect('acceso_denegado')
    return _wrapped_view


def _verify_oauth(token: str, user, method: str | None = None) -> bool:
    if not token or not user:
        return False
    try:
        at = AccessToken.objects.select_related('application', 'user').filter(token=token).first()
        if not at:
            return False
        if at.expires < timezone.now():
            return False
        if at.user_id != user.id:
            return False
        app = at.application
        if not app or app.name != 'ProyLogico First-Party':
            return False
        # Scope check: GET requires 'read', POST requires 'write'
        sc = (getattr(at, 'scope', '') or '')
        need = 'write' if (method or '').upper() == 'POST' else 'read'
        if need not in sc.split():
            return False
        return True
    except Exception:
        return False
