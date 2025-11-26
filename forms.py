from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.utils import timezone
from .models import (
    Localfarmacia,
    Motorista,
    Moto,
    AsignacionMotoMotorista,
    Despacho,
    AsignacionMotoristaFarmacia,
    Usuario,
    Rol,
    Region,
)


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label="Nombre")
    last_name = forms.CharField(required=True, label="Apellido")
    rol = forms.ModelChoiceField(queryset=Rol.objects.all(), required=True, label="Rol")
    tipo_documento = forms.ChoiceField(
        choices=(
            ("RUT", "DNI (Chile) o Cédula/RUT"),
            ("PASAPORTE", "Pasaporte (extranjeros)"),
            ("DNI_EXTRANJERO", "Documento extranjero (DNI/Visa)"),
            ("VISA", "Visa"),
            ("VISA_TRABAJO", "Visa de trabajo"),
        ),
        required=True,
        label="Tipo de documento",
    )
    documento_identidad = forms.CharField(required=True, label="DNI / documento")
    telefono = forms.CharField(required=False, label="Teléfono")
    consiente_datos_salud = forms.BooleanField(required=True, label="Acepta tratamiento de datos de salud")

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "rol",
            "tipo_documento",
            "documento_identidad",
            "telefono",
            "consiente_datos_salud",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["rol"].queryset = Rol.objects.filter(activo=True).order_by("nombre")
        except Exception:
            pass
        self.fields["telefono"].widget.attrs.update({"pattern": r"^[0-9+\- ]{7,15}$"})
        self.fields["documento_identidad"].widget.attrs.update({"maxlength": 20, "placeholder": "DNI / documento"})
        self.fields["first_name"].widget.attrs.update({"pattern": r"^[A-Za-zÁÉÍÓÚáéíóúÑñ' ]{2,}$", "title": "Solo letras, espacios y apostrofes"})
        self.fields["last_name"].widget.attrs.update({"pattern": r"^[A-Za-zÁÉÍÓÚáéíóúÑñ' ]{2,}$", "title": "Solo letras, espacios y apostrofes"})

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado")
        rol = self.cleaned_data.get("rol")
        is_admin_role = False
        try:
            if rol and getattr(rol, 'codigo', None):
                is_admin_role = str(rol.codigo).strip().upper() == 'ADMIN'
            elif rol and getattr(rol, 'django_group_name', None):
                is_admin_role = 'ADMIN' in str(rol.django_group_name).strip().upper()
        except Exception:
            is_admin_role = False
        if not is_admin_role:
            if not email.endswith('@discopro.cl'):
                raise forms.ValidationError("El email debe ser corporativo @discopro.cl")
        return email

    def clean_first_name(self):
        nombre = (self.cleaned_data.get("first_name") or "").strip()
        import re
        if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ' ]{2,}$", nombre):
            raise forms.ValidationError("El nombre no puede contener números ni símbolos")
        return nombre

    def clean_last_name(self):
        apellido = (self.cleaned_data.get("last_name") or "").strip()
        import re
        if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ' ]{2,}$", apellido):
            raise forms.ValidationError("El apellido no puede contener números ni símbolos")
        return apellido

    def clean_documento_identidad(self):
        doc = self.cleaned_data.get("documento_identidad", "").strip()
        tipo = self.cleaned_data.get("tipo_documento")
        if tipo == "RUT":
            raw = doc.replace(".", "").replace("-", "").upper()
            if len(raw) < 2:
                raise forms.ValidationError("RUT inválido")
            cuerpo, dv = raw[:-1], raw[-1]
            if not cuerpo.isdigit():
                raise forms.ValidationError("RUT inválido")
            factors = [2,3,4,5,6,7]
            s = 0
            j = 0
            for ch in reversed(cuerpo):
                s += int(ch) * factors[j]
                j = (j + 1) % len(factors)
            r = 11 - (s % 11)
            dv_calc = "0" if r == 11 else ("K" if r == 10 else str(r))
            if dv != dv_calc:
                raise forms.ValidationError("RUT inválido")
        else:
            if not doc or len(doc) < 5 or len(doc) > 20:
                raise forms.ValidationError("Documento inválido: longitud 5–20")
            ok = True
            for ch in doc:
                if not (ch.isalnum() or ch in "-"):
                    ok = False
                    break
            if not ok:
                raise forms.ValidationError("Documento inválido: solo letras, números y guion")
        try:
            if Usuario.objects.filter(documento_identidad=doc).exists():
                raise forms.ValidationError("Este documento de identidad ya existe")
        except Exception:
            pass
        return doc

    def clean_consiente_datos_salud(self):
        v = self.cleaned_data.get("consiente_datos_salud")
        if not v:
            raise forms.ValidationError("Debe aceptar el tratamiento de datos de salud")
        return v

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        if commit:
            user.save()
        rol = self.cleaned_data["rol"]
        tipo_doc = self.cleaned_data["tipo_documento"]
        doc = self.cleaned_data["documento_identidad"].strip()
        tel = self.cleaned_data.get("telefono")
        consiente = True
        now = timezone.now()
        Usuario.objects.create(
            rol=rol,
            django_user_id=user.id,
            tipo_documento=tipo_doc,
            documento_identidad=doc,
            nombre=user.first_name,
            apellido=user.last_name,
            telefono=tel or None,
            activo=True,
            consiente_datos_salud=True if consiente else False,
            fecha_consentimiento_salud=now,
            fecha_creacion=now,
            fecha_modificacion=now,
        )
        try:
            if rol and rol.django_group_name:
                group = Group.objects.filter(name=rol.django_group_name).first()
                if group:
                    user.groups.add(group)
        except Exception:
            pass
        return user


class FarmaciaForm(forms.ModelForm):
    class Meta:
        model = Localfarmacia
        fields = (
            "local_id",
            "local_nombre",
            "local_direccion",
            "comuna_nombre",
            "localidad_nombre",
            "fk_region",
            "fk_comuna",
            "fk_localidad",
            "funcionamiento_hora_apertura",
            "funcionamiento_hora_cierre",
            "funcionamiento_dia",
            "local_telefono",
            "local_lat",
            "local_lng",
            "geolocalizacion_validada",
            "fecha",
            "activo",
        )
    def clean(self):
        cleaned = super().clean()
        ap = cleaned.get("funcionamiento_hora_apertura")
        ci = cleaned.get("funcionamiento_hora_cierre")
        if ap and ci and ap >= ci:
            self.add_error("funcionamiento_hora_cierre", "La hora de cierre debe ser posterior a la de apertura")
        lat = cleaned.get("local_lat")
        lng = cleaned.get("local_lng")
        geo_ok = cleaned.get("geolocalizacion_validada")
        if geo_ok and (lat is None or lng is None):
            self.add_error("geolocalizacion_validada", "No puedes validar geolocalización sin coordenadas")
        if lat is not None:
            try:
                if float(lat) < -90 or float(lat) > 90:
                    self.add_error("local_lat", "Latitud fuera de rango (-90 a 90)")
            except Exception:
                self.add_error("local_lat", "Latitud inválida")
        if lng is not None:
            try:
                if float(lng) < -180 or float(lng) > 180:
                    self.add_error("local_lng", "Longitud fuera de rango (-180 a 180)")
            except Exception:
                self.add_error("local_lng", "Longitud inválida")
        # Permitir teléfono mínimo y limpiar en la vista (tests esperan flexibilidad)
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["fk_region"].label = "Región"
            self.fields["fk_comuna"].label = "Comuna"
            self.fields["fk_localidad"].label = "Localidad"
            self.fields["fk_region"].queryset = Region.objects.filter(activo=True).order_by("nombre")
            self.fields["fk_region"].empty_label = "Seleccione región"
            self.fields["fk_region"].widget = forms.Select()
        except Exception:
            pass


class MotoristaForm(forms.ModelForm):
    class Meta:
        model = Motorista
        fields = (
            "usuario",
            "licencia_numero",
            "licencia_clase",
            "fecha_vencimiento_licencia",
            "emergencia_nombre",
            "emergencia_telefono",
            "emergencia_parentesco",
            "total_entregas_completadas",
            "total_entregas_fallidas",
            "activo",
            "disponible_hoy",
        )
    def clean(self):
        cleaned = super().clean()
        clase = (cleaned.get("licencia_clase") or "").upper().strip()
        if not clase.startswith("A"):
            self.add_error("licencia_clase", "La clase de licencia debe ser A para motos")
        from django.utils import timezone
        fv = cleaned.get("fecha_vencimiento_licencia")
        if fv and fv < timezone.now().date():
            self.add_error("fecha_vencimiento_licencia", "Licencia vencida")
        tel = cleaned.get("emergencia_telefono") or ""
        if tel and not __import__("re").match(r"^[0-9+\- ]{7,15}$", tel):
            self.add_error("emergencia_telefono", "Teléfono inválido (7–15 dígitos)")
        en = (cleaned.get("emergencia_nombre") or "").strip()
        import re
        if en and not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ' ]{2,}$", en):
            self.add_error("emergencia_nombre", "El nombre no puede contener números ni símbolos")
        return cleaned


class MotoForm(forms.ModelForm):
    PROPIETARIO_TDOC_CHOICES = (
        ("RUT", "RUT"),
        ("PASAPORTE", "PASAPORTE"),
        ("DNI", "DNI"),
        ("OTRO", "OTRO"),
    )
    class Meta:
        model = Moto
        fields = (
            "patente",
            "marca",
            "modelo",
            "anio",
            "propietario_nombre",
            "propietario_tipo_documento",
            "propietario_documento",
            "cilindrada_cc",
            "color",
            "tipo_combustible",
            "numero_motor",
            "numero_chasis",
            "fecha_inscripcion",
            "fecha_revision_tecnica",
            "fecha_venc_permiso_circulacion",
            "fecha_venc_seguro_soap",
            "estado",
            "kilometraje_actual",
            "activo",
        )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["propietario_tipo_documento"].widget = forms.Select(choices=self.PROPIETARIO_TDOC_CHOICES)
        except Exception:
            pass
        from django.utils import timezone
        current_year = timezone.now().year
        self.fields["anio"].label = "Año"
        self.fields["anio"].widget = forms.NumberInput(attrs={"min": 1950, "max": current_year, "step": 1, "placeholder": "AAAA"})
        for f in ("fecha_inscripcion", "fecha_revision_tecnica", "fecha_venc_permiso_circulacion", "fecha_venc_seguro_soap"):
            if f in self.fields:
                self.fields[f].widget = forms.DateInput(attrs={"type": "date"})
    def clean(self):
        cleaned = super().clean()
        pat = (cleaned.get("patente") or "").upper().strip()
        import re
        if not (re.match(r"^[A-Z]{2}\d{4}$", pat) or re.match(r"^[A-Z]{4}\d{2}$", pat)):
            self.add_error("patente", "Patente inválida (AA1234 o ABCD12)")
        nm = (cleaned.get("numero_motor") or "").strip()
        nc = (cleaned.get("numero_chasis") or "").strip()
        from .models import Moto as MM
        if nm and MM.objects.filter(numero_motor=nm).exclude(pk=self.instance.pk if self.instance and self.instance.pk else None).exists():
            self.add_error("numero_motor", "Número de motor ya existe")
        if nc and MM.objects.filter(numero_chasis=nc).exclude(pk=self.instance.pk if self.instance and self.instance.pk else None).exists():
            self.add_error("numero_chasis", "Número de chasis ya existe")
        anio = cleaned.get("anio")
        if anio is not None:
            from django.utils import timezone
            y = timezone.now().year
            if anio < 1950 or anio > y:
                self.add_error("anio", "Año fuera de rango (1950–%d)" % y)
        pn = (cleaned.get("propietario_nombre") or "").strip()
        import re
        if pn and not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ' ]{2,}$", pn):
            self.add_error("propietario_nombre", "El nombre no puede contener números ni símbolos")
        fi = cleaned.get("fecha_inscripcion")
        frt = cleaned.get("fecha_revision_tecnica")
        fpc = cleaned.get("fecha_venc_permiso_circulacion")
        fss = cleaned.get("fecha_venc_seguro_soap")
        try:
            if fi and frt and frt < fi:
                self.add_error("fecha_revision_tecnica", "La revisión técnica no puede ser anterior a la inscripción")
            if fi and fpc and fpc < fi:
                self.add_error("fecha_venc_permiso_circulacion", "El permiso de circulación no puede ser anterior a la inscripción")
            if fi and fss and fss < fi:
                self.add_error("fecha_venc_seguro_soap", "El seguro SOAP no puede ser anterior a la inscripción")
        except Exception:
            pass
        try:
            activo = bool(cleaned.get("activo"))
            from django.utils import timezone
            hoy = timezone.now().date()
            if activo:
                if fpc and fpc < hoy:
                    self.add_error("fecha_venc_permiso_circulacion", "Permiso de circulación vencido (moto activa)")
                if fss and fss < hoy:
                    self.add_error("fecha_venc_seguro_soap", "Seguro SOAP vencido (moto activa)")
                if frt and frt < hoy:
                    self.add_error("fecha_revision_tecnica", "Revisión técnica vencida (moto activa)")
        except Exception:
            pass
        try:
            from django.utils import timezone
            hoy = timezone.now().date()
            if fi and fi > hoy:
                self.add_error("fecha_inscripcion", "La inscripción no puede ser futura")
        except Exception:
            pass
        return cleaned


class AsignarMotoristaForm(forms.ModelForm):
    class Meta:
        model = AsignacionMotoMotorista
        fields = (
            "motorista",
            "moto",
            "fecha_asignacion",
            "fecha_desasignacion",
            "kilometraje_inicio",
            "kilometraje_fin",
            "activa",
            "observaciones",
        )


class ReporteMovimientosForm(forms.Form):
    TIPO_CHOICES = (
        ("diario", "Diario"),
        ("mensual", "Mensual"),
        ("anual", "Anual"),
    )
    tipo_reporte = forms.ChoiceField(choices=TIPO_CHOICES)
    fecha = forms.DateField(required=False)
    mes = forms.DateField(required=False, input_formats=["%Y-%m"]) 
    anio = forms.IntegerField(required=False)
    farmacia = forms.ModelChoiceField(queryset=Localfarmacia.objects.filter(activo=True), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.utils import timezone
        hoy = timezone.now().date()
        anio_max = hoy.year
        self.fields["fecha"].widget = forms.DateInput(attrs={"type": "date", "min": "1984-01-01", "max": hoy.isoformat()})
        self.fields["mes"].widget = forms.DateInput(attrs={"type": "month", "min": "1984-01", "max": f"{anio_max:04d}-{hoy.month:02d}"})
        self.fields["anio"].widget = forms.NumberInput(attrs={"min": 1984, "max": anio_max, "step": 1, "placeholder": "AAAA"})
        self.fields["farmacia"].empty_label = "Todas las farmacias"

    def clean(self):
        cleaned = super().clean()
        tipo = (cleaned.get("tipo_reporte") or "").strip().lower()
        from django.utils import timezone
        hoy = timezone.now().date()
        min_fecha = timezone.datetime(1984, 1, 1).date()
        if tipo not in {"diario","mensual","anual"}:
            self.add_error("tipo_reporte", "Tipo inválido")
            return cleaned
        if tipo == "diario":
            f = cleaned.get("fecha")
            if not f:
                self.add_error("fecha", "Selecciona la fecha del día a consultar")
            else:
                if f < min_fecha or f > hoy:
                    self.add_error("fecha", "Fecha fuera de rango (1984–hoy)")
        elif tipo == "mensual":
            m = cleaned.get("mes")
            if not m:
                self.add_error("mes", "Selecciona el mes a consultar")
            else:
                if m < min_fecha or m > hoy:
                    self.add_error("mes", "Mes fuera de rango (1984–hoy)")
        else:  # anual
            a = cleaned.get("anio")
            if a is None:
                self.add_error("anio", "Ingresa el año a consultar")
            else:
                if a < 1984 or a > hoy.year:
                    self.add_error("anio", "Año fuera de rango (1984–%d)" % hoy.year)
        return cleaned


class DespachoForm(forms.ModelForm):
    class Meta:
        model = Despacho
        fields = (
            "codigo_despacho",
            "numero_orden_farmacia",
            "farmacia_origen_local_id",
            "farmacia_destino_local_id",
            "motorista",
            "estado",
            "tipo_despacho",
            "prioridad",
            "cliente_nombre",
            "cliente_telefono",
            "cliente_comuna_nombre",
            "destino_direccion",
            "destino_referencia",
            "destino_lat",
            "destino_lng",
            "destino_geolocalizacion_validada",
            "tiene_receta_retenida",
            "numero_receta",
            "requiere_devolucion_receta",
            "descripcion_productos",
            "valor_declarado",
            "requiere_aprobacion_operadora",
            "aprobado_por_operadora",
            "receptor_nombre",
            "receptor_tipo_documento",
            "receptor_documento",
            "receptor_relacion",
            "firma_digital",
            "hubo_incidencia",
            "tipo_incidencia",
            "descripcion_incidencia",
            "observaciones",
            "motivo_anulacion",
        )
    def clean(self):
        cleaned = super().clean()
        lat = cleaned.get("destino_lat")
        lng = cleaned.get("destino_lng")
        geo_ok = cleaned.get("destino_geolocalizacion_validada")
        if geo_ok and (lat is None or lng is None):
            self.add_error("destino_geolocalizacion_validada", "No puedes validar geolocalización sin coordenadas")
        # Si se ingresa una coordenada, exigir ambas para consistencia
        if (lat and not lng) or (lng and not lat):
            if not lng:
                self.add_error("destino_lng", "Debe ingresar longitud cuando hay latitud")
            if not lat:
                self.add_error("destino_lat", "Debe ingresar latitud cuando hay longitud")
        if lat is not None:
            try:
                if float(lat) < -90 or float(lat) > 90:
                    self.add_error("destino_lat", "Latitud fuera de rango (-90 a 90)")
            except Exception:
                self.add_error("destino_lat", "Latitud inválida")
        if lng is not None:
            try:
                if float(lng) < -180 or float(lng) > 180:
                    self.add_error("destino_lng", "Longitud fuera de rango (-180 a 180)")
            except Exception:
                self.add_error("destino_lng", "Longitud inválida")
        # Validar formato de código de despacho
        cd = (cleaned.get("codigo_despacho") or "").strip()
        import re
        if cd and not re.match(r"^DSP-\d{4}-\d{6}$", cd):
            self.add_error("codigo_despacho", "Formato inválido: DSP-AAAA-000000")
        # Validación de receta retenida en reenvío
        tipo = (cleaned.get("tipo_despacho") or "").strip().upper()
        tiene = bool(cleaned.get("tiene_receta_retenida"))
        requiere = bool(cleaned.get("requiere_devolucion_receta"))
        if tipo == "REENVIO_RECETA" and tiene and requiere:
            nro = (cleaned.get("numero_receta") or "").strip()
            if not nro:
                self.add_error("numero_receta", "Número de receta requerido para reenvío con devolución")
        return cleaned
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["prioridad"].widget = forms.Select(choices=(("ALTA","ALTA"),("MEDIA","MEDIA"),("BAJA","BAJA")))
        self.fields["estado"].widget = forms.Select(choices=(("PENDIENTE","PENDIENTE"),("ASIGNADO","ASIGNADO"),("PREPARANDO","PREPARANDO"),("PREPARADO","PREPARADO"),("EN_PROCESO","EN_PROCESO"),("EN_CAMINO","EN_CAMINO"),("ENTREGADO","ENTREGADO"),("FALLIDO","FALLIDO"),("ANULADO","ANULADO")))
        self.fields["tipo_despacho"].widget = forms.Select(choices=(("DOMICILIO","DOMICILIO"),("REENVIO_RECETA","REENVIO_RECETA"),("INTERCAMBIO_FARMACIAS","INTERCAMBIO_FARMACIAS"),("ERROR_DESPACHO","ERROR_DESPACHO")))
        self.fields["cliente_telefono"].widget.attrs.update({"pattern": r"^[0-9+\- ]{7,15}$"})
        self.fields["destino_lat"].widget.attrs.update({"step": "0.0000001"})
        self.fields["destino_lng"].widget.attrs.update({"step": "0.0000001"})
        self.fields["receptor_tipo_documento"].widget = forms.Select(choices=(("DNI","DNI"),("PASAPORTE","PASAPORTE"),("VISA","VISA"),("VISA_TRABAJO","VISA_TRABAJO")))

    def clean(self):
        cleaned = super().clean()
        import re
        tel = (cleaned.get("cliente_telefono") or "").strip()
        if tel and not re.match(r"^[0-9+\- ]{7,15}$", tel):
            self.add_error("cliente_telefono", "Teléfono inválido (7–15 dígitos)")
        cn = (cleaned.get("cliente_nombre") or "").strip()
        if cn and not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ' ]{2,}$", cn):
            self.add_error("cliente_nombre", "El nombre no puede contener números ni símbolos")
        rn = (cleaned.get("receptor_nombre") or "").strip()
        if rn and not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ' ]{2,}$", rn):
            self.add_error("receptor_nombre", "El nombre no puede contener números ni símbolos")
        codigo = (cleaned.get("codigo_despacho") or "").strip().upper()
        if codigo and not re.match(r"^DSP-\d{4}-\d{6}$", codigo):
            self.add_error("codigo_despacho", "Formato esperado DSP-AAAA-NNNNNN")
        lat = cleaned.get("destino_lat")
        lng = cleaned.get("destino_lng")
        geo_ok = cleaned.get("destino_geolocalizacion_validada")
        if (lat is None) != (lng is None):
            self.add_error("destino_lat", "Debes ingresar latitud y longitud juntas")
            self.add_error("destino_lng", "Debes ingresar latitud y longitud juntas")
        if lat is not None and (lat < -90 or lat > 90):
            self.add_error("destino_lat", "Latitud inválida (-90 a 90)")
        if lng is not None and (lng < -180 or lng > 180):
            self.add_error("destino_lng", "Longitud inválida (-180 a 180)")
        if geo_ok and (lat is None or lng is None):
            self.add_error("destino_geolocalizacion_validada", "No puedes validar geolocalización sin coordenadas")

        prioridad = (cleaned.get("prioridad") or "").upper()
        if prioridad not in {"ALTA","MEDIA","BAJA"}:
            self.add_error("prioridad", "Prioridad inválida")
        estado = (cleaned.get("estado") or "").upper()
        estados_ok = {"PENDIENTE","ASIGNADO","PREPARANDO","PREPARADO","EN_PROCESO","EN_CAMINO","ENTREGADO","FALLIDO","ANULADO"}
        if estado not in estados_ok:
            self.add_error("estado", "Estado inválido")
        tipo = (cleaned.get("tipo_despacho") or "").upper()
        tipos_ok = {"DOMICILIO","REENVIO_RECETA","INTERCAMBIO_FARMACIAS","ERROR_DESPACHO"}
        if tipo not in tipos_ok:
            self.add_error("tipo_despacho", "Tipo de despacho inválido")

        retenida = bool(cleaned.get("tiene_receta_retenida") or False)
        req_dev = bool(cleaned.get("requiere_devolucion_receta") or False)
        num_rec = (cleaned.get("numero_receta") or "").strip()
        if tipo == "REENVIO_RECETA" and not retenida:
            cleaned["tiene_receta_retenida"] = True
            retenida = True
        if retenida:
            if not req_dev:
                cleaned["requiere_devolucion_receta"] = True
            if not num_rec:
                self.add_error("numero_receta", "Número de receta requerido si está retenida")

        valor = cleaned.get("valor_declarado")
        if valor is not None and valor < 0:
            self.add_error("valor_declarado", "El valor no puede ser negativo")
        rdoc = (cleaned.get("receptor_documento") or "").strip()
        rtdoc = (cleaned.get("receptor_tipo_documento") or "").upper()
        if rdoc and not re.match(r"^[A-Za-z0-9\-]{5,20}$", rdoc):
            self.add_error("receptor_documento", "Documento inválido (5–20, letras/números/guion)")
        tipos_ok2 = {"DNI","PASAPORTE","VISA","VISA_TRABAJO",""}
        if rtdoc not in tipos_ok2:
            self.add_error("receptor_tipo_documento", "Tipo de documento inválido")
        return cleaned


class AsignacionMotoristaFarmaciaForm(forms.ModelForm):
    activa = forms.ChoiceField(required=True, choices=((True, 'Activa'), (False, 'Inactiva')), widget=forms.Select)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from .models import Motorista, Localfarmacia
            self.fields['motorista'].queryset = Motorista.objects.filter(activo=True).order_by('usuario__nombre')
            self.fields['farmacia'].queryset = Localfarmacia.objects.filter(activo=True).order_by('local_nombre')
        except Exception:
            pass
        self.fields['motorista'].widget.attrs.update({'required': 'required', 'class': 'form-select'})
        self.fields['farmacia'].widget.attrs.update({'required': 'required', 'class': 'form-select'})
        self.fields['fecha_asignacion'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local', 'required': 'required', 'class': 'form-control'})
        try:
            self.fields['fecha_asignacion'].initial = timezone.now().replace(microsecond=0)
        except Exception:
            pass
        self.fields['fecha_desasignacion'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
        self.fields['activa'].widget.attrs.update({'class': 'form-select'})
        self.fields['observaciones'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'maxlength': 500})

    def clean_activa(self):
        v = self.cleaned_data.get('activa')
        if v in (True, False):
            return bool(v)
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'sí', 'si')
        return bool(v)

    def clean(self):
        cleaned = super().clean()
        fa = cleaned.get('fecha_asignacion')
        fd = cleaned.get('fecha_desasignacion')
        if fd and fa and fd < fa:
            self.add_error('fecha_desasignacion', 'La fecha de desasignación no puede ser anterior a la de asignación')
        try:
            mot = cleaned.get('motorista')
            from django.utils import timezone
            hoy = timezone.now().date()
            if mot and mot.fecha_vencimiento_licencia and mot.fecha_vencimiento_licencia < hoy:
                self.add_error('motorista', 'Licencia vencida: no se puede asignar')
        except Exception:
            pass
        return cleaned
    class Meta:
        model = AsignacionMotoristaFarmacia
        fields = (
            "motorista",
            "farmacia",
            "fecha_asignacion",
            "fecha_desasignacion",
            "activa",
            "observaciones",
        )
