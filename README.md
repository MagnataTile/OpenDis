<p align="center">
  <img src="./logo.png" alt="OpenDis" width="850">
</p>

<h1 align="center">OpenDis</h1>

<p align="center">
  <strong>VPN Automation & Discord Launcher</strong>
</p>

<p align="center">
  Gerenciamento de perfis OpenVPN, conexão automatizada, verificação de IP e inicialização controlada do Discord.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white">
  <img src="https://img.shields.io/badge/OpenVPN-Community-EA7E20?style=for-the-badge&logo=openvpn&logoColor=white">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Discord-Launcher-5865F2?style=for-the-badge&logo=discord&logoColor=white">
</p>

---

## 🛡️ Sobre

O **OpenDis** é uma aplicação Windows criada para centralizar o uso de VPN através do **OpenVPN Community** e controlar a inicialização do Discord somente depois que a conexão VPN estiver pronta.

A aplicação gerencia os perfis `.ovpn`, credenciais, conexão, validação do túnel, verificação do IP público e inicialização do Discord.

O fluxo principal é:

```text
OpenDis
   ↓
Selecionar VPN
   ↓
Verificar credenciais
   ↓
Iniciar OpenVPN
   ↓
Aguardar conexão
   ↓
Confirmar IP público
   ↓
Iniciar Discord
   ↓
Utilizar normalmente
   ↓
Encerrar OpenVPN
```

---

# ⚠️ Importante antes de usar

## Discord deve estar fechado

O **Discord precisa estar completamente fechado antes de iniciar o OpenDis**.

O OpenDis é responsável por iniciar o Discord **depois que a VPN estiver conectada e validada**.

Portanto, antes de abrir o OpenDis:

```text
Discord
   ↓
FECHADO
   ↓
Abrir OpenDis
   ↓
Conectar VPN
   ↓
Validar VPN
   ↓
OpenDis inicia o Discord
```

Se o Discord já estiver aberto, o fluxo de inicialização controlada pode não funcionar corretamente.

---

## ⏳ Discord pode ficar alguns segundos sem conexão

Ao fechar o OpenDis, é **normal que o Discord permaneça alguns segundos mostrando ausência de conexão**.

Isso acontece porque o Discord pode levar um pequeno período para perceber a alteração da conexão de rede após o encerramento da VPN.

Não é necessário reiniciar o Discord imediatamente.

A conexão normalmente retorna sozinha após alguns segundos.

```text
OpenDis fechado
      ↓
VPN encerrada
      ↓
Discord pode ficar alguns segundos sem conexão
      ↓
Discord reconecta automaticamente
```

---

## 🚨 Discord carregando indefinidamente ou compartilhamento bloqueado

Se o Discord ficar preso em:

```text
Carregando...
Carregando...
Carregando...
```

ou se, mesmo depois de iniciar o compartilhamento, ele continuar **bloqueado**, faça o seguinte:

### Troque o perfil `.ovpn`

O problema pode estar relacionado ao servidor VPN utilizado pelo perfil atual.

```text
Discord com problema
       ↓
Trocar perfil .ovpn
       ↓
Conectar novamente
       ↓
Testar Discord
```

Se estiver utilizando a opção **VPN ALEATÓRIA**, tente novamente para obter outro perfil disponível.

---

# 🚀 Principais recursos

## VPN

* Detecção automática do OpenVPN Community.
* Localização do executável do OpenVPN.
* Gerenciamento de arquivos `.ovpn`.
* Seleção manual de perfil.
* Importação de novos perfis.
* Modo **VPN ALEATÓRIA**.
* Validação do perfil antes da conexão.
* Execução do OpenVPN diretamente pelo sistema.
* Monitoramento do processo OpenVPN.
* Detecção do estabelecimento do túnel.
* Verificação do IP público.
* Desconexão controlada.

## Credenciais

* Identificação de perfis que exigem autenticação.
* Tela para usuário e senha.
* Recuperação de credenciais salvas.
* Preenchimento automático.
* Opção **Lembrar credenciais**.
* Credenciais associadas ao perfil utilizado.
* Possibilidade de alterar as credenciais.
* Navegação entre as etapas do processo.

## Discord

* Detecção da instalação do Discord.
* Inicialização automática após a VPN ser validada.
* Espera pelo início do processo do Discord.
* Controle do fluxo de inicialização.
* Funcionamento integrado ao estado da conexão VPN.

---

# 📂 Perfis VPN

Os perfis `.ovpn` utilizados pelo OpenDis ficam na pasta:

```text
OpenDis/
│
├── README.md
├── logo.png
├── opendis6.py
│
└── VPN/
    ├── perfil1.ovpn
    ├── perfil2.ovpn
    └── ...
```

Ao abrir a seleção de VPN, os perfis disponíveis são apresentados para utilização.

O usuário pode:

* Selecionar um perfil existente.
* Adicionar/importar um novo `.ovpn`.
* Utilizar a **VPN ALEATÓRIA**.

---

# 📥 Adicionando um novo perfil

Para adicionar uma configuração OpenVPN:

```text
Adicionar .ovpn
      ↓
Selecionar arquivo
      ↓
Copiar para OpenDis/VPN
      ↓
Atualizar lista
      ↓
Perfil disponível
```

Depois da importação, o novo perfil poderá ser selecionado normalmente.

---

# 🎲 VPN ALEATÓRIA

A **VPN ALEATÓRIA** foi criada para facilitar a utilização de perfis do **VPNBook**.

Quando essa opção é utilizada, o OpenDis verifica as informações disponíveis, procura um perfil local compatível e, quando necessário, obtém uma nova configuração.

Fluxo:

```text
VPN ALEATÓRIA
      ↓
Obter informações atuais
      ↓
Procurar perfil local
      ↓
Perfil disponível?
    /       \
  SIM       NÃO
   │          │
   │       Obter perfil
   │          ↓
   │       Validar
   │          ↓
   │        Salvar
   │          │
   └────┬─────┘
        ↓
   Usar perfil
        ↓
     OpenVPN
```

As credenciais disponibilizadas pelo serviço também podem ser obtidas para permitir a utilização do perfil.

Como essas informações podem mudar, o OpenDis não depende exclusivamente de valores fixos armazenados localmente.

---

# 🔎 Análise do perfil `.ovpn`

Antes de iniciar a conexão, o OpenDis analisa o perfil selecionado.

Entre outras informações, é verificado se a configuração exige autenticação.

```text
Perfil selecionado
       ↓
Analisar .ovpn
       ↓
Precisa de credenciais?
      /        \
    NÃO        SIM
     │           │
     │      Verificar salvas
     │           │
     │      Usuário/Senha
     │           │
     └─────┬─────┘
           ↓
       Preparação
```

---

# 🔐 Credenciais

Quando o perfil exige autenticação, o OpenDis apresenta os campos necessários:

```text
Usuário:
[________________________]

Senha:
[________________________]

☐ Lembrar credenciais
```

Se existirem credenciais salvas para aquele perfil, elas podem ser carregadas automaticamente.

O usuário também pode alterar os dados antes de iniciar a conexão.

---

## 💾 Lembrar credenciais

A opção **Lembrar credenciais** permite reutilizar os dados em futuras conexões do mesmo perfil.

```text
Primeiro acesso
      ↓
Usuário + senha
      ↓
Lembrar credenciais
      ↓
Dados armazenados
      ↓
Próximo acesso
      ↓
Preenchimento automático
```

As credenciais são vinculadas ao perfil utilizado, permitindo que diferentes `.ovpn` tenham configurações de autenticação diferentes.

---

# ⚙️ Preparação da conexão

Depois da escolha do perfil e do tratamento das credenciais, o OpenDis apresenta a etapa de preparação.

O usuário pode revisar a configuração e iniciar o processo.

```text
Perfil
  ↓
Credenciais
  ↓
Preparação
  ↓
INICIAR
```

O OpenVPN só é iniciado após a confirmação do usuário.

---

# 🔌 Conexão OpenVPN

Ao clicar em **INICIAR**, o OpenDis executa o OpenVPN utilizando:

```text
OpenDis
   │
   ├── Executável OpenVPN
   ├── Perfil .ovpn
   └── Credenciais
          │
          ▼
       OpenVPN
          │
          ▼
      Servidor VPN
```

A aplicação acompanha o processo enquanto a conexão é estabelecida.

---

# 📡 Validação da conexão

O OpenDis não considera simplesmente a abertura do processo OpenVPN como uma conexão concluída.

A aplicação aguarda o estabelecimento efetivo do túnel.

```text
OpenVPN iniciado
      ↓
Monitorar processo
      ↓
Túnel estabelecido
      ↓
Consultar IP público
      ↓
IP confirmado
      ↓
VPN operacional
```

Essa validação reduz o risco de iniciar o Discord antes de a VPN estar realmente funcionando.

---

# 🌐 Verificação do IP público

Depois do estabelecimento do túnel, o OpenDis verifica o IP público atual.

A confirmação ocorre após a conexão VPN:

```text
VPN conectada
     ↓
Consultar IP público
     ↓
IP obtido
     ↓
Conexão confirmada
```

O objetivo é adicionar uma camada de validação ao processo antes da inicialização do Discord.

---

# 💬 Inicialização do Discord

Somente depois da confirmação da VPN e do IP público o OpenDis inicia o Discord.

```text
VPN validada
     ↓
IP confirmado
     ↓
Iniciar Discord
     ↓
Aguardar inicialização
     ↓
Processo pronto
```

Por isso, **o Discord deve estar fechado antes de abrir o OpenDis**.

O OpenDis controla a ordem de inicialização para evitar que o Discord seja aberto antes da etapa VPN.

---

# ⏳ Durante a utilização

Depois que o Discord é iniciado, o OpenDis mantém o fluxo da aplicação e a conexão VPN enquanto o processo estiver sendo utilizado.

A VPN permanece ativa durante a etapa correspondente da execução.

---

# 🔌 Encerramento

Quando o processo termina, o OpenDis encerra o processo do OpenVPN de forma controlada.

```text
Processo encerrado
       ↓
Encerrar OpenVPN
       ↓
VPN desconectada
       ↓
OpenDis finalizado
```

Após isso, o Discord pode levar alguns segundos para reconhecer a alteração da conexão e voltar ao estado normal.

**Esse pequeno período sem conexão é esperado.**

---

# 📁 Estrutura do projeto

Uma estrutura típica do projeto:

```text
OpenDis/
│
├── README.md
├── logo.png
├── opendis6.py
│
└── VPN/
    ├── *.ovpn
    └── perfis VPN armazenados
```

Dependendo da configuração e da versão utilizada, a aplicação também pode criar diretórios e arquivos auxiliares para logs, credenciais e configurações.

---

# 💻 Requisitos

Para executar o OpenDis, são necessários:

* Windows
* OpenVPN Community
* Discord
* Acesso à Internet

Para execução pelo código-fonte:

* Python 3.x
* Dependências listadas em `requirements.txt`

O OpenDis foi desenvolvido considerando um ambiente Windows com o OpenVPN Community instalado.

---

# 🐍 Executando pelo código-fonte

Clone o projeto:

```bash
git clone 
```

Entre no diretório:

```bash
cd OpenDis
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute a aplicação:

```bash
python opendis.py
```

> O nome do arquivo principal pode variar conforme a versão do projeto.

### Antes de executar

Feche completamente o Discord.

```text
Discord fechado
      ↓
Executar OpenDis
      ↓
Selecionar VPN
      ↓
Iniciar conexão
```

---

# 📦 Executável

O OpenDis também pode ser distribuído como executável utilizando **PyInstaller**.

Exemplo:

```bash
pyinstaller --clean --noconfirm OpenDis.spec
```

O executável normalmente será gerado em:

```text
dist/
```

O OpenDis cria as pastas necessárias para VPN e logs no local em que for executado.

Para uma utilização correta, mantenha os arquivos e diretórios necessários junto do `OpenDis.exe`, especialmente a pasta:

```text
VPN/
```

---

# 🔧 Tecnologias

| Tecnologia        | Função                             |
| ----------------- | ---------------------------------- |
| Python            | Linguagem principal                |
| CustomTkinter     | Interface gráfica                  |
| OpenVPN Community | Motor VPN                          |
| `.ovpn`           | Configuração dos perfis VPN        |
| Discord           | Aplicação iniciada após a VPN      |
| HTTP/HTTPS        | Obtenção de informações e recursos |
| PyInstaller       | Geração do executável              |

---

# 🛠️ Tratamento de erros

O OpenDis deve impedir que uma etapa inválida avance silenciosamente.

Entre as situações que podem ser identificadas:

```text
OpenVPN não encontrado
Discord não encontrado
Perfil .ovpn inválido
Arquivo VPN inexistente
Credenciais ausentes
Falha de autenticação
Falha na conexão
Túnel não estabelecido
IP não confirmado
Falha ao iniciar Discord
Processo OpenVPN encerrado inesperadamente
```

Quando uma etapa não pode ser concluída, o fluxo pode ser interrompido ou retornar para uma etapa anterior, conforme o tipo de erro.

---

# 🔐 Segurança

O OpenDis é uma ferramenta local para automação de conexões VPN.

Por segurança:

* Nunca compartilhe arquivos contendo credenciais.
* Não compartilhe seu `.ovpn` sem verificar o conteúdo.
* Arquivos `.ovpn` podem conter informações relacionadas à conexão.
* Não envie arquivos com usuário e senha para outras pessoas.
* Revise os perfis antes de utilizá-los.
* Utilize apenas servidores VPN nos quais você confia.

---

# 🌐 VPNBook

O modo **VPN ALEATÓRIA** utiliza informações disponibilizadas pelo VPNBook para obter configurações e credenciais necessárias ao funcionamento dos perfis.

Como essas informações podem ser alteradas pelo serviço, o OpenDis trata sua obtenção de forma dinâmica.

Isso permite atualizar ou substituir o perfil utilizado sem que o usuário precise realizar manualmente todas as etapas.

---

# ⚠️ Solução de problemas

## Discord não inicia corretamente

Verifique:

1. Se o Discord estava fechado antes de abrir o OpenDis.
2. Se a VPN foi realmente conectada.
3. Se o IP público foi confirmado.
4. Se o Discord não ficou aberto em segundo plano antes da execução.

---

## Discord fica carregando indefinidamente

Se o Discord permanecer carregando e não estabelecer conexão:

```text
Fechar OpenDis
      ↓
Trocar perfil .ovpn
      ↓
Abrir novamente o OpenDis
      ↓
Conectar
      ↓
Testar Discord
```

Se estiver usando **VPN ALEATÓRIA**, tente novamente para obter outro perfil.

---

## Compartilhamento continua bloqueado

Se o Discord iniciar, mas o compartilhamento continuar bloqueado:

**troque o perfil `.ovpn` utilizado.**

O comportamento pode estar relacionado ao servidor VPN atual.

---

## Discord fica sem conexão depois de fechar o OpenDis

Isso pode acontecer por alguns segundos após a desconexão da VPN.

É esperado que o Discord demore um pequeno período para detectar a mudança de rede.

```text
OpenDis fechado
      ↓
VPN encerrada
      ↓
Discord sem conexão por alguns segundos
      ↓
Reconexão automática
```

Aguarde alguns segundos antes de considerar que existe um problema.

---

# 🔄 Fluxo completo

Para entender o funcionamento do OpenDis sem entrar nos detalhes individuais:

```text
┌──────────────────────┐
│      Abrir OpenDis   │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Verificar OpenVPN    │
│ e Discord            │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Selecionar VPN       │
│ Manual / Aleatória   │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Analisar .ovpn       │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Verificar            │
│ credenciais          │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Preparar conexão     │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│      INICIAR         │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│      OpenVPN         │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Túnel estabelecido   │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Confirmar IP público │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│       Discord        │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│     Utilização       │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ Encerrar OpenVPN     │
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│      CONCLUÍDO       │
└──────────────────────┘
```

---

# 🎯 Objetivo

O objetivo do OpenDis é eliminar a necessidade de controlar manualmente várias ferramentas para utilizar uma conexão VPN.

Em vez de alternar entre:

```text
OpenVPN
   ↓
Perfil .ovpn
   ↓
Credenciais
   ↓
Conexão
   ↓
Verificação de IP
   ↓
Discord
```

o usuário utiliza uma única aplicação para controlar esse fluxo.

```text
┌───────────────────────────┐
│          OpenDis          │
├───────────────────────────┤
│ Gerenciamento de VPN      │
│ Perfis .ovpn              │
│ Credenciais               │
│ Controle do OpenVPN        │
│ Verificação de IP         │
│ Inicialização do Discord  │
└───────────────────────────┘
```

---

# 📌 Status

🚧 **Em desenvolvimento**

O projeto continua recebendo melhorias relacionadas à interface, gerenciamento de VPNs, automação, tratamento de erros e experiência de utilização.

---

# ⚠️ Aviso

O OpenDis é uma ferramenta de automação para gerenciamento de conexões VPN e inicialização de aplicações.

O usuário é responsável por:

* Possuir autorização para utilizar os serviços VPN escolhidos.
* Respeitar os termos de uso dos serviços utilizados.
* Utilizar a ferramenta de acordo com as leis aplicáveis.
* Manter suas credenciais protegidas.
* Verificar os arquivos `.ovpn` utilizados.

O projeto não garante anonimato absoluto, segurança absoluta ou proteção contra falhas de terceiros.

---

<p align="center">
  <img src="./logo.png" alt="OpenDis Logo" width="180">
</p>

<p align="center">
  <strong>OpenDis</strong>
  <br>
  VPN Automation & Discord Launcher
  <br><br>
  Powered by MagnataTile
</p>

<p align="center">
  <sub>© 2026 OpenDis — All rights reserved.</sub>
</p>
