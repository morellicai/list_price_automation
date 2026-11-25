# List Price Automation (Automação de Lista de Preços)

Este projeto é uma automação desenvolvida em Python projetada para interagir com o sistema SAP, processar listas de itens e preços, e enviar notificações ou relatórios automáticos por e-mail.

## 📁 Estrutura do Projeto

Abaixo está a estrutura principal dos arquivos do projeto:

```
list_price_automation/
├── app.py                  # Ponto de entrada principal (orquestrador da automação)
├── requirements.txt        # Lista de dependências e bibliotecas Python
├── test_suite.py           # Suíte de testes automatizados
└── services/               # Diretório contendo as regras de negócio e integrações
    ├── body_email_gen.py   # Responsável por gerar/formatar o corpo do e-mail
    ├── email_service.py    # Módulo responsável por disparar os e-mails
    ├── lista_itens.py      # Lógica para extração ou processamento da lista de itens
    └── login_logout_sap.py # Gerenciamento de sessão (login e logout) no SAP

```

## 🚀 Funcionalidades

* **Integração SAP:** Conexão automatizada para login e logout de forma segura (`login_logout_sap.py`).

* **Processamento de Dados:** Leitura e estruturação da lista de itens e preços (`lista_itens.py`).

* **Comunicação Automatizada:** Geração de relatórios dinâmicos (`body_email_gen.py`) e envio direto para os destinatários via e-mail (`email_service.py`).

* **Cobertura de Testes:** Scripts de teste integrados para garantir a estabilidade das funções principais (`test_suite.py`).

## 🛠️ Pré-requisitos

* [Python 3.x](https://www.python.org/downloads/) instalado.

* Credenciais válidas e ambiente SAP configurado e acessível pela máquina onde o script será executado.

* Dependências do projeto listadas no `requirements.txt`.

## ⚙️ Instalação

1. Clone o repositório ou faça o download dos arquivos.

2. É recomendado criar um ambiente virtual (opcional, mas recomendado):

   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. Instale as bibliotecas necessárias:

   ```
   pip install -r requirements.txt
   ```

## ▶️ Como executar

Para iniciar a automação, basta rodar o arquivo principal na raiz do projeto:

```
python app.py
```

## 🧪 Como rodar os testes

Para garantir que os serviços (SAP, E-mail, Gerador) estão funcionando corretamente antes de colocar em produção, execute a suíte de testes:

```
python test_suite.py
```

*Documentação gerada automaticamente com base na estrutura atual do projeto.*
