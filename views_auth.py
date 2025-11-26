from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import RegistroForm
from .roles import obtener_rol_usuario
from django.conf import settings
import time, json, hmac, hashlib, base64
from oauth2_provider.models import Application, AccessToken, RefreshToken
import os
from django.utils import timezone
from datetime import timedelta


def login_view(request):
    """Vista de inicio de sesión personalizado"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            login(request, usuario)
            rol = obtener_rol_usuario(usuario)
            messages.success(request, f'¡Bienvenido {usuario.username}! (Rol: {rol})')
            return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'auth/iniciar-sesion.html', {'form': form})


def registro_view(request):
    """Vista de registro de nuevos usuarios"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            try:
                docf = request.FILES.get('documento_archivo')
                if docf:
                    allow = set(settings.UPLOAD_ALLOWED_CONTENT_TYPES)
                    if getattr(docf, 'content_type', '') not in allow:
                        raise ValueError('Tipo de archivo no permitido')
                    if docf.size > settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024:
                        raise ValueError('Archivo demasiado grande')
                    import os, imghdr
                    tipo = form.cleaned_data.get('tipo_documento') or 'DOC'
                    base = os.path.join(settings.MEDIA_ROOT, 'docs', 'users', str(usuario.id))
                    os.makedirs(base, exist_ok=True)
                    ext = '.bin'
                    ct = getattr(docf, 'content_type', '')
                    if ct == 'application/pdf':
                        ext = '.pdf'
                        head = docf.read(4)
                        docf.seek(0)
                        if head != b'%PDF':
                            raise ValueError('PDF inválido')
                    else:
                        sniff = imghdr.what(None, h=docf.read(32))
                        docf.seek(0)
                        if sniff not in ('jpeg','png'):
                            raise ValueError('Imagen inválida')
                        ext = '.jpg' if sniff == 'jpeg' else '.png'
                    fname = f'{tipo.lower()}_documento{ext}'
                    path = os.path.join(base, fname)
                    with open(path, 'wb') as dest:
                        for chunk in docf.chunks():
                            dest.write(chunk)
            except Exception:
                pass
            messages.success(
                request, 
                f'¡Usuario "{usuario.username}" registrado exitosamente! '
                'Por favor, inicia sesión.'
            )
            return redirect('login')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RegistroForm()
    
    return render(request, 'auth/registro.html', {'form': form})


@login_required(login_url='login')
def logout_view(request):
    """Vista para cerrar sesión"""
    nombre_usuario = request.user.username
    logout(request)
    messages.success(request, 'Cerraste tu sesión. Gracias por usar la plataforma.')
    return redirect('login')


def acceso_denegado(request):
    """Página de acceso denegado"""
    return render(request, 'auth/acceso-denegado.html', status=403)


@ensure_csrf_cookie
def login_react_app(request):
    return render(request, 'react/app.html')


@login_required(login_url='login')
def logout_confirm(request):
    return render(request, 'auth/cerrar-sesion.html')


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')

def _create_jwt(payload: dict) -> str:
    header = {'alg': 'HS256', 'typ': 'JWT'}
    h = _b64url(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    p = _b64url(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    signing_input = f'{h}.{p}'.encode('ascii')
    sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    return f'{h}.{p}.{_b64url(sig)}'


def _ensure_password_app():
    app, _ = Application.objects.get_or_create(
        name='ProyLogico First-Party',
        client_type=Application.CLIENT_CONFIDENTIAL,
        authorization_grant_type=Application.GRANT_PASSWORD,
    )
    return app


@ensure_csrf_cookie
def oauth_password_token(request):
    if request.method != 'POST':
        return redirect('login')
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()
    user = authenticate(request, username=username, password=password)
    if not user:
        return render(request, 'auth/iniciar-sesion.html', {'form': AuthenticationForm(request, data=request.POST)})
    app = _ensure_password_app()
    expires = timezone.now() + timedelta(seconds=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'])
    access = AccessToken.objects.create(user=user, application=app, token=_b64url(os.urandom(24)), expires=expires, scope='read write')
    refresh = RefreshToken.objects.create(user=user, application=app, token=_b64url(os.urandom(24)), access_token=access)
    resp = redirect('home')
    secure_flag = (not settings.DEBUG) or request.is_secure()
    samesite = 'Strict' if secure_flag else 'Lax'
    resp.set_cookie('access_token', access.token, max_age=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'], secure=secure_flag, httponly=True, samesite=samesite)
    resp.set_cookie('refresh_token', refresh.token, max_age=settings.OAUTH2_PROVIDER['REFRESH_TOKEN_EXPIRE_SECONDS'], secure=secure_flag, httponly=True, samesite=samesite)
    return resp


def oauth_refresh_token(request):
    from django.utils import timezone
    from datetime import timedelta
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return redirect('login')
    try:
        app = _ensure_password_app()
        rt = RefreshToken.objects.select_related('user').get(token=refresh_token)
        at = AccessToken.objects.create(
            user=rt.user,
            application=app,
            token=os.urandom(24).hex(),
            expires=timezone.now() + timedelta(seconds=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS']),
            scope='read write'
        )
        resp = redirect('home')
        secure_flag = (not settings.DEBUG) or request.is_secure()
        samesite = 'Strict' if secure_flag else 'Lax'
        resp.set_cookie('access_token', at.token, max_age=settings.OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS'], secure=secure_flag, httponly=True, samesite=samesite)
        return resp
    except Exception:
        return redirect('login')
