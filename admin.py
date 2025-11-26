from django.contrib import admin
from django.conf import settings
from django.utils.html import format_html
import os, glob
from .models import Usuario, Rol, AuditoriaGeneral, Motorista, Localfarmacia, Moto


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "django_group_name", "activo", "fecha_creacion", "fecha_modificacion")
    list_filter = ("activo",)
    search_fields = ("codigo", "nombre", "django_group_name")


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "apellido", "documento_identidad", "tipo_documento", "telefono", "rol", "activo", "documentos")
    list_filter = ("rol", "activo", "tipo_documento")
    search_fields = ("nombre", "apellido", "documento_identidad")

    def documentos(self, obj):
        base = os.path.join(settings.MEDIA_ROOT, 'docs', 'users', str(obj.django_user_id))
        if not os.path.isdir(base):
            return "-"
        files = []
        for p in glob.glob(os.path.join(base, '*')):
            name = os.path.basename(p)
            url = settings.MEDIA_URL + f'docs/users/{obj.django_user_id}/' + name
            files.append(f'<a href="{url}" target="_blank">{name}</a>')
        return format_html(' | '.join(files))


@admin.register(AuditoriaGeneral)
class AuditoriaGeneralAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre_tabla", "id_registro_afectado", "tipo_operacion", "usuario", "fecha_evento")
    search_fields = ("nombre_tabla", "id_registro_afectado", "tipo_operacion")
    list_filter = ("tipo_operacion", "nombre_tabla", "usuario")
    date_hierarchy = "fecha_evento"
    readonly_fields = ("datos_antiguos", "datos_nuevos")
    fieldsets = (
        (None, {
            "fields": ("nombre_tabla", "id_registro_afectado", "tipo_operacion", "usuario", "fecha_evento")
        }),
        ("Datos", {
            "fields": ("datos_antiguos", "datos_nuevos")
        }),
    )


@admin.register(Motorista)
class MotoristaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "licencia_numero", "licencia_clase", "fecha_vencimiento_licencia", "activo", "documentos")
    list_filter = ("activo", "licencia_clase")
    search_fields = ("usuario__nombre", "usuario__apellido", "licencia_numero")

    def documentos(self, obj):
        base = os.path.join(settings.MEDIA_ROOT, 'docs', 'motoristas', str(obj.id))
        if not os.path.isdir(base):
            return "-"
        links = []
        for key in ("licencia_vigente", "permiso_circulacion"):
            pattern = glob.glob(os.path.join(base, key + '.*'))
            if pattern:
                name = os.path.basename(pattern[0])
                url = settings.MEDIA_URL + f'docs/motoristas/{obj.id}/' + name
                label = "Licencia" if key == "licencia_vigente" else "Permiso"
                links.append(f'<a href="{url}" target="_blank">{label}</a>')
        return format_html(' | '.join(links) if links else "-")


@admin.register(Localfarmacia)
class LocalfarmaciaAdmin(admin.ModelAdmin):
    list_display = ("local_id", "local_nombre", "comuna_nombre", "activo", "fecha", "geolocalizacion_validada")
    list_filter = ("activo", "comuna_nombre", "geolocalizacion_validada")
    search_fields = ("local_id", "local_nombre", "local_direccion", "comuna_nombre")
    date_hierarchy = "fecha"


@admin.register(Moto)
class MotoAdmin(admin.ModelAdmin):
    list_display = ("patente", "marca", "modelo", "estado", "propietario_nombre", "activo")
    list_filter = ("estado", "activo", "tipo_combustible")
    search_fields = ("patente", "marca", "modelo", "numero_motor", "numero_chasis", "propietario_nombre")
    date_hierarchy = "fecha_inscripcion"
admin.site.site_header = "LOGICO · Administración"
admin.site.site_title = "LOGICO Admin"
admin.site.index_title = "Panel de control"
