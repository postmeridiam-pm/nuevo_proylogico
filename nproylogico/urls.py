"""
URL configuration for nproylogico project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from appnproylogico import views_configuration, views, views_auth
from appnproylogico.api import views as api_views
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),

    path('login/', views_auth.login_view, name='login'),
    path('oauth/password-token/', views_auth.oauth_password_token, name='oauth_password_token'),
    path('login/react/', views_auth.login_react_app, name='login_react'),
    path('registro/', views_auth.registro_view, name='registro'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('cerrar-sesion/', views_auth.logout_confirm, name='logout_confirm'),
    path('acceso-denegado/', views_auth.acceso_denegado, name='acceso_denegado'),

    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    path('configuracion/', views_configuration.configuracion, name='panel_configuracion'),
    path('configuracion/mis-permisos/', views_configuration.mis_permisos, name='mis_permisos'),
    path('configuracion/gestionar-usuarios/', views_configuration.gestionar_usuarios, name='gestionar_usuarios'),
    path('configuracion/generar-cuentas-prueba/', views_configuration.generar_cuentas_prueba, name='generar_cuentas_prueba'),
    path('configuracion/cargar-datos-demo/', views_configuration.cargar_datos_demo, name='cargar_datos_demo'),
    path('configuracion/asignar-rol/<int:user_id>/', views_configuration.asignar_rol, name='asignar_rol'),
    path('configuracion/cambiar-contrasena/', views_configuration.cambiar_contrasena, name='cambiar_contrasena'),
    path('configuracion/preferencias/', views_configuration.preferencias, name='preferencias'),
    path('configuracion/backup/', views_configuration.backup_datos, name='backup_datos'),

    path('supervisor/', views_configuration.panel_supervisor, name='panel_supervisor'),
    path('supervisor/generar-datos-masivos/', views_configuration.cargar_datos_demo, name='generar_datos_masivos'),
    path('supervisor/asignaciones-motorista-farmacia/', views_configuration.asignaciones_motorista_farmacia, name='asignaciones_motorista_farmacia'),

    path('farmacias/', views.listado_farmacias, name='listado_farmacias'),
    path('farmacias/agregar/', views.agregar_farmacia, name='agregar_farmacia'),
    path('farmacias/importar/', views.importar_farmacias, name='importar_farmacias'),
    path('farmacias/<int:pk>/', views.detalle_farmacia, name='detalle_farmacia'),
    path('farmacias/<int:pk>/actualizar/', views.actualizar_farmacia, name='actualizar_farmacia'),
    path('farmacias/<int:pk>/remover/', views.remover_farmacia, name='remover_farmacia'),
    path('movimientos/ingestar-normalizacion/', views.ingestar_normalizacion, name='ingestar_normalizacion'),
    path('movimientos/registrar/', views.registrar_movimiento, name='registrar_movimiento'),
    path('movimientos/anular/', views.movimiento_anular, name='movimiento_anular'),
    path('movimientos/modificar/', views.movimiento_modificar, name='movimiento_modificar'),
    path('movimientos/domicilio/', views.movimiento_directo, name='movimiento_directo'),
    path('movimientos/receta/', views.movimiento_receta, name='movimiento_receta'),
    path('movimientos/reenvio/', views.movimiento_reenvio, name='movimiento_reenvio'),
    path('movimientos/traslado/', views.movimiento_traslado, name='movimiento_traslado'),

    path('motoristas/', views.listado_motoristas, name='listado_motoristas'),
    path('motoristas/agregar/', views.agregar_motorista, name='agregar_motorista'),
    path('motoristas/<int:pk>/', views.detalle_motorista, name='detalle_motorista'),
    path('motoristas/<int:pk>/actualizar/', views.actualizar_motorista, name='actualizar_motorista'),
    path('motoristas/<int:pk>/remover/', views.remover_motorista, name='remover_motorista'),

    path('motos/', views.listado_motos, name='listado_motos'),
    path('motos/agregar/', views.agregar_moto, name='agregar_moto'),
    path('motos/<int:pk>/', views.detalle_moto, name='detalle_moto'),
    path('motos/<int:pk>/actualizar/', views.actualizar_moto, name='actualizar_moto'),
    path('motos/<int:pk>/remover/', views.remover_moto, name='remover_moto'),

    path('asignaciones/', views.listado_asignaciones, name='listado_asignaciones'),
    path('asignaciones/agregar/', views.agregar_asignacion, name='agregar_asignacion'),
    path('asignaciones/<int:pk>/', views.detalle_asignacion, name='detalle_asignacion'),
    path('asignaciones/<int:pk>/modificar/', views.modificar_asignacion, name='modificar_asignacion'),
    path('asignaciones/<int:pk>/remover/', views.remover_asignacion, name='remover_asignacion'),

    # API
    path('api/despachos/', api_views.DespachoList.as_view(), name='api_despachos'),
    path('api/movimientos/', api_views.MovimientoList.as_view(), name='api_movimientos'),
    path('api/farmacias/', api_views.FarmaciaList.as_view(), name='api_farmacias'),
    path('api/motoristas/', api_views.MotoristaList.as_view(), name='api_motoristas'),
    path('api/motos/', api_views.MotoList.as_view(), name='api_motos'),

    path('reportes/movimientos/', views.reporte_movimientos, name='reporte_movimientos'),
    path('reportes/resumen-operativo/', views.resumen_operativo_hoy, name='resumen_operativo_hoy'),
    path('reportes/resumen-operativo/export/', views.export_resumen_operativo, name='export_resumen_operativo'),
    path('react/despachos-activos/', views.react_despachos_activos, name='react_despachos_activos'),
    path('api/despachos-activos/', views.api_despachos_activos, name='api_despachos_activos'),
    path('reportes/despachos-activos/', views.despachos_activos, name='despachos_activos'),
    path('reportes/recetas-pendientes/', views.recetas_pendientes_devolucion, name='recetas_pendientes'),
    path('reportes/consulta-rapida/', views.consulta_rapida, name='consulta_rapida'),
    path('reportes/movimientos/', views.movimientos_general, name='movimientos_general'),
    path('motoristas/aviso/', views.avisar_movimiento_motorista, name='avisar_movimiento_motorista'),
    path('operadora/avisos/', views.feed_avisos_operadora, name='feed_avisos_operadora'),
    path('operadora/avisos/<int:audit_id>/leido/', views.marcar_aviso_leido, name='marcar_aviso_leido'),

    path('operadora/', views.panel_operadora, name='panel_operadora'),
    path('operadora/recetas/', views.recetas_retencion_panel, name='recetas_retencion_panel'),
    path('operadora/recetas/<int:despacho_id>/devuelta/', views.receta_marcar_devuelta, name='receta_marcar_devuelta'),
    path('operadora/cerrar-dia/', views.cerrar_dia_operadora, name='cerrar_dia_operadora'),
    path('operadora/generar-despachos-demo/', views.generar_despachos_demo, name='generar_despachos_demo'),
    path('operadora/generar-despachos-fecha/', views.generar_despachos_demo, name='generar_despachos_fecha'),

    # Despachos CRUD
    path('despachos/', views.listado_despachos, name='listado_despachos'),
    path('despachos/agregar/', views.agregar_despacho, name='agregar_despacho'),
    path('despachos/<int:pk>/', views.detalle_despacho, name='detalle_despacho'),
    path('despachos/<int:pk>/actualizar/', views.actualizar_despacho, name='actualizar_despacho'),
    path('despachos/<int:pk>/remover/', views.remover_despacho, name='remover_despacho'),
    path('despachos/<int:pk>/receta/', views.actualizar_receta_despacho, name='despacho_actualizar_receta'),
    path('despachos/<int:pk>/correccion/', views.solicitar_correccion_estado, name='solicitar_correccion_estado'),
    path('despachos/<int:pk>/correccion/aplicar/', views.aplicar_correccion_estado, name='aplicar_correccion_estado'),

    # Asignación Motorista–Farmacia CRUD (supervisor)
    path('supervisor/asignaciones-mf/', views_configuration.asignaciones_motorista_farmacia, name='listado_asignaciones_mf'),
    path('supervisor/asignaciones-mf/agregar/', views_configuration.agregar_asignacion_mf, name='agregar_asignacion_mf'),
    path('supervisor/asignaciones-mf/<int:pk>/', views_configuration.detalle_asignacion_mf, name='detalle_asignacion_mf'),
    path('supervisor/asignaciones-mf/<int:pk>/modificar/', views_configuration.modificar_asignacion_mf, name='modificar_asignacion_mf'),
    path('supervisor/asignaciones-mf/<int:pk>/remover/', views_configuration.remover_asignacion_mf, name='remover_asignacion_mf'),

    path('app/', TemplateView.as_view(template_name='react/app.html'), name='react_app'),
    path('oauth/refresh/', views_auth.oauth_refresh_token, name='oauth_refresh'),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('__debug__/', include('debug_toolbar.urls')),
]


# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
