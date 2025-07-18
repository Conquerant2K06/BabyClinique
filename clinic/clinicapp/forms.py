from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Entrez votre email',
            'autocomplete': 'email'
        })
    )
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personnalisation du champ username
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': '...',
            'autocomplete': 'username'
        })
        
        # Personnalisation du champ password1
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': '...',
            'autocomplete': 'new-password'
        })
        
        # Personnalisation du champ password2
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': '...',
            'autocomplete': 'new-password'
        })
        
        # Personnalisation des labels
        self.fields['username'].label = 'Nom d\'utilisateur'
        self.fields['email'].label = 'Adresse email'
        self.fields['password1'].label = 'Mot de passe'
        self.fields['password2'].label = 'Confirmer le mot de passe'
        
        # Suppression des textes d'aide par défaut
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Un utilisateur avec cette adresse email existe déjà.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class CustomLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Nom d\'utilisateur ou email',
            'autocomplete': 'username'
        }),
        label='Nom d\'utilisateur'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Mot de passe',
            'autocomplete': 'current-password'
        }),
        label='Mot de passe'
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Se souvenir de moi'
    )

from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(label='Votre Nom', max_length=100)
    email = forms.EmailField(label='Votre Email')
    subject = forms.CharField(label='Sujet', max_length=100)
    message = forms.CharField(label='Message', widget=forms.Textarea)
