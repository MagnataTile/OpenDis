<p align="center">
  <img src="./logo.png" alt="OpenDis" width="850">
</p>

<h1 align="center">OpenDis</h1>

<p align="center">
  <strong>Discord App‑VPN & OpenVPN Automation</strong>
</p>

<p align="center">
  Abra o Discord pela VPN sem colocar o restante do computador na VPN.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-2.0.0-5865F2?style=for-the-badge">
  <img src="https://img.shields.io/badge/Windows-Supported-0078D6?style=for-the-badge&logo=windows&logoColor=white">
  <img src="https://img.shields.io/badge/Android-APK%20Legacy-3DDC84?style=for-the-badge&logo=android&logoColor=white">
  <img src="https://img.shields.io/badge/OpenVPN-Community-EA7E20?style=for-the-badge&logo=openvpn&logoColor=white">
  <img src="https://img.shields.io/badge/sing--box-App--VPN-111827?style=for-the-badge">
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Discord-Isolated-5865F2?style=for-the-badge&logo=discord&logoColor=white">
</p>

---

## 👉 [📥 Baixar a última versão](https://github.com/MagnataTile/OpenDis/releases)

# 🛡️ Sobre

**OpenDis** é uma aplicação criada para automatizar o uso do **OpenVPN Community** junto com o **Discord**.

A partir da versão **2.0.0 para Windows**, o objetivo deixou de ser apenas conectar uma VPN e abrir o Discord. O OpenDis agora cria uma camada **App‑VPN / split tunnel**, mantendo o túnel OpenVPN disponível exclusivamente para o tráfego do Discord enquanto o restante do computador continua utilizando a conexão normal de Internet.

Em resumo:

```text
Discord.exe
     │
     ▼
 OpenDisTun
     │
     ▼
  OpenVPN
     │
     ▼
Servidor VPN

Outros aplicativos
     │
     ▼
WAN normal
```

O OpenDis também gerencia perfis `.ovpn`, VPNBook, credenciais protegidas pelo Windows, validações de rede, atualização automática e limpeza controlada do ambiente ao encerrar.

---

# 🚀 OpenDis 2.0.0

## O que mudou

A versão **2.0.0** introduz a maior alteração de arquitetura do projeto até agora:

- **Split tunnel real no Windows.**
- **Somente o Discord é direcionado para a VPN.**
- O restante do computador continua usando a **WAN original**.
- Nova interface virtual **OpenDisTun**.
- Integração com **sing-box** para roteamento por processo.
- O OpenVPN deixa de assumir a rota padrão do computador.
- Perfis `.ovpn` manuais são sanitizados em runtime para impedir alterações globais de rota e DNS.
- Validação fail‑closed: se o OpenDis não conseguir confirmar que a WAN continua normal, a operação é cancelada.
- Bloqueio de IPv6 do Discord no fluxo atual para impedir bypass da VPN IPv4.
- Verificação de conexão TCP real do Discord antes de declarar a operação concluída.
- Seleção VPNBook com **ping ao vivo** e opção de usar o servidor com menor latência.
- Instalação automática do componente App‑VPN quando necessário.
- Atualizador automático do `OpenDis.exe` através das Releases do GitHub.
- Encerramento controlado do `OpenDisTun`, sing-box e OpenVPN.
- Verificação do retorno da conexão normal ao fechar.

---

# 🎯 Objetivo da v2

O OpenDis 2.0.0 foi projetado para alcançar este estado:

```text
┌──────────────────────────────┐
│            Windows           │
├──────────────────────────────┤
│ Discord.exe  ───────► VPN    │
│ Discord PTB  ───────► VPN    │
│ Discord Canary ─────► VPN    │
│                              │
│ Navegador ──────────► WAN    │
│ Jogos ──────────────► WAN    │
│ Steam ──────────────► WAN    │
│ Outros apps ────────► WAN    │
└──────────────────────────────┘
```

Isso significa que, diferentemente das versões anteriores, **não é necessário colocar todo o computador atrás da VPN para abrir e utilizar o Discord**.

---

# ⚠️ Importante antes de usar

## O Discord deve estar completamente fechado

O OpenDis precisa iniciar o Discord depois que o ambiente App‑VPN estiver preparado.

Antes de clicar em **INICIAR**:

1. Feche o Discord.
2. Verifique também a bandeja do sistema.
3. Certifique-se de que não exista nenhum `Discord.exe` em execução.

Se o Discord já estiver aberto, o OpenDis cancela a operação para evitar conexões antigas fora da VPN.

---

## 🔐 Permissão de Administrador

O OpenDis 2.0.0 precisa executar com privilégios administrativos no Windows porque cria e controla interfaces virtuais e rotas de rede.

Quando necessário, o aplicativo solicita elevação pelo UAC antes de criar a interface gráfica principal.

Se a elevação for recusada, o OpenDis não inicia o fluxo App‑VPN.

---

# 🧠 Como o split tunnel funciona

A arquitetura do OpenDis 2.0.0 utiliza duas camadas diferentes.

## 1. OpenVPN

O OpenVPN cria a interface VPN e mantém um caminho de saída para o servidor VPN.

Porém, o OpenDis impede que o perfil transforme essa interface na rota padrão do Windows.

## 2. OpenDis App‑VPN

O OpenDis utiliza o **sing-box** para criar a interface virtual:

```text
OpenDisTun
```

Essa interface recebe o tráfego e aplica regras por processo.

### Discord

```text
Discord.exe
DiscordPTB.exe
DiscordCanary.exe
        │
        ▼
   OpenDisTun
        │
        ▼
   bridge L3
        │
        ▼
Interface OpenVPN
```

### Outros processos

```text
Navegador / jogos / launchers / sistema
                  │
                  ▼
              OpenDisTun
                  │
                  ▼
             WAN original
```

O resultado esperado é:

```text
Discord → VPN
restante → Internet normal
```

---

# 🛡️ Proteções de rota

O OpenDis não confia apenas no fato de o OpenVPN ter conectado.

Antes e depois da criação do túnel, ele verifica a rota do computador e o IP público da WAN.

## Antes da VPN

O OpenDis registra:

- Interface WAN original.
- IPv4 local da WAN.
- Rotas default IPv4.
- Interfaces de rede já existentes.
- IP público original.

## Durante a VPN

O OpenDis bloqueia ou remove diretivas capazes de transformar a VPN em rota global, incluindo comportamentos relacionados a:

```text
redirect-gateway
redirect-private
route-nopull
route-noexec
dhcp-option
block-outside-dns
block-ipv6
route-ipv6
```

Em perfis manuais, o tratamento é ainda mais restritivo.

O perfil original **não é alterado**. O OpenDis cria uma cópia temporária de runtime e aplica as regras somente nessa cópia.

## Fail-safe de rota

Depois que o OpenVPN conecta, o OpenDis verifica se surgiram rotas que poderiam assumir o tráfego global do computador.

Rotas `def1` e rotas default VPN com prioridade indevida são removidas.

Uma rota VPN de métrica muito alta pode ser mantida exclusivamente para permitir o egress do bridge do App‑VPN sem superar a rota normal da WAN.

Se o IP público normal do computador mudar quando não deveria, o OpenDis tenta restaurar a WAN e, se não conseguir confirmar a restauração, **cancela a operação**.

---

# 🌐 Validação da WAN

O OpenDis verifica o IP público em vários pontos do fluxo.

```text
IP inicial da WAN
       │
       ▼
Criar OpenVPN
       │
       ▼
Confirmar que IP do PC continua igual
       │
       ▼
Criar OpenDisTun
       │
       ▼
Confirmar novamente a WAN
```

Se a rota normal não puder ser confirmada, o OpenDis não declara o isolamento como seguro.

---

# 🔒 Proteção contra bypass

No fluxo atual, o OpenVPN utilizado pelo OpenDis trabalha com saída IPv4.

Para evitar que o Discord utilize IPv6 diretamente pela WAN enquanto o IPv4 está na VPN, o App‑VPN bloqueia IPv6 para os processos do Discord.

O restante do computador continua utilizando a rede normalmente.

---

# 💬 Verificação do Discord

O OpenDis não considera o processo concluído apenas porque o Discord abriu.

O fluxo verifica:

1. O Discord foi iniciado pelo OpenDis.
2. Os PIDs do Discord foram detectados.
3. Os processos foram associados ao App‑VPN.
4. O engine continua ativo.
5. A interface OpenVPN continua ativa.
6. A interface WAN original continua ativa.
7. A configuração do roteamento do Discord continua válida.
8. O Discord conseguiu estabelecer pelo menos uma conexão TCP real.

Somente então o OpenDis apresenta:

```text
✅ CONCLUÍDO — Discord na VPN
```

---

# 📦 Componente App‑VPN / sing-box

O OpenDis utiliza **sing-box 1.14.0 ou superior** como engine de App‑VPN.

Se o componente ainda não existir, o OpenDis pode baixar uma cópia privada do binário oficial para o diretório da aplicação no perfil do usuário.

O OpenDis verifica:

- se o executável existe;
- se consegue ser executado;
- a versão instalada;
- suporte necessário ao stack gVisor.

O componente não precisa ser adicionado ao `PATH` e não é instalado como serviço global do Windows.

---

# 🎲 VPN ALEATÓRIA / VPNBook

O modo **VPN ALEATÓRIA VPNBook** continua disponível, mas foi ampliado.

O OpenDis agora pode testar os servidores configurados e exibir o ping atualizado na tela.

Fluxo:

```text
VPN ALEATÓRIA VPNBook
        │
        ▼
Testar servidores
        │
        ▼
Exibir ping ao vivo
        │
        ├──► Selecionar manualmente
        │
        └──► Usar menor ping agora
                │
                ▼
Obter credenciais VPNBook
                │
                ▼
Procurar perfil salvo
        ┌───────┴───────┐
        │               │
      existe          não existe
        │               │
        │               ▼
        │        baixar perfil
        │               │
        └───────┬───────┘
                ▼
          validar .ovpn
                │
                ▼
            OpenVPN
```

A opção **Guardar rede VPNBook** permite reaproveitar o perfil baixado em execuções futuras.

As credenciais do VPNBook são obtidas dinamicamente quando necessárias.

---

# 📥 Perfis `.ovpn` manuais

Você também pode usar seu próprio arquivo OpenVPN.

```text
Adicionar / selecionar .ovpn
          │
          ▼
Selecionar arquivo
          │
          ▼
OpenDis copia para VPN/
          │
          ▼
Analisar autenticação
          │
          ├──► sem credenciais
          │
          └──► solicitar usuário e senha
                      │
                      ▼
                  CONTINUAR
                      │
                      ▼
                    INICIAR
```

O OpenDis mantém o arquivo original intacto e gera um perfil temporário de runtime para aplicar as proteções de split tunnel.

Perfis próprios de provedores como Proton VPN também podem ser utilizados desde que sejam compatíveis com OpenVPN.

Documentação para obter configurações OpenVPN da Proton VPN:

https://protonvpn.com/support/vpn-config-download

---

# 🔐 Credenciais

Quando um perfil utiliza `auth-user-pass`, o OpenDis solicita:

```text
Usuário:
[________________________]

Senha:
[________________________]

☐ Lembrar credenciais
```

## 🔒 Como as credenciais são protegidas

Na versão atual, as credenciais persistentes são armazenadas em um arquivo protegido pelo **Windows DPAPI**.

```text
Usuário informa credenciais
          │
          ▼
        OpenDis
          │
          ▼
Windows DPAPI
          │
          ▼
%APPDATA%\OpenDis\credentials.dat
```

O conteúdo persistente não é salvo em texto puro.

A proteção DPAPI fica vinculada ao usuário atual do Windows.

A associação entre credencial e perfil é feita usando uma identificação derivada do conteúdo do `.ovpn`, permitindo que o OpenDis continue reconhecendo o mesmo perfil mesmo se o diretório da aplicação for movido.

## Credencial temporária do OpenVPN

Durante a conexão, quando necessário, o OpenDis cria um arquivo temporário contendo usuário e senha para entregar ao OpenVPN.

Esse arquivo é utilizado apenas durante a operação e é removido no bloco de limpeza ao final do fluxo.

---

# 🔄 Fluxo completo da versão 2.0.0

```text
┌──────────────────────────┐
│       Abrir OpenDis      │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Solicitar Administrador  │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Verificar atualização    │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Detectar OpenVPN/Discord │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Selecionar VPN           │
│ Manual / VPNBook         │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Preparar credenciais     │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Preparar sing-box        │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Capturar WAN original    │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Criar perfil runtime     │
│ seguro                   │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Iniciar OpenVPN          │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Confirmar túnel VPN      │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Confirmar WAN preservada │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Criar OpenDisTun         │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Discord → OpenVPN        │
│ Outros → WAN             │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Abrir Discord            │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Detectar PIDs            │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Verificar isolamento     │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Confirmar conexão TCP    │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ ✅ CONCLUÍDO             │
│ Discord permanece na VPN │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ FECHAR E ENCERRAR VPN    │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│ Remover OpenDisTun       │
│ Encerrar OpenVPN         │
│ Limpar DNS               │
│ Confirmar WAN            │
└──────────────────────────┘
```

---

# ⏳ Durante a utilização

Depois que a operação chega a 100%, o OpenDis **não encerra a VPN automaticamente**.

O estado final é ativo:

```text
Discord → VPN
restante → WAN normal
OpenVPN → ativo
OpenDisTun → ativo
OpenDis → minimizado
```

O OpenDis pode voltar para a frente após a inicialização do Discord e depois ser minimizado mantendo o ambiente de rede ativo.

Para desfazer a operação, restaure a janela do OpenDis e utilize:

```text
⛔ FECHAR E ENCERRAR VPN
```

---

# 🔌 Encerramento e restauração

Ao encerrar uma sessão ativa, o OpenDis executa a restauração na ordem correta:

```text
1. Encerrar sing-box
       ↓
2. Remover/desativar OpenDisTun
       ↓
3. Encerrar OpenVPN
       ↓
4. Limpar cache DNS
       ↓
5. Consultar IP público
       ↓
6. Confirmar retorno da WAN
       ↓
7. Fechar OpenDis
```

O botão **X** da janela também verifica se existe uma operação ativa e solicita confirmação antes de desmontar a VPN.

O OpenDis tenta encerrar os processos de forma graciosa e possui fallbacks de `terminate`/`kill` quando necessário.

---

# 🔄 Atualização automática

A versão Windows verifica a Release mais recente do GitHub ao iniciar.

Quando uma versão mais nova é encontrada, o usuário pode aceitar a atualização dentro do próprio aplicativo.

Fluxo:

```text
OpenDis inicia
     │
     ▼
GitHub Releases API
     │
     ▼
Comparar versões
     │
     ├──► já atualizado
     │
     └──► nova versão
              │
              ▼
        baixar OpenDis.exe
              │
              ▼
        validar SHA256
        se disponível
              │
              ▼
       updater temporário
              │
              ▼
         criar backup
              │
              ▼
     substituir executável
              │
              ▼
        reiniciar OpenDis
```

O atualizador utiliza um processo externo temporário para que o `OpenDis.exe` consiga ser substituído depois que a instância antiga for encerrada.

A variável `PYINSTALLER_RESET_ENVIRONMENT=1` é utilizada ao reiniciar a nova versão para que o bootloader do PyInstaller trate o processo como uma nova instância independente.

A atualização automática funciona na versão compilada `.exe`.

---

# 📁 Estrutura de arquivos

## Diretório do OpenDis

```text
OpenDis/
├── OpenDis.exe
├── logo.png
│
├── VPN/
│   ├── perfil1.ovpn
│   ├── perfil2.ovpn
│   └── VPNBook/
│       ├── vpnbook-...-tcp443.ovpn
│       └── ...
│
└── Logs/
    ├── sing-box.log
    ├── openvpn_....log
    └── ...
```

Os logs temporários podem ser removidos pelo próprio fluxo dependendo do resultado da operação.

## Diretório de dados do usuário

```text
%APPDATA%\OpenDis\
├── credentials.dat
│
└── sing-box\
    ├── sing-box.exe
    └── opendis-discord.json
```

O arquivo `credentials.dat` é protegido com Windows DPAPI.

O `sing-box.exe` é mantido como componente privado do OpenDis.

---

# 🚀 Principais recursos

## App‑VPN / Split tunnel

- Roteamento específico para Discord.
- Preservação da WAN original.
- Interface virtual `OpenDisTun`.
- Engine sing-box.
- Stack gVisor.
- Bridge para interface OpenVPN.
- Roteamento direto do restante do sistema pela WAN.
- Bloqueio de bypass IPv6 do Discord.
- Validação de adaptadores e configuração.
- Verificação fail‑closed.

## OpenVPN

- Detecção automática do OpenVPN Community.
- Instalação automática via `winget` quando disponível.
- Localização do executável sem depender exclusivamente do `PATH`.
- Importação de `.ovpn`.
- Perfis manuais.
- Perfis VPNBook.
- Perfil temporário de runtime.
- `route-nopull` e filtros de segurança.
- Monitoramento do processo.
- Detecção de `Initialization Sequence Completed`.
- Desconexão controlada.

## VPNBook

- Obtenção dinâmica de credenciais.
- Download de perfil via API.
- Reaproveitamento de perfis salvos.
- Medição de ping.
- Atualização de ping ao vivo.
- Seleção manual de servidor.
- Seleção automática do menor ping disponível.

## Credenciais

- Detecção de `auth-user-pass`.
- Tela dedicada de usuário e senha.
- Opção **Lembrar credenciais**.
- Proteção com Windows DPAPI.
- Associação por conteúdo do perfil `.ovpn`.
- Remoção individual de credenciais salvas.
- Arquivo temporário de autenticação removido após o uso.

## Discord

- Detecção do Discord estável.
- Suporte de identificação para Discord PTB e Canary.
- Bloqueio da operação se o Discord já estiver aberto.
- Inicialização automática depois da preparação do App‑VPN.
- Detecção de novos PIDs.
- Associação de novos processos ao engine.
- Verificação de conexão TCP real.

## Atualização

- Consulta automática ao GitHub Releases.
- Comparação de versões.
- Download do novo `OpenDis.exe`.
- Suporte à validação SHA256 quando o hash estiver disponível na Release.
- Backup temporário.
- Substituição automática.
- Reinicialização do OpenDis.

---

# 💻 Requisitos — Windows 2.0.0

Para a versão Windows:

- Windows 10/11.
- OpenVPN Community.
- Discord Desktop.
- Acesso à Internet.
- Privilégios administrativos.

O componente sing-box pode ser preparado automaticamente pelo OpenDis.

Para execução pelo código-fonte:

- Python 3.x.
- Dependências listadas em `requirements.txt`.

---

# 🐍 Executando pelo código-fonte

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

Execute:

```bash
python opendis.py
```

O Windows poderá solicitar elevação administrativa.

Antes de iniciar a operação, feche completamente o Discord.

---

# 📦 Versões compiladas

## 🪟 Windows

A versão principal atual do projeto é:

```text
OpenDis 2.0.0
```

Baixe através da página de Releases:

👉 [📥 Releases do OpenDis](https://github.com/MagnataTile/OpenDis/releases)

Na versão `.exe`, não é necessário instalar Python nem executar `pip install`.

O **OpenVPN Community** continua sendo necessário para o túnel OpenVPN.

---

# 🤖 Android / APK

> ⚠️ **Atenção:** o APK ainda não foi atualizado para a arquitetura 2.0.0 do Windows.

A versão Android disponível deve ser considerada uma implementação anterior/legacy até que o novo App‑VPN seja portado.

Portanto, as funcionalidades abaixo são atualmente específicas da versão Windows 2.0.0:

- `OpenDisTun`.
- sing-box App‑VPN.
- split tunnel por processo do Windows.
- preservação e validação da WAN usando as rotas do Windows.
- isolamento `Discord.exe → VPN`.

---

# 🛠️ Gerando seu próprio executável

Depois de instalar as dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
pyinstaller --clean --noconfirm OpenDis.spec
```

O executável normalmente será criado em:

```text
dist/
└── OpenDis.exe
```

Antes de compilar uma nova Release:

1. Atualize a versão no código.
2. Limpe as pastas `build/` e `dist/`.
3. Compile novamente.
4. Teste o executável gerado.
5. Publique `OpenDis.exe` na Release correta.
6. Opcionalmente publique também um arquivo `.sha256` ou `sha256.txt` para validação do atualizador.

---

# 🔧 Tecnologias

| Tecnologia | Função |
|---|---|
| Python | Aplicação Windows |
| CustomTkinter | Interface gráfica |
| OpenVPN Community | Túnel VPN |
| `.ovpn` | Perfis OpenVPN |
| sing-box | Engine App‑VPN / TUN |
| Wintun | Interface virtual utilizada pelo App‑VPN |
| gVisor | Stack do TUN no sing-box |
| PowerShell | Consulta de adaptadores, rotas e processos no Windows |
| Windows DPAPI | Proteção das credenciais persistentes |
| GitHub Releases API | Verificação de atualização |
| PyInstaller | Geração do `OpenDis.exe` |
| Kotlin / Android | Base da versão APK, ainda não portada para a arquitetura 2.0.0 |

---

# 🔐 Segurança

O OpenDis aplica uma política fail‑closed em vários pontos do fluxo.

Se não for possível confirmar que o estado de rede é seguro, o aplicativo deve interromper a operação em vez de declarar sucesso silenciosamente.

Entre as validações existentes estão:

- Discord deve estar fechado antes da operação.
- WAN original precisa ser identificada.
- IP público inicial precisa ser obtido.
- OpenVPN precisa concluir a inicialização.
- Rota principal do computador precisa permanecer na WAN.
- OpenDisTun precisa ser criado corretamente.
- sing-box precisa continuar em execução.
- Interface OpenVPN precisa continuar ativa.
- Interface WAN precisa continuar ativa.
- Discord precisa estar associado ao App‑VPN.
- Discord precisa conseguir estabelecer conexão TCP.
- Ao encerrar, a interface App‑VPN e o OpenVPN precisam ser desmontados.
- O OpenDis tenta confirmar o retorno do IP público original.

---

# ⚠️ Solução de problemas

## Discord já está aberto

Feche completamente o Discord antes de clicar em **INICIAR**.

```text
Discord aberto
     ↓
Fechar Discord
     ↓
Verificar bandeja/processos
     ↓
Iniciar OpenDis novamente
```

---

## OpenVPN não encontrado

O OpenDis tenta detectar o OpenVPN em vários caminhos do Windows.

Se não for encontrado, utilize a instalação automática quando disponível ou instale manualmente o **OpenVPN Community**.

---

## App‑VPN não inicia

Verifique:

- se o OpenDis foi executado como Administrador;
- se existe conexão com a Internet;
- se o `sing-box.exe` conseguiu ser preparado;
- se a versão do sing-box é compatível;
- se o binário possui suporte gVisor;
- se a interface OpenVPN foi criada corretamente.

Consulte também:

```text
Logs/sing-box.log
```

---

## O IP do computador mudou para o IP da VPN

Isso não é o comportamento esperado da versão 2.0.0.

O OpenDis deve detectar essa alteração e cancelar/restaurar a operação.

Se isso ocorrer:

1. Encerre o OpenDis pelo botão **FECHAR E ENCERRAR VPN**.
2. Confirme que a rede normal voltou.
3. Tente outro perfil `.ovpn`.
4. Verifique o log da execução.

---

## Discord abre, mas não conecta

Tente outro servidor VPN ou outro perfil `.ovpn`.

No VPNBook, utilize a opção de menor ping ou escolha outro servidor manualmente.

Perfis e servidores VPN podem estar ativos, mas ainda assim apresentar bloqueios ou instabilidade para determinados serviços.

---

## Compartilhamento continua bloqueado

Troque o servidor/perfil VPN utilizado e execute novamente o fluxo.

O OpenDis controla o caminho de rede, mas a disponibilidade final do serviço também depende do servidor VPN e da conectividade até os serviços do Discord.

---

## OpenDisTun permanece visível depois de fechar

O Windows pode manter um adaptador virtual listado como `Down` por alguns segundos mesmo depois de o túnel ter sido desmontado.

O OpenDis diferencia um adaptador residual/inativo de um túnel ainda ativo e possui um fallback de remoção para a interface `OpenDisTun` quando necessário.

---

## Atualização automática não funciona

Verifique se a Release contém um asset chamado:

```text
OpenDis.exe
```

O atualizador procura especificamente esse executável.

Se existir um arquivo de hash, ele pode utilizar:

```text
*.sha256
```

ou:

```text
sha256.txt
```

---

# 📌 Principais erros tratados

| Situação | Comportamento esperado |
|---|---|
| OpenVPN não encontrado | Interrompe e oferece instalação quando possível |
| Discord não encontrado | Interrompe e oferece instalação quando possível |
| Discord já aberto | Interrompe para evitar bypass |
| Nenhum `.ovpn` selecionado | Interrompe |
| Perfil inválido | Interrompe |
| Credenciais ausentes | Solicita usuário e senha |
| `AUTH_FAILED` | Conexão não conclui; trocar/corrigir credenciais |
| OpenVPN encerra antes de conectar | Interrompe e limpa o ambiente |
| Timeout da VPN | Interrompe e limpa o ambiente |
| WAN original não identificada | Interrompe |
| IP público inicial não confirmado | Interrompe |
| IP global muda para a VPN | Tenta restaurar e cancela se necessário |
| Interface OpenVPN não identificada | Interrompe |
| sing-box inválido/incompatível | Interrompe |
| OpenDisTun não criado | Interrompe |
| Isolamento do Discord não confirmado | Interrompe |
| Discord sem conexão TCP | Interrompe e registra diagnóstico |
| VPN cai durante estabilização | Interrompe |
| Discord fecha durante estabilização | Interrompe |
| Falha ao desmontar rede | Exibe aviso e permite nova tentativa |
| Atualização sem `OpenDis.exe` | Informa que o executável não está disponível |
| SHA256 divergente | Rejeita o arquivo baixado |

---


# 📜 Changelog resumido

## v2.0.0 — Windows

**Nova arquitetura App‑VPN / split tunnel.**

Principais mudanças:

- Discord passa pela VPN.
- Restante do computador permanece na WAN.
- Novo `DiscordVPNEngine`.
- Novo `OpenDisTun`.
- sing-box 1.14.0+.
- stack gVisor.
- proteção contra alteração de rota global.
- sanitização de perfis `.ovpn` em runtime.
- bloqueio IPv6 do Discord para evitar bypass.
- verificação fail‑closed de IP/WAN.
- seleção VPNBook com ping ao vivo.
- verificação TCP do Discord.
- atualização automática do executável.
- encerramento e restauração controlados.

## Android

O APK ainda não recebeu as alterações da versão 2.0.0 e permanece como versão legacy até a implementação do novo `VpnService` por aplicativo.

---

# ⚠️ Aviso

O OpenDis é uma ferramenta de automação de rede.

O usuário é responsável por:

- possuir autorização para utilizar os serviços VPN escolhidos;
- respeitar os termos de uso dos provedores e serviços utilizados;
- utilizar a ferramenta de acordo com as leis aplicáveis;
- manter suas credenciais protegidas;
- verificar os arquivos `.ovpn` utilizados;
- utilizar apenas servidores VPN nos quais confia.

O OpenDis não fornece nem opera servidores VPN próprios. Ele automatiza a utilização de conexões VPN configuradas pelo usuário ou obtidas através dos fluxos suportados pela aplicação.

---

<p align="center">
  <img src="./logo.png" alt="OpenDis Logo" width="180">
</p>

<p align="center">
  <strong>OpenDis 2.0.0</strong>
  <br>
  Discord App‑VPN & OpenVPN Automation
  <br><br>
  Powered by MagnataTile
</p>

<p align="center">
  <sub>© 2026 OpenDis — All rights reserved.</sub>
</p>
