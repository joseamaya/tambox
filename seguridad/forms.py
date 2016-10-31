# -*- coding: utf-8 -*- 
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout


class FormularioCambioPassword(forms.Form):
    password_actual = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_nueva = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_verificacion = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(FormularioCambioPassword, self).__init__(*args, **kwargs)

    def clean_password_actual(self):
        if self.cleaned_data.get('password_actual') and not self.request.user.check_password(
                self.cleaned_data['password_actual']):
            raise ValidationError('La contraseña ingresada no es la actual.')
        return self.cleaned_data['password_actual']

    def clean_password_nueva(self):
        if self.cleaned_data.get('password_nueva') and not len(self.cleaned_data['password_nueva']) > 6:
            raise ValidationError('La nueva contraseña no cumple los requisitos de seguridad mínimos.')
        return self.cleaned_data['password_nueva']

    def clean_password_verificacion(self):
        if self.cleaned_data.get('password_nueva') and self.cleaned_data.get('password_verificacion') and \
                        self.cleaned_data['password_nueva'] != self.cleaned_data['password_verificacion']:
            raise ValidationError('Las contraseñas no coinciden')
        return self.cleaned_data['password_verificacion']

    def clean(self):
        usuario = self.request.user
        password_actual = self.cleaned_data.get('password_actual')
        password_nueva = self.cleaned_data.get('password_nueva')
        password_verificacion = self.cleaned_data.get('password_verificacion')
        if password_actual and password_nueva and password_verificacion:
            password_nueva = self.clean_password_nueva()
            usuario.set_password(password_nueva)
            usuario.save()
            logout(self.request)


class FormularioLogin(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(FormularioLogin, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Usuario'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['placeholder'] = 'Contraseña'
