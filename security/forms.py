# -*- coding: utf-8 -*- 
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirmation = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(PasswordChangeForm, self).__init__(*args, **kwargs)

    def clean_password_actual(self):
        if self.cleaned_data.get('old_password') and not self.request.user.check_password(
                self.cleaned_data['old_password']):
            raise ValidationError('La contraseña ingresada no es la actual.')
        return self.cleaned_data['old_password']

    def clean_password_nueva(self):
        if self.cleaned_data.get('new_password') and not len(self.cleaned_data['new_password']) > 6:
            raise ValidationError('La nueva contraseña no cumple los requisitos de seguridad mínimos.')
        return self.cleaned_data['new_password']

    def clean_password_verificacion(self):
        if self.cleaned_data.get('new_password') and self.cleaned_data.get('password_confirmation') and\
                self.cleaned_data['new_password'] != self.cleaned_data['password_confirmation']:
            raise ValidationError('Las contraseñas no coinciden')
        return self.cleaned_data['password_confirmation']

    def clean(self):
        user = self.request.user
        old_password = self.cleaned_data.get('old_password')
        new_password = self.cleaned_data.get('new_password')
        password_confirmation = self.cleaned_data.get('password_confirmation')
        if old_password and new_password and password_confirmation:
            new_password = self.clean_password_nueva()
            user.set_password(new_password)
            user.save()
            logout(self.request)


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Usuario'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['placeholder'] = 'Contraseña'
