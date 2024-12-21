# accountsapp/views/user_registration.py


from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model, authenticate, login
from accountsapp.forms import UserRegistrationForm, UserLoginForm, CompleteRegistrationForm
from django.contrib.auth.hashers import make_password
from accountsapp.models import CustomUserModel


User = get_user_model()

def user_registration_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False) 
            password = form.cleaned_data['password']
            user.password = make_password(password)
            user.is_active = False  
            user.save()  
            send_verification_email(user)
            messages.success(request, "Cadastro realizado com sucesso! Verifique seu e-mail para concluir a ativação.")
            return redirect('confirmation_email') 
        else:
            messages.error(request, "Erro no cadastro. Verifique os campos e tente novamente.")
    else:
        form = UserRegistrationForm() 

    return render(request, 'register.html', {'form': form})



def confirmation_email_view(request):
    return render(request, 'confirmation_email.html')



def complete_registration_view(request, id):
    user = get_object_or_404(CustomUserModel, id=id)
    
    if request.method == 'POST':
        form = CompleteRegistrationForm(request.POST, request.FILES, instance=user, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = CompleteRegistrationForm(instance=user, user=request.user)
    
    user_img = user.profile_picture.url if user.profile_picture else '/media/profile_pics/usercommonimg.jpg'

    context = {
        'form': form,
        'user': user,
        'user_img': user_img,
        'welcome_message': f"Complete o cadastro de {user.username}.",
    }
    return render(request, 'complete_registration.html', context)






def send_verification_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    verification_link = reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    verification_url = f"{settings.SITE_URL}{verification_link}"

    subject = "Verifique seu e-mail para concluir o cadastro"
    message = f"Por favor, clique no link abaixo para verificar seu e-mail:\n{verification_url}"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    try:
        send_mail(subject, message, from_email, recipient_list)
    except Exception as e:
        messages.error(user, f"Erro ao enviar o e-mail: {str(e)}")

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Seu e-mail foi verificado com sucesso! Faça login para continuar.")
            return redirect('login')
        else:
            messages.error(request, "O link de verificação é inválido ou expirou.")
            return redirect('home')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, "O link de verificação é inválido ou expirou.")
        return redirect('home')




def user_login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'home')  # Verifica se existe um 'next' no URL
                messages.success(request, "Login realizado com sucesso!")
                return redirect(next_url)  # Redireciona para a página original ou 'home'
            else:
                messages.error(request, "Credenciais inválidas. Verifique seu nome de usuário e senha.")
        else:
            messages.error(request, "Erro ao validar o formulário. Por favor, corrija os campos destacados.")
    else:
        form = UserLoginForm()

    context = {
        'form': form,
    }

    return render(request, 'user_login.html', context)
