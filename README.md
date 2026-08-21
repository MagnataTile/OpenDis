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
  <img src="https://img.shields.io/badge/Android-3DDC84?style=for-the-badge&logo=android&logoColor=white">
  <img src="https://img.shields.io/badge/OpenVPN-Community-EA7E20?style=for-the-badge&logo=openvpn&logoColor=white">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Kotlin-7F52FF?style=for-the-badge&logo=kotlin&logoColor=white">
  <img src="https://img.shields.io/badge/Discord-Launcher-5865F2?style=for-the-badge&logo=discord&logoColor=white">
</p>

---
## 👉 **[📥 Baixar a última versão](https://github.com/MagnataTile/OpenDis/releases)**
## 🛡️ Sobre

**OpenDis** é uma aplicação para Windows e Android criada para simplificar o processo de **conectar uma VPN e iniciar o Discord**.

A proposta é simples: substituir o processo manual de abrir uma VPN, selecionar uma região, conectar à VPN, aguardar a conexão e então abrir o Discord.

Tudo isso é centralizado em uma única aplicação.

O OpenDis funciona como uma **interface de automação para abrir o Discord**. 
### 🔐 O que o OpenDis faz

- Detecta o **OpenVPN Community** e o **Discord** instalado.

- Inicia o OpenVPN automaticamente.
- Aguarda a conexão VPN ser estabelecida.
- Verifica se a conexão VPN está realmente ativa.
- Verifica o IP público após a conexão.
- Inicia o Discord somente após a VPN estar conectada.
- Encerra a conexão VPN pelo próprio aplicativo.
- Fecha o processo do OpenVPN quando a sessão é encerrada.
- Pode utilizar configurações de VPN salvas para agilizar a proxima abertura.

---

# ⚠️ Importante antes de usar

## Discord deve estar fechado

O **Discord precisa estar completamente fechado antes de iniciar o OpenDis**.

O OpenDis é responsável por iniciar o Discord **depois que a VPN estiver conectada e validada**.

Portanto, antes de abrir o OpenDis, feche completamente o Discord.


Se o Discord já estiver aberto, o fluxo de inicialização controlada pode não funcionar corretamente.

---

### ⚠️ Evite buscar partidas online durante a execução do OpenDis

Enquanto o OpenDis estiver em execução, evite iniciar ou buscar partidas em jogos online, pois a conexão poderá estar utilizando um servidor VPN estrangeiro, o que pode direcioná-lo para servidores ou partidas de outras regiões.

---
## ⏳ Discord pode ficar alguns segundos sem conexão

Ao fechar o OpenDis, é **normal que o Discord permaneça alguns segundos mostrando ausência de conexão**.

Isso acontece porque o Discord pode levar um pequeno período para perceber a alteração da conexão de rede após o encerramento da VPN.

Não reinicie o Discord, isso fara você perder o processo de conexão.

A conexão normalmente retorna sozinha após alguns segundos.

### Troque de canal de voz para forçar estabilizacão mais rápida.


---

## 🚨 Discord carregando indefinidamente ou compartilhamento bloqueado

Se o Discord ficar preso em:

```text
Carregando...
Carregando...
Carregando...
```

ou se, mesmo depois de iniciar o compartilhamento, ele continuar **bloqueado**, faça o seguinte:

### 🔄 Troque o perfil `.ovpn`

O problema pode estar relacionado ao servidor VPN utilizado pelo perfil atual.

```text
Desmarque a opção GUARDAR REDE VPNBOOK
       ↓
Clique em VPN ALEATÓRIA VPNBook
       ↓
Clique em Iniciar
       ↓
Aguarde até aparecer "Concluído"
       ↓
Teste o Discord
```

Se a **VPN ALEATÓRIA** não trocar o IP ou o Discord continuar demorando para abrir, tente apagar os arquivos da pasta **VPNBook** criada pelo aplicativo e repita o processo.

### ⚡ Alternativa mais rápida: Proton VPN

Para uma conexão mais rápida e estável, recomendamos criar uma **conta gratuita na Proton VPN** e baixar seu próprio arquivo `.ovpn`.

Isso pode ser mais rápido porque você estará utilizando uma configuração própria, evitando depender dos servidores e perfis compartilhados do VPNBook.

Depois de criar sua conta, baixe a configuração `.ovpn` diretamente pela Proton VPN:

[Veja como baixar uma configuração OpenVPN da Proton VPN](https://protonvpn.com/support/vpn-config-download)

> 💡 **Dica:** uma configuração própria da Proton VPN pode proporcionar uma conexão mais estável e reduzir o tempo de conexão e estabilização da VPN.

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

## 📁 Estrutura de arquivos

O OpenDis mantém seus arquivos organizados no mesmo diretório onde o programa está sendo executado.

Ao iniciar, o programa cria automaticamente as pastas necessárias caso elas ainda não existam.

A estrutura do projeto em execução fica assim:

```text
/
├── OpenDis.exe
│
├── Logs/
│   ├── opendis_20260119_070337.log
│   └── ...
│
└── VPN/
    ├── perfil1.ovpn
    ├── perfil1.ovpn
    ├── ...
    └── VPNBook/
        ├── vpnbook-ca196-tcp443.ovpn
        ├── vpnbook-us17-tcp443.ovpn
        ├── vpnbook-us16-tcp443.ovpn
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
Adicionar / Selecionar .ovpn
      ↓
Selecionar arquivo
      ↓
Clique em Continuar
      ↓
Poderá ou não solicitar senha
      ↓
Iniciar normalmente
```



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


---

# 🔐 Credenciais





Quando o perfil VPN exige autenticação, o OpenDis apresenta os campos necessários:

```text
Usuário:
[________________________]

Senha:
[________________________]

☐ Lembrar credenciais
````

Se o usuário optar por **lembrar as credenciais**, o OpenDis não armazena o usuário ou a senha em arquivos próprios da aplicação.

As credenciais são armazenadas utilizando o **Gerenciador de Credenciais do Windows (Windows Credential Manager)**, ficando sob responsabilidade do próprio sistema operacional.

## 🔒 Segurança das credenciais

O OpenDis **não salva as credenciais em arquivos**


Quando a opção **"Lembrar credenciais"** é utilizada, o OpenDis solicita ao Windows que armazene as credenciais através do mecanismo nativo de gerenciamento de credenciais do sistema.

O fluxo funciona da seguinte forma:

```text
Usuário informa as credenciais
            ↓
         OpenDis
            ↓
Windows Credential Manager
            ↓
Credencial protegida pelo Windows
```

Caso a opção **"Lembrar credenciais"** não seja selecionada, as credenciais são utilizadas apenas durante a sessão atual e não são solicitadas para armazenamento permanente pelo OpenDis.

> **Importante:** o armazenamento e a proteção das credenciais salvas são realizados pelo próprio Windows. O OpenDis apenas solicita ao sistema operacional que armazene ou recupere essas credenciais.





---
# 🔄 Resumo do Fluxo completo do programa

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

# ⚙️ Funcionamento do OpenDis

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

Caso você queira executar o OpenDis diretamente pelo código-fonte, siga os passos abaixo.

Clone o projeto:

```bash
git clone https://github.com/MagnataTile/OpenDis.git
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

Feche completamente o Discord antes de iniciar o OpenDis.


---

# 📦 Versões compiladas

## 🚀 Baixar a versão mais recente

A maneira mais simples de utilizar o OpenDis é baixar a versão já compilada diretamente na página de **Releases** do projeto.

👉 **[📥 Baixar a última versão](https://github.com/MagnataTile/OpenDis/releases)**

Na página de Releases, procure pela versão mais recente. Cada Release disponibiliza as versões do OpenDis para as plataformas suportadas:

- 🪟 **Windows:** arquivo `.exe` ou `.zip`
- 🤖 **Android:** arquivo `.apk`

> **Windows:** não é necessário instalar Python, instalar dependências ou compilar o projeto. Basta baixar a versão `.exe` disponível.

> **Android:** basta baixar o arquivo `.apk` e realizar a instalação no dispositivo Android.
---

# 🛠️ Gerando seu próprio executável

Caso você tenha clonado o projeto e queira gerar sua própria versão do `OpenDis.exe`, é possível utilizar o **PyInstaller**.

Depois de instalar as dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
pyinstaller --clean --noconfirm OpenDis.spec
```

O executável normalmente será gerado dentro da pasta:

```text
dist/
```

Estrutura esperada:

```text
dist/
└── OpenDis.exe
```

Você pode utilizar esse executável para testar sua própria compilação do projeto.
> Lembre-se de criar uma cópia do arquivo anterior e manter as pastas ***build*** e ***dist***  limpa na hora de gerar seu executável.


---

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


# 🔐 Sua Segurança

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
# 🛠️ Tratamento de erros

O OpenDis deve impedir que uma etapa inválida avance silenciosamente.

Entre as situações que podem ser identificadas:

# 📌 Resumo dos principais erros

| Erro | Tratamento | Solução |
|---|---|---|
| OpenVPN não encontrado | Interrompe | Instalar o OpenVPN |
| Discord não encontrado | Interrompe | Instalar o Discord |
| `winget` indisponível | Instalação automática falha | Instalação manual |
| Nenhum `.ovpn` selecionado | Interrompe | Selecionar um perfil |
| Perfil não encontrado | Interrompe | Adicionar o perfil novamente |
| Arquivo não é `.ovpn` | Interrompe | Utilizar um arquivo `.ovpn` válido |
| Credenciais não informadas | Interrompe | Informar usuário e senha |
| `AUTH_FAILED` | Interrompe | Corrigir as credenciais |
| `TLS Error` | Interrompe | Trocar o servidor ou perfil |
| `Cannot open TUN/TAP` | Interrompe | Verificar ou reinstalar o OpenVPN |
| `Options error` | Interrompe | Corrigir ou trocar o perfil `.ovpn` |
| `Connection failed` | Interrompe | Tentar outro servidor |
| OpenVPN encerra antes de conectar | Interrompe | Trocar o perfil `.ovpn` |
| Timeout da VPN | Interrompe | Tentar novamente ou utilizar outro perfil |
| IP não pôde ser consultado | Aviso | Verificar a conexão com a internet e tentar novamente |
| IP não mudou | Aviso | Verificar a conexão ou trocar o perfil |
| Discord não inicia | Interrompe | Reiniciar o Discord e tentar novamente |
| VPN não desconecta | Tenta múltiplos métodos | Verificar o processo `openvpn.exe` |
| Erro durante a execução | Limpeza automática | Consultar os arquivos de log |

Quando uma etapa não pode ser concluída, o fluxo pode ser interrompido ou retornar para uma etapa anterior, conforme o tipo de erro.


---

# 🎯 Objetivo

O objetivo do OpenDis é eliminar a necessidade de controlar manualmente várias ferramentas para utilizar uma conexão VPN.



```text
┌───────────────────────────┐
│          OpenDis          │
├───────────────────────────┤
│ Gerenciamento de VPN      │
│ Perfis .ovpn              │
│ Credenciais               │
│ Controle do OpenVPN       │
│ Verificação de IP         │
│ Inicialização do Discord  │
└───────────────────────────┘
```



# ⚠️ Aviso

O OpenDis é uma ferramenta de automação para gerenciamento de conexões VPN e inicialização de aplicações.

O usuário é responsável por:

* Possuir autorização para utilizar os serviços VPN escolhidos.
* Respeitar os termos de uso dos serviços utilizados.
* Utilizar a ferramenta de acordo com as leis aplicáveis.
* Manter suas credenciais protegidas.
* Verificar os arquivos `.ovpn` utilizados.

> ⚠️  O OpenDis é apenas uma ferramenta de automação. Ele não fornece, modifica ou cria serviços de VPN, apenas automatiza o processo de abrir e conectar uma VPN já existente e, após a conexão, iniciar o Discord. O projeto não possui finalidade ilegal e não incentiva qualquer uso indevido. O usuário é responsável pela utilização do software, pelas VPNs utilizadas e pelas atividades realizadas durante seu uso.
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
