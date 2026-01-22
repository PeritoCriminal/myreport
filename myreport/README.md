# MyReport | Sistema EPCL

Plataforma web desenvolvida em Django destinada ao apoio à produção,
organização e gestão de conteúdos técnico-científicos e periciais,
com foco em fluxos de trabalho relacionados à segurança pública.

O projeto foi concebido a partir de necessidades reais da atividade
pericial, priorizando organização, rastreabilidade, padronização textual
e evolução gradual das funcionalidades.

---

## 🎯 Finalidade do projeto

O **MyReport** teve como objetivo:

- Apoiar a elaboração e organização de laudos técnicos e periciais;
- Centralizar documentos técnicos e científicos;
- Oferecer recursos auxiliares para análise, revisão e validação de conteúdo;
- Servir como base para evolução futura voltada a ambientes institucionais
  e governamentais.

O sistema encontra-se em **desenvolvimento contínuo**, com foco inicial
em uso interno e experimental.

---

## 🧩 Principais módulos

O projeto é estruturado de forma modular, por meio de apps Django:

- **accounts**  
  Gerenciamento de usuários, perfis, preferências e autenticação.

- **home**  
  Páginas iniciais e navegação principal do sistema.

- **social_net**  
  Funcionalidades sociais internas (postagens, interações e controle de acesso).

- **technical_repository**  
  Repositório de documentos técnicos organizados por tema e autoria.

- **report_maker**  
  Núcleo de elaboração de laudos, organização de objetos examinados,
  imagens, textos técnicos e geração de documentos.

- **devtools**  
  Painel interno de testes e validações, incluindo páginas de erro
  (403, 404, 500) e futuras ferramentas de diagnóstico.

---

## 🛠 Tecnologias utilizadas

- Python 3.x  
- Django 5.x  
- HTML5  
- CSS3  
- Bootstrap 5  
- JavaScript  
- SQLite (ambiente de desenvolvimento)  
- Git / GitHub  

---

## 📂 Estrutura geral do projeto

```text
myreport/
├── accounts/
├── common/
├── devtools/
├── groups/
├── home/
├── institutions/
├── media/
├── myreport/
├── report_maker/
├── social_net/
├── technical_repository/
├── templates/
├── users/
├── manage.py
├── db.sqlite3
├── README.md
└── requirements.txt
```

A estrutura segue o padrão de projetos Django modulares, com separação
clara de responsabilidades por app.

---

## 🚀 Execução em ambiente de desenvolvimento

1. Clonar o repositório:
   ```bash
   git clone https://github.com/seu-usuario/myreport.git

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py runserver

---

## 📄 Licença

Este projeto é de autoria de Marcos Capristo.

O código-fonte e a estrutura do sistema destinam-se a uso experimental
e interno. A utilização, reprodução, modificação ou redistribuição,
total ou parcial, depende de autorização expressa do autor.

Todos os direitos reservados.
