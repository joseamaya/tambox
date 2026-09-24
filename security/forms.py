# -*- coding: utf-8 -*- 
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout

from tambox.forms import BootstrapFormMixin


class PasswordChangeForm(BootstrapFormMixin, forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput())
    new_password = forms.CharField(widget=forms.PasswordInput())
    password_confirmation = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs['autocomplete'] = 'current-password'
        self.fields['new_password'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password_confirmation'].widget.attrs['autocomplete'] = 'new-password'

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if old_password and not self.request.user.check_password(old_password):
            raise ValidationError('La contraseña ingresada no es la actual.')
        return old_password

    def clean_new_password(self):
        new_password = self.cleaned_data.get('new_password')
        if new_password and not len(new_password) > 6:
            raise ValidationError('La nueva contraseña no cumple los requisitos de seguridad mínimos.')
        return new_password

    def clean_password_confirmation(self):
        new_password = self.cleaned_data.get('new_password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if new_password and password_confirmation and new_password != password_confirmation:
            raise ValidationError('Las contraseñas no coinciden')
        return password_confirmation

    def clean(self):
        user = self.request.user
        old_password = self.cleaned_data.get('old_password')
        new_password = self.cleaned_data.get('new_password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if old_password and new_password and password_confirmation:
            user.set_password(new_password)
            user.save()
            logout(self.request)
        return self.cleaned_data


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Usuario',
            'autocomplete': 'username',
            'autofocus': True,
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password',
        })
