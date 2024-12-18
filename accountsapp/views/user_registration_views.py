from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from accountsapp.forms import UserRegistrationForm
# from accountsapp.views.decorators import login_forbidden
from accountsapp.models import CustomUserModel


User = get_user_model()

# @login_forbidden
def user_registration_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Desativa o usuário até a verificação de e-mail
            user.save()
            send_verification_email(user)
            messages.success(request, "Cadastro realizado com sucesso! Verifique seu e-mail para concluir a ativação.")
            return redirect('home')
        else:
            messages.error(request, "Erro no cadastro. Verifique os campos e tente novamente.")
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def send_verification_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_link = reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    verification_url = f"{settings.SITE_URL}{verification_link}"

    subject = "Verifique seu e-mail para concluir o cadastro"
    message = f"Por favor, clique no link abaixo para verificar seu e-mail:\n{verification_url}"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            user.is_active = True 
            user.save()
            messages.success(request, "Seu e-mail foi verificado com sucesso! Você pode fazer login.")
            # return redirect('login') 
            return redirect('user')
        else:
            messages.error(request, "O link de verificação é inválido ou expirou.")
            return redirect('home')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, "O link de verificação é inválido ou expirou.")
        return redirect('home')


def confirm_email(request, token):
    # Obtendo o usuário que corresponde ao token de confirmação
    user = get_object_or_404(CustomUserModel, confirmation_token=token)
    
    # Ativa o usuário
    user.is_active = True
    user.save()

    # Login automático após a confirmação
    login(request, user)

    return redirect('complete_registration_form')
