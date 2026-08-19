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

## 🛡️ Sobre o OpenDis

O **OpenDis** é uma aplicação desenvolvida para simplificar e automatizar o processo de utilização de VPN através do **OpenVPN Community**, integrando gerenciamento de perfis `.ovpn`, credenciais, conexão, validação do túnel VPN e inicialização do Discord.

A proposta é transformar um processo que normalmente exige várias etapas manuais em um único fluxo controlado pela aplicação.

Em vez de:

```text
Abrir OpenVPN
      ↓
Escolher configuração
      ↓
Digitar usuário
      ↓
Digitar senha
      ↓
Conectar
      ↓
Esperar VPN
      ↓
Verificar IP
      ↓
Abrir Discord
      ↓
Usar
      ↓
Desconectar
```

o OpenDis centraliza tudo:

```text
                 ┌───────────────┐
                 │    OpenDis    │
                 └───────┬───────┘
                         │
                         ▼
              Detecta ambiente
                         │
                         ▼
              Seleciona perfil VPN
                         │
                         ▼
             Verifica credenciais
                         │
                         ▼
                 Prepara conexão
                         │
                         ▼
                  Inicia OpenVPN
                         │
                         ▼
               Aguarda túnel VPN
                         │
                         ▼
                Confirma IP público
                         │
                         ▼
                 Inicia Discord
                         │
                         ▼
                  Mantém conexão
                         │
                         ▼
                Encerra OpenVPN
                         │
                         ▼
                    CONCLUÍDO
```

---

# 🚀 Principais recursos

### VPN

* Detecção automática do OpenVPN Community.
* Localização do executável do OpenVPN.
* Gerenciamento de arquivos `.ovpn`.
* Seleção manual de perfil.
* Importação de novos perfis.
* VPN ALEATÓRIA.
* Validação do perfil antes da conexão.
* Execução do OpenVPN diretamente pelo sistema.
* Monitoramento do processo do OpenVPN.
* Detecção do estabelecimento do túnel.
* Verificação do IP público.
* Desconexão controlada.

### Credenciais

* Identificação automática de perfis que exigem autenticação.
* Tela de usuário e senha.
* Recuperação de credenciais previamente salvas.
* Preenchimento automático.
* Opção **Lembrar credenciais**.
* Credenciais associadas ao perfil utilizado.
* Possibilidade de alterar as credenciais quando necessário.

### VPN ALEATÓRIA

O OpenDis possui um modo especial para utilização de perfis VPNBook.

Nesse modo, a aplicação:

```text
OpenDis
   │
   ├── Acessa a fonte configurada
   │
   ├── Obtém as credenciais atuais
   │
   ├── Procura um perfil VPNBook já salvo
   │
   ├── Se necessário, baixa um novo perfil
   │
   ├── Valida o arquivo
   │
   ├── Salva localmente
   │
   └── Utiliza o perfil para conexão
```

Isso evita depender de um arquivo `.ovpn` fixo quando o serviço disponibiliza configurações atualizadas.

### Discord

* Detecção do Discord instalado.
* Inicialização automática após a VPN estar conectada.
* Aguarda o processo do Discord iniciar.
* Mantém o fluxo da aplicação durante a utilização.
* Finaliza o processo VPN quando a operação termina.

---

# 📋 Fluxo completo

O funcionamento do OpenDis segue uma sequência definida para reduzir erros e evitar que o Discord seja iniciado antes da VPN estar pronta.

## 1. Inicialização

Ao abrir o OpenDis, a aplicação inicia sua interface gráfica e começa a verificar o ambiente.

Primeiramente são verificadas as dependências necessárias.

```text
OpenDis iniciado
       │
       ├── Verificar OpenVPN
       │
       └── Verificar Discord
```

---

## 2. Detecção do OpenVPN Community

O OpenDis verifica se o **OpenVPN Community** está instalado e localiza o executável necessário para iniciar as conexões.

O OpenDis utiliza o mecanismo do OpenVPN para estabelecer o túnel VPN.

A aplicação não precisa depender da interface gráfica do OpenVPN para controlar a conexão.

O processo pode ser iniciado diretamente pelo sistema utilizando o executável encontrado.

---

## 3. Detecção do Discord

Depois da verificação do OpenVPN, o OpenDis procura a instalação do Discord.

O objetivo é garantir que o aplicativo que será iniciado posteriormente esteja disponível no computador.

Fluxo:

```text
OpenVPN encontrado
       ↓
Discord encontrado
       ↓
OpenDis pronto
```

Caso alguma dependência necessária não seja encontrada, a aplicação pode interromper o fluxo e informar o usuário.

---

# 📂 4. Gerenciamento dos perfis VPN

Os arquivos `.ovpn` utilizados pelo OpenDis ficam no diretório:

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

Ao acessar a seleção de VPN, o OpenDis lista os arquivos `.ovpn` disponíveis.

O usuário pode:

* Selecionar um perfil existente.
* Importar/adicionar um novo `.ovpn`.
* Utilizar a opção **VPN ALEATÓRIA**.

---

# 📥 5. Importação de um novo `.ovpn`

O usuário pode adicionar uma nova configuração OpenVPN sem precisar editar manualmente os arquivos internos da aplicação.

O processo é:

```text
Selecionar "Adicionar .ovpn"
             ↓
Selecionar arquivo
             ↓
Copiar para OpenDis/VPN
             ↓
Atualizar lista
             ↓
Novo perfil disponível
```

Depois disso, o novo perfil passa a aparecer na seleção de VPN.

---

# 🎲 6. VPN ALEATÓRIA

A opção **VPN ALEATÓRIA** automatiza o processo de obtenção de uma configuração VPNBook.

Quando selecionada, o OpenDis verifica primeiro se existe um perfil VPNBook previamente armazenado.

```text
VPN ALEATÓRIA
      │
      ▼
Existe perfil salvo?
   │          │
  SIM        NÃO
   │          │
   │          ▼
   │      Obter perfil
   │          │
   │          ▼
   │       Validar
   │          │
   │          ▼
   │        Salvar
   │          │
   └──────┬───┘
          ▼
     Usar perfil
```

As credenciais atuais disponibilizadas pelo serviço também são obtidas para que o perfil possa ser utilizado corretamente.

Isso permite que o OpenDis trabalhe com configurações atualizadas sem exigir que o usuário faça manualmente todo o processo de download e configuração.

---

# 🔎 7. Análise do arquivo `.ovpn`

Depois que um perfil é selecionado, o OpenDis analisa sua configuração.

Um dos pontos verificados é se o perfil exige autenticação.

A aplicação identifica a necessidade de credenciais antes de iniciar a conexão.

```text
Perfil selecionado
        ↓
Analisar .ovpn
        ↓
Precisa de credenciais?
      /       \
    NÃO       SIM
     │          │
     ▼          ▼
Preparação   Usuário/Senha
```

---

# 🔐 8. Credenciais

Quando o perfil exige autenticação, o OpenDis apresenta uma tela para:

```text
Usuário:
[________________________]

Senha:
[________________________]

☐ Lembrar credenciais
```

Se existirem credenciais previamente armazenadas para aquele perfil, elas podem ser carregadas automaticamente.

Isso evita que o usuário precise digitar as mesmas informações toda vez que abrir o programa.

---

# 💾 9. Lembrar credenciais

A opção:

```text
☑ Lembrar credenciais
```

permite armazenar as credenciais para utilização futura.

No próximo acesso ao mesmo perfil, o OpenDis procura as informações salvas e pode preencher os campos automaticamente.

O usuário continua podendo alterar as informações antes de iniciar a conexão.

---


Isso permite trocar o perfil `.ovpn` antes de iniciar o OpenVPN.

O objetivo é evitar que uma escolha errada obrigue o usuário a fechar e abrir novamente o programa.

---

# ⚙️ 11. Tela de preparação

Depois que o perfil e as credenciais estão definidos, o OpenDis apresenta a tela de preparação.

Essa etapa permite confirmar que tudo está pronto antes de iniciar o processo.

O fluxo fica:

```text
Perfil
  ↓
Credenciais
  ↓
Preparação
  ↓
INICIAR
```

O OpenVPN somente é executado quando o usuário confirma o início.

---

# 🔌 12. Inicialização do OpenVPN

Ao clicar em **INICIAR**, o OpenDis executa o OpenVPN utilizando o perfil selecionado.

Conceitualmente:

```text
OpenDis
   │
   ├── Executável OpenVPN
   │
   ├── Perfil .ovpn
   │
   └── Credenciais
          │
          ▼
      OpenVPN
          │
          ▼
      Servidor VPN
```

O OpenDis acompanha o processo enquanto a conexão está sendo estabelecida.

---

# 📡 13. Monitoramento da conexão

A aplicação monitora a saída do processo do OpenVPN para identificar quando a conexão realmente foi estabelecida.

O objetivo não é simplesmente verificar se o processo abriu.

O OpenDis precisa confirmar que o túnel VPN foi efetivamente inicializado.

A aplicação aguarda o sinal correspondente à conclusão da inicialização do túnel.

---

# 🌐 14. Verificação do IP público

Depois que o túnel é estabelecido, o OpenDis verifica o IP público atual.

Fluxo:

```text
OpenVPN conectado
       ↓
Consultar IP público
       ↓
IP obtido
       ↓
Confirmar conexão
```

Isso adiciona uma camada de validação ao processo.

Em vez de simplesmente assumir:

```text
OpenVPN abriu = VPN funcionando
```

o OpenDis procura confirmar:

```text
OpenVPN abriu
      +
Túnel estabelecido
      +
IP público confirmado
      =
VPN operacional
```

---

# 💬 15. Inicialização do Discord

Depois da confirmação da VPN, o OpenDis inicia o Discord.

```text
VPN confirmada
      ↓
IP confirmado
      ↓
Abrir Discord
      ↓
Aguardar inicialização
```

A aplicação aguarda o Discord iniciar antes de avançar.

Isso mantém a sequência organizada e evita que o Discord seja iniciado antes da etapa de VPN estar concluída.

---

# ⏳ 16. Manutenção da VPN

Enquanto o processo necessário estiver ativo, o OpenDis mantém o processo do OpenVPN funcionando.

A conexão VPN permanece ativa durante a etapa definida pelo fluxo da aplicação.

---

# 🔌 17. Encerramento do OpenVPN

Quando o processo termina, o OpenDis encerra a conexão VPN de forma controlada.

```text
Processo concluído
       ↓
Encerrar OpenVPN
       ↓
VPN desconectada
```

O objetivo é evitar deixar processos do OpenVPN rodando desnecessariamente em segundo plano.

---

# ✅ 18. Resultado final

Depois que todas as etapas são concluídas, o OpenDis apresenta o resultado final.

```text
╔══════════════════════════════╗
║                              ║
║         CONCLUÍDO            ║
║                              ║
║  Processo finalizado         ║
║  VPN encerrada               ║
║                              ║
╚══════════════════════════════╝
```

---

# 🧠 Arquitetura lógica

O funcionamento geral pode ser representado assim:

```text
                         OpenDis
                            │
                            ▼
                    Verificar ambiente
                     /              \
                    /                \
             OpenVPN OK?          Discord OK?
                  │                   │
                  └─────────┬─────────┘
                            ▼
                     Seleção de VPN
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
          Manual         Importar      Aleatória
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                     Analisar .ovpn
                            │
                    Credenciais?
                       /       \
                     NÃO       SIM
                      │          │
                      │      Carregar salvas
                      │          │
                      │      Usuário/Senha
                      │          │
                      └────┬─────┘
                           ▼
                       Preparação
                           │
                           ▼
                         INICIAR
                           │
                           ▼
                       OpenVPN
                           │
                           ▼
                    Túnel estabelecido
                           │
                           ▼
                      Verificar IP
                           │
                           ▼
                        Discord
                           │
                           ▼
                    Processo necessário
                           │
                           ▼
                    Encerrar OpenVPN
                           │
                           ▼
                       CONCLUÍDO
```

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

Dependendo da configuração utilizada, arquivos auxiliares de credenciais e configurações também podem ser criados pela aplicação.

---

# 💻 Requisitos

Para utilizar o OpenDis, o ambiente deve possuir:

* Windows
* Python 3.x, caso seja executado pelo código-fonte
* OpenVPN Community
* Discord
* Acesso à Internet

O OpenDis foi desenvolvido pensando em uma instalação Windows onde o OpenVPN Community esteja disponível para execução.

---

# 🐍 Executando pelo código-fonte

Clone o projeto:

```bash
git clone SEU_REPOSITORIO
```

Entre no diretório:

```bash
cd OpenDis
```

Instale as dependências Python necessárias:

```bash
pip install -r requirements.txt
```

Depois execute:

```bash
python opendis.py
```

> O nome do arquivo principal pode variar conforme a versão do projeto.

---

# 📦 Executável

O OpenDis também pode ser distribuído como executável utilizando ferramentas como **PyInstaller**.

Exemplo:

```bash
pyinstaller --onefile --windowed --icon=logo.ico opendis.py
```

O executável gerado poderá ser encontrado dentro de:

```text
dist/
```
O OpenDis irá Criar a pasta da VPN e LOGs no local que for executado.

Para funcionar bem, recomenda-se manter os arquivos e diretórios necessários para os perfis VPN junto do OpenDis.exe

---

# 🔧 Tecnologias

O projeto utiliza principalmente:

| Tecnologia        | Função                             |
| ----------------- | ---------------------------------- |
| Python            | Linguagem principal                |
| CustomTkinter     | Interface gráfica                  |
| OpenVPN Community | Motor VPN                          |
| `.ovpn`           | Configurações dos perfis VPN       |
| Discord           | Aplicação iniciada após a VPN      |
| HTTP/HTTPS        | Obtenção de informações e recursos |
| PyInstaller       | Geração do executável              |

---

# 🔐 Segurança

O OpenDis foi projetado para automatizar o gerenciamento de uma conexão VPN local.

Alguns pontos importantes:

* Nunca compartilhe arquivos de credenciais.
* Não compartilhe seu .ovpn ele contém seus dados.
* Não envie arquivos contendo credenciais para outras pessoas.
* Revise os perfis `.ovpn` antes de utilizá-los.
* Utilize apenas servidores VPN nos quais você confia.


---

# 🌐 VPNBook

O modo **VPN ALEATÓRIA** utiliza informações disponibilizadas pelo VPNBook para obter configurações e credenciais necessárias ao funcionamento do perfil.

Como essas informações podem ser alteradas pelo serviço, o OpenDis trata a obtenção das informações de maneira dinâmica em vez de depender exclusivamente de valores fixos.

O fluxo é:

```text
VPN ALEATÓRIA
      ↓
Obter informações atuais
      ↓
Procurar perfil local
      ↓
Perfil disponível?
   /          \
 SIM          NÃO
  │             │
  │          Download
  │             │
  │          Validação
  │             │
  └──────┬──────┘
         ↓
      OpenVPN
```

---

# 🛠️ Tratamento de erros

O OpenDis deve impedir que uma etapa inválida avance silenciosamente para a próxima.

Exemplos de situações que podem ser verificadas:

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

Quando uma etapa não pode ser concluída, o fluxo deve ser interrompido ou retornar para uma etapa anterior conforme o caso.

---

# 🔄 Fluxo resumido

Para quem quer entender o projeto rapidamente:

```text
1. Abrir OpenDis
2. Detectar OpenVPN
3. Detectar Discord
4. Abrir interface
5. Listar VPNs
6. Escolher perfil
7. Ou importar .ovpn
8. Ou utilizar VPN ALEATÓRIA
9. Analisar perfil
10. Verificar autenticação
11. Carregar credenciais salvas
12. Solicitar credenciais se necessário
13. Permitir lembrar credenciais
14. Permitir voltar
15. Preparar conexão
16. Clicar em INICIAR
17. Executar OpenVPN
18. Monitorar OpenVPN
19. Confirmar túnel
20. Confirmar IP público
21. Abrir Discord
22. Aguardar Discord
23. Manter VPN durante o processo
24. Encerrar OpenVPN
25. Mostrar resultado
26. Exibir CONCLUÍDO
```

---

# 🎯 Objetivo do projeto

O objetivo do OpenDis é transformar o gerenciamento de uma conexão OpenVPN em um processo simples, automatizado e centralizado.

A ideia é que o usuário não precise ficar alternando entre:

```text
Explorador de Arquivos
        ↓
OpenVPN
        ↓
Arquivo .ovpn
        ↓
Credenciais
        ↓
Terminal
        ↓
Verificação de IP
        ↓
Discord
```

O OpenDis reúne essas etapas em uma única interface.

```text
                    ┌───────────────────┐
                    │      OpenDis      │
                    ├───────────────────┤
                    │ VPN Management    │
                    │ Credentials       │
                    │ OpenVPN Control   │
                    │ IP Verification   │
                    │ Discord Launcher  │
                    └───────────────────┘
```

---

# 📌 Status

🚧 **Em desenvolvimento**

O projeto está sendo desenvolvido continuamente, com melhorias na interface, gerenciamento de VPNs, automação, tratamento de erros e experiência de utilização.

---

# ⚠️ Aviso

O OpenDis é uma ferramenta de automação para gerenciamento de conexões VPN e inicialização de aplicações.

O usuário é responsável por:

* Possuir autorização para utilizar os serviços VPN escolhidos.
* Respeitar os termos de uso dos serviços utilizados.
* Utilizar a ferramenta de acordo com as leis aplicáveis.
* Manter suas próprias credenciais protegidas.
* Verificar os arquivos `.ovpn` utilizados.

O projeto não garante anonimato absoluto, segurança absoluta ou proteção contra falhas de terceiros.

---

# 👨‍💻 Desenvolvimento

Projeto desenvolvido para centralizar e automatizar o fluxo:

```text
VPN
 +
OpenVPN
 +
Credenciais
 +
Verificação
 +
Discord
 =
OpenDis
```

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
