# path = accountsapp/models/custom_user_model.py

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class CustomUserModel(AbstractUser):
        
    def clean(self):
        super().clean()
        self.validate_email_domain()

    def validate_email_domain(self):
        """
        Essa validação restringe o acesso para políciais civis ou científicos com seus e-mails institucionais ativos.
        """
        valid_domains = [
            '@policiacientifica.sp.gov.br', 
            '@policiacivil.sp.gov.br',
            ]
        if self.email and not any(self.email.endswith(domain) for domain in valid_domains):
            raise ValidationError({
                'email': "O e-mail deve pertencer aos domínios: "
                         "@policiacientifica.sp.gov.br ou @policiacivil.sp.gov.br."
            })

    def __str__(self):
        return self.username
