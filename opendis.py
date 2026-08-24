#!/usr/bin/env python3
"""
OpenDis - MagnataTile
OpenVPN Community + Discord

Fluxo completo:
1. Detecta o OpenVPN Community instalado
2. Detecta o Discord instalado
3. Inicializa a interface do OpenDis
4. Lista os arquivos .ovpn disponíveis em OpenDis/VPN
5. Permite:
   - Selecionar manualmente um arquivo .ovpn
   - Importar/adicionar um novo .ovpn
   - Usar VPN ALEATÓRIA
6. Analisa o perfil .ovpn selecionado
7. Verifica se o perfil exige credenciais
8. Se não exigir credenciais:
   - Avança diretamente para a tela de conexão
9. Se exigir credenciais:
   - Mostra tela de usuário e senha
   - Procura credenciais salvas para aquele perfil
   - Preenche automaticamente se existirem
   - Permite marcar "Lembrar credenciais"
   - Permite voltar e escolher outro .ovpn
10. Na VPN ALEATÓRIA:
    - Obtém as credenciais atuais do VPNBook
    - Procura um perfil VPNBook já salvo
    - Se não existir, baixa o perfil
    - Valida o arquivo .ovpn
    - Salva o perfil localmente
    - Utiliza as credenciais necessárias
11. Mostra a tela de preparação/conexão
12. Permite voltar para a seleção do perfil antes de iniciar
13. Ao clicar em INICIAR:
    - Executa o OpenVPN
    - Utiliza o perfil .ovpn selecionado
    - Utiliza as credenciais quando necessárias
14. Monitora o processo do OpenVPN
15. Confirma o estabelecimento do túnel VPN
16. Confirma o IP público
17. Abre o Discord
18. Aguarda o Discord iniciar
19. Mantém a VPN durante o processo necessário
20. Desconecta/encerra o OpenVPN
21. Mostra o resultado final
22. Exibe CONCLUÍDO quando todo o processo termina
"""

import os
import sys
import re
import time
import json
import signal
import socket
import threading
import subprocess
import webbrowser
import random
import ctypes
from pathlib import Path
from urllib.request import (
    urlopen,
)
import hashlib
import tempfile
from html import unescape
from urllib.request import Request
from urllib.error import HTTPError, URLError
import customtkinter as ctk
import tkinter.messagebox as mb
from tkinter import filedialog


# ============================================================
# CONFIGURAÇÃO
# ============================================================

APP_NAME = "OpenDis"
APP_VERSION = "1.1.0"
WAIT_VPN_TIMEOUT = 60
WAIT_DISCORD = 40
DISCORD_STABILIZE_DELAY = 20
IP_CHECK_TIMEOUT = 30


OPENVPN_WINGET_ID = "OpenVPNTechnologies.OpenVPN"

DISCORD_WINGET_ID = "Discord.Discord"


GITHUB_OWNER = "MagnataTile"
GITHUB_REPO = "OpenDis"

GITHUB_RELEASE_API = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
# ============================================================
# DIRETÓRIOS DO OPENDIS
# ============================================================

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

VPN_DIR = BASE_DIR / "VPN"
LOG_DIR = BASE_DIR / "Logs"

VPN_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)



# ============================================================
# ESTADO GLOBAL
# ============================================================

OPENVPN_EXECUTABLE = None
DISCORD_EXECUTABLE = None


# ============================================================
# APARÊNCIA
# ============================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ============================================================
# VPNBOOK
# ============================================================

VPNBOOK_URL = (
    "https://www.vpnbook.com/pt/freevpn/openvpn"
)

VPNBOOK_API_URL = (
    "https://www.vpnbook.com/api/openvpn"
)

# ------------------------------------------------------------
# PADRÃO DO BOTÃO "VPN ALEATÓRIA"
# ------------------------------------------------------------

VPNBOOK_SERVERS = [
    {
        "server": "us16.vpnbook.com",
        "name": "US Server 1",
        "protocol": "tcp443",
    },
    {
        "server": "us178.vpnbook.com",
        "name": "US Server 2",
        "protocol": "tcp443",
    },
    {
        "server": "ca149.vpnbook.com",
        "name": "Canada Server",
        "protocol": "tcp443",
    },
]

VPNBOOK_SELECTED = random.choice(VPNBOOK_SERVERS)

VPNBOOK_DEFAULT_SERVER = VPNBOOK_SELECTED["server"]
VPNBOOK_DEFAULT_SERVER_NAME = VPNBOOK_SELECTED["name"]
VPNBOOK_DEFAULT_PROTOCOL = VPNBOOK_SELECTED["protocol"]

VPNBOOK_DIR = VPN_DIR / "VPNBook"

VPNBOOK_DIR.mkdir(
    parents=True,
    exist_ok=True
)



# ============================================================
# UTILITÁRIOS
# ============================================================

def run_command(
    command,
    timeout=30,
    capture=True,
    cwd=None
):
    """
    Executa comando do Windows com segurança.
    """

    try:
        return subprocess.run(
            command,
            capture_output=capture,
            text=True,
            timeout=timeout,
            cwd=cwd,
            creationflags=subprocess.CREATE_NO_WINDOW
            if os.name == "nt"
            else 0
        )

    except Exception as e:

        class Result:
            returncode = -1
            stdout = ""
            stderr = str(e)

        return Result()


# ============================================================
# DETECTAR OPENVPN
# ============================================================

def find_openvpn_executable():
    """
    Procura o OpenVPN Community.

    Não depende do PATH.

    Ordem:
        1. PATH
        2. Program Files
        3. Program Files x86
        4. LocalAppData
        5. Busca controlada
    """

    global OPENVPN_EXECUTABLE

    # --------------------------------------------------------
    # 1. PATH
    # --------------------------------------------------------

    try:

        result = subprocess.run(
            ["where", "openvpn.exe"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:

            for line in result.stdout.splitlines():

                path = line.strip()

                if path and os.path.isfile(path):

                    OPENVPN_EXECUTABLE = os.path.abspath(path)

                    return OPENVPN_EXECUTABLE

    except Exception:
        pass


    # --------------------------------------------------------
    # 2. CAMINHOS CONHECIDOS
    # --------------------------------------------------------

    possible_paths = [

        os.path.join(
            os.environ.get(
                "ProgramFiles",
                r"C:\Program Files"
            ),
            "OpenVPN",
            "bin",
            "openvpn.exe"
        ),

        os.path.join(
            os.environ.get(
                "ProgramFiles(x86)",
                r"C:\Program Files (x86)"
            ),
            "OpenVPN",
            "bin",
            "openvpn.exe"
        ),

        os.path.join(
            os.environ.get(
                "LOCALAPPDATA",
                ""
            ),
            "OpenVPN",
            "bin",
            "openvpn.exe"
        ),

        os.path.join(
            os.environ.get(
                "LOCALAPPDATA",
                ""
            ),
            "Programs",
            "OpenVPN",
            "bin",
            "openvpn.exe"
        ),
    ]


    for path in possible_paths:

        if path and os.path.isfile(path):

            OPENVPN_EXECUTABLE = os.path.abspath(path)

            return OPENVPN_EXECUTABLE


    # --------------------------------------------------------
    # 3. BUSCA CONTROLADA
    # --------------------------------------------------------

    roots = [

        os.environ.get(
            "ProgramFiles",
            r"C:\Program Files"
        ),

        os.environ.get(
            "ProgramFiles(x86)",
            r"C:\Program Files (x86)"
        ),

        os.environ.get(
            "LOCALAPPDATA",
            ""
        ),
    ]


    for root in roots:

        if not root or not os.path.isdir(root):
            continue

        try:

            for current_root, dirs, files in os.walk(root):

                dirs[:] = [
                    d for d in dirs
                    if d.lower() not in {
                        "windowsapps",
                        "microsoft",
                        "node_modules",
                        "packages",
                        "cache",
                        "temp",
                        "__pycache__",
                    }
                ]

                for filename in files:

                    if filename.lower() == "openvpn.exe":

                        path = os.path.join(
                            current_root,
                            filename
                        )

                        if os.path.isfile(path):

                            OPENVPN_EXECUTABLE = os.path.abspath(path)

                            return OPENVPN_EXECUTABLE

        except (
            PermissionError,
            OSError
        ):
            continue


    return None


# ============================================================
# DETECTAR DISCORD
# ============================================================

def find_discord_executable():
    """
    Localiza Discord instalado.

    Não depende de caminho fixo do usuário.
    """

    global DISCORD_EXECUTABLE


    # --------------------------------------------------------
    # Caminhos padrão
    # --------------------------------------------------------

    local_appdata = os.environ.get(
        "LOCALAPPDATA",
        ""
    )

    paths = [

        os.path.join(
            local_appdata,
            "Discord",
            "Discord.exe"
        ),

        os.path.join(
            local_appdata,
            "DiscordPTB",
            "DiscordPTB.exe"
        ),

        os.path.join(
            local_appdata,
            "DiscordCanary",
            "DiscordCanary.exe"
        ),
    ]


    for path in paths:

        if os.path.isfile(path):

            DISCORD_EXECUTABLE = os.path.abspath(path)

            return DISCORD_EXECUTABLE


    # --------------------------------------------------------
    # Busca controlada em LocalAppData
    # --------------------------------------------------------

    if os.path.isdir(local_appdata):

        try:

            for current_root, dirs, files in os.walk(
                local_appdata
            ):

                dirs[:] = [
                    d for d in dirs
                    if d.lower() not in {
                        "packages",
                        "temp",
                        "cache",
                        "npm-cache",
                        "__pycache__",
                    }
                ]

                for filename in files:

                    low = filename.lower()

                    if low in {
                        "discord.exe",
                        "discordptb.exe",
                        "discordcanary.exe",
                    }:

                        path = os.path.join(
                            current_root,
                            filename
                        )

                        if os.path.isfile(path):

                            DISCORD_EXECUTABLE = os.path.abspath(path)

                            return DISCORD_EXECUTABLE

        except (
            PermissionError,
            OSError
        ):
            pass


    return None


# ============================================================
# VERIFICAÇÕES
# ============================================================

def is_openvpn_installed():

    return find_openvpn_executable() is not None


def is_discord_installed():

    return find_discord_executable() is not None


# ============================================================
# INSTALAÇÃO AUTOMÁTICA
# ============================================================

def winget_available():

    try:

        result = run_command(
            ["winget", "--version"],
            timeout=10
        )

        return result.returncode == 0

    except Exception:

        return False


def install_openvpn():

    if not winget_available():
        return False, "winget não está disponível."

    result = run_command(
        [
            "winget",
            "install",
            "--id",
            OPENVPN_WINGET_ID,
            "-e",
            "--accept-source-agreements",
            "--accept-package-agreements",
        ],
        timeout=600
    )

    if result.returncode == 0:

        path = find_openvpn_executable()

        if path:
            return True, path

    error = (
        result.stderr.strip()
        or result.stdout.strip()
        or "Instalação não concluída."
    )

    return False, error


def install_discord():

    if not winget_available():
        return False, "winget não está disponível."

    result = run_command(
        [
            "winget",
            "install",
            "--id",
            DISCORD_WINGET_ID,
            "-e",
            "--accept-source-agreements",
            "--accept-package-agreements",
        ],
        timeout=600
    )

    if result.returncode == 0:

        path = find_discord_executable()

        if path:
            return True, path

    error = (
        result.stderr.strip()
        or result.stdout.strip()
        or "Instalação não concluída."
    )

    return False, error


# ============================================================
# ARQUIVOS OVPN
# ============================================================

def get_ovpn_files():

    VPN_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    return sorted(
        VPN_DIR.glob("*.ovpn"),
        key=lambda p: p.name.lower()
    )


def import_ovpn_file():

    path = filedialog.askopenfilename(
        title="Selecionar configuração OpenVPN",
        initialdir=str(VPN_DIR),
        filetypes=[
            (
                "OpenVPN",
                "*.ovpn"
            ),
            (
                "Todos os arquivos",
                "*.*"
            )
        ]
    )

    if not path:
        return None

    source = Path(path)

    destination = VPN_DIR / source.name

    if source.resolve() != destination.resolve():

        try:

            destination.write_bytes(
                source.read_bytes()
            )

        except Exception as e:

            mb.showerror(
                "Erro",
                f"Não foi possível copiar o perfil:\n{e}"
            )

            return None

    return destination


# ============================================================
# ANALISAR PERFIL
# ============================================================

def profile_requires_credentials(profile_path):
    """
    Detecta se o perfil utiliza auth-user-pass.

    Exemplos:

        auth-user-pass

        auth-user-pass arquivo.txt

    """

    try:

        text = profile_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if line.lower().startswith(
                "auth-user-pass"
            ):

                parts = line.split()

                if len(parts) == 1:

                    return True

                # Já existe arquivo de credenciais
                credentials_file = parts[1]

                credentials_path = (
                    profile_path.parent /
                    credentials_file
                )

                if credentials_path.exists():

                    return False

                return True

        return False

    except Exception:

        return False


def get_credentials_file(profile_path):

    """
    Retorna caminho de arquivo de credenciais
    caso o .ovpn especifique um.
    """

    try:

        text = profile_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        for line in text.splitlines():

            line = line.strip()

            if line.lower().startswith(
                "auth-user-pass"
            ):

                parts = line.split()

                if len(parts) >= 2:

                    return (
                        profile_path.parent /
                        parts[1]
                    )

    except Exception:
        pass

    return None

# ============================================================
# CREDENCIAIS SALVAS
# ============================================================

import base64
import hashlib
import ctypes
from ctypes import wintypes


CREDENTIALS_DIR = (
    Path(os.environ.get("APPDATA", str(BASE_DIR)))
    / APP_NAME
)

CREDENTIALS_FILE = (
    CREDENTIALS_DIR
    / "credentials.dat"
)


def _dpapi_protect(data):
    """
    Criptografa dados usando Windows DPAPI.

    A informação fica vinculada ao usuário atual
    do Windows.
    """

    if os.name != "nt":
        raise RuntimeError(
            "Windows DPAPI está disponível somente no Windows."
        )

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    raw = bytes(data)

    buffer = ctypes.create_string_buffer(raw)

    blob_in = DATA_BLOB(
        len(raw),
        ctypes.cast(
            buffer,
            ctypes.POINTER(ctypes.c_byte)
        )
    )

    blob_out = DATA_BLOB()

    crypt32 = ctypes.windll.crypt32

    result = crypt32.CryptProtectData(
        ctypes.byref(blob_in),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out)
    )

    if not result:
        raise ctypes.WinError()

    try:

        encrypted = ctypes.string_at(
            blob_out.pbData,
            blob_out.cbData
        )

    finally:

        ctypes.windll.kernel32.LocalFree(
            blob_out.pbData
        )

    return encrypted


def _dpapi_unprotect(data):
    """
    Descriptografa dados protegidos pelo Windows DPAPI.
    """

    if os.name != "nt":
        raise RuntimeError(
            "Windows DPAPI está disponível somente no Windows."
        )

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_byte)),
        ]

    raw = bytes(data)

    buffer = ctypes.create_string_buffer(raw)

    blob_in = DATA_BLOB(
        len(raw),
        ctypes.cast(
            buffer,
            ctypes.POINTER(ctypes.c_byte)
        )
    )

    blob_out = DATA_BLOB()

    crypt32 = ctypes.windll.crypt32

    result = crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out)
    )

    if not result:
        raise ctypes.WinError()

    try:

        decrypted = ctypes.string_at(
            blob_out.pbData,
            blob_out.cbData
        )

    finally:

        ctypes.windll.kernel32.LocalFree(
            blob_out.pbData
        )

    return decrypted


def _credential_profile_key(profile_path):
    """
    Cria uma identificação estável para o perfil .ovpn.

    Usa o conteúdo do arquivo em vez do caminho físico.
    Assim, se o OpenDis for movido de pasta, a credencial
    continua associada ao mesmo perfil.
    """

    try:

        profile_path = Path(profile_path)

        content = profile_path.read_bytes()

        return hashlib.sha256(
            content
        ).hexdigest()

    except Exception:

        return hashlib.sha256(
            str(profile_path).encode(
                "utf-8",
                errors="ignore"
            )
        ).hexdigest()


def load_saved_credentials(profile_path):
    """
    Retorna:

        {
            "username": "...",
            "password": "..."
        }

    ou None caso não exista.
    """

    try:

        if not CREDENTIALS_FILE.exists():
            return None

        encrypted = CREDENTIALS_FILE.read_bytes()

        if not encrypted:
            return None

        decrypted = _dpapi_unprotect(
            encrypted
        )

        database = json.loads(
            decrypted.decode("utf-8")
        )

        key = _credential_profile_key(
            profile_path
        )

        credentials = database.get(key)

        if not isinstance(
            credentials,
            dict
        ):
            return None

        username = credentials.get(
            "username",
            ""
        )

        password = credentials.get(
            "password",
            ""
        )

        if not username or not password:
            return None

        return {
            "username": username,
            "password": password
        }

    except Exception:

        return None


def save_credentials(
    profile_path,
    username,
    password
):
    """
    Salva as credenciais do perfil usando DPAPI.
    """

    try:

        CREDENTIALS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        database = {}

        # --------------------------------------------------------
        # Recuperar banco existente
        # --------------------------------------------------------

        if CREDENTIALS_FILE.exists():

            try:

                encrypted = (
                    CREDENTIALS_FILE.read_bytes()
                )

                if encrypted:

                    decrypted = _dpapi_unprotect(
                        encrypted
                    )

                    database = json.loads(
                        decrypted.decode("utf-8")
                    )

                    if not isinstance(
                        database,
                        dict
                    ):
                        database = {}

            except Exception:

                database = {}

        # --------------------------------------------------------
        # Salvar credencial
        # --------------------------------------------------------

        key = _credential_profile_key(
            profile_path
        )

        database[key] = {
            "username": str(username),
            "password": str(password)
        }

        raw = json.dumps(
            database,
            ensure_ascii=False
        ).encode("utf-8")

        encrypted = _dpapi_protect(
            raw
        )

        # --------------------------------------------------------
        # Escrita atômica
        # --------------------------------------------------------

        temporary_file = (
            CREDENTIALS_FILE.with_suffix(
                ".tmp"
            )
        )

        temporary_file.write_bytes(
            encrypted
        )

        temporary_file.replace(
            CREDENTIALS_FILE
        )

        return True

    except Exception:

        return False


def delete_saved_credentials(profile_path):
    """
    Remove as credenciais salvas somente do perfil informado.
    """

    try:

        if not CREDENTIALS_FILE.exists():
            return True

        encrypted = CREDENTIALS_FILE.read_bytes()

        if not encrypted:
            return True

        decrypted = _dpapi_unprotect(
            encrypted
        )

        database = json.loads(
            decrypted.decode("utf-8")
        )

        if not isinstance(
            database,
            dict
        ):
            return True

        key = _credential_profile_key(
            profile_path
        )

        if key in database:

            del database[key]

            if database:

                raw = json.dumps(
                    database,
                    ensure_ascii=False
                ).encode("utf-8")

                encrypted = _dpapi_protect(
                    raw
                )

                temporary_file = (
                    CREDENTIALS_FILE.with_suffix(
                        ".tmp"
                    )
                )

                temporary_file.write_bytes(
                    encrypted
                )

                temporary_file.replace(
                    CREDENTIALS_FILE
                )

            else:

                CREDENTIALS_FILE.unlink(
                    missing_ok=True
                )

        return True

    except Exception:

        return False
# ============================================================
# IP PÚBLICO
# ============================================================

def get_public_ip(timeout=10):

    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
    ]

    for url in services:

        try:

            with urlopen(
                url,
                timeout=timeout
            ) as response:

                ip = response.read().decode().strip()

                if re.match(
                    r"^[0-9a-fA-F:.]+$",
                    ip
                ):

                    return ip

        except Exception:
            continue

    return None


# ============================================================
# VERIFICAR DISCORD
# ============================================================

def discord_process_running():

    result = run_command(
        [
            "tasklist",
            "/FI",
            "IMAGENAME eq Discord.exe"
        ],
        timeout=10
    )

    output = (
        result.stdout or ""
    ).lower()

    return (
        "discord.exe" in output
    )


# ============================================================
# LOG
# ============================================================

def create_log_file():

    timestamp = time.strftime(
        "%Y%m%d_%H%M%S"
    )

    return LOG_DIR / (
        f"opendis_{timestamp}.log"
    )

def parse_version(version):
    """
    Converte uma versão como:

        v1.2.3
        1.2.3
        V1.2.3

    para uma tupla comparável.
    """

    try:

        version = str(version).strip().lower()

        if version.startswith("v"):
            version = version[1:]

        parts = version.split(".")

        numbers = []

        for part in parts[:3]:

            match = re.match(
                r"\d+",
                part
            )

            if match:
                numbers.append(
                    int(match.group())
                )
            else:
                numbers.append(0)

        while len(numbers) < 3:
            numbers.append(0)

        return tuple(numbers)

    except Exception:

        return (0, 0, 0)

def is_running_as_admin():
    """
    Verifica se o OpenDis está executando com privilégios
    administrativos no Windows.
    """

    if os.name != "nt":
        return True

    try:
        import ctypes

        return bool(
            ctypes.windll.shell32.IsUserAnAdmin()
        )

    except Exception:
        return False

def check_for_update():
    """
    Consulta a última Release do GitHub.

    Retorna:

        {
            "available": True/False,
            "version": "...",
            "download_url": "...",
            "sha256": "..."
        }

    ou None em caso de erro.
    """

    try:

        request = Request(
            GITHUB_RELEASE_API,
            headers={
                "User-Agent": (
                    f"{APP_NAME}/{APP_VERSION}"
                ),
                "Accept": (
                    "application/vnd.github+json"
                )
            }
        )

        with urlopen(
            request,
            timeout=8
        ) as response:

            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        latest_version = (
            data.get("tag_name")
            or data.get("name")
            or ""
        )

        latest_version = (
            latest_version
            .strip()
            .lstrip("vV")
        )

        if not latest_version:

            return None

        current = parse_version(
            APP_VERSION
        )

        latest = parse_version(
            latest_version
        )

        if latest <= current:

            return {
                "available": False,
                "version": latest_version
            }

        download_url = None
        sha256 = None

        assets = data.get(
            "assets",
            []
        )

        for asset in assets:

            name = (
                asset.get("name")
                or ""
            )

            if name.lower() == "opendis.exe":

                download_url = (
                    asset.get(
                        "browser_download_url"
                    )
                )

                break

        # ----------------------------------------------------
        # Procurar SHA256
        # ----------------------------------------------------

        for asset in assets:

            name = (
                asset.get("name")
                or ""
            ).lower()

            if (
                name.endswith(".sha256")
                or
                name == "sha256.txt"
            ):

                sha256_url = asset.get(
                    "browser_download_url"
                )

                if sha256_url:

                    try:

                        sha_request = Request(
                            sha256_url,
                            headers={
                                "User-Agent":
                                    f"{APP_NAME}/{APP_VERSION}"
                            }
                        )

                        with urlopen(
                            sha_request,
                            timeout=8
                        ) as sha_response:

                            sha_text = (
                                sha_response
                                .read()
                                .decode(
                                    "utf-8",
                                    errors="ignore"
                                )
                                .strip()
                            )

                            match = re.search(
                                r"\b[a-fA-F0-9]{64}\b",
                                sha_text
                            )

                            if match:

                                sha256 = (
                                    match.group(0)
                                    .lower()
                                )

                    except Exception:

                        sha256 = None

                break

        if not download_url:

            return {
                "available": True,
                "version": latest_version,
                "download_url": None,
                "sha256": None
            }

        return {
            "available": True,
            "version": latest_version,
            "download_url": download_url,
            "sha256": sha256
        }

    except (
        HTTPError,
        URLError,
        TimeoutError,
        json.JSONDecodeError,
        Exception
    ):

        return None

def download_update(
    download_url,
    destination,
    expected_sha256=None
):
    """
    Baixa o novo OpenDis.exe para um arquivo temporário.

    Retorna True se o download e a validação forem concluídos.
    """

    try:

        request = Request(
            download_url,
            headers={
                "User-Agent":
                    f"{APP_NAME}/{APP_VERSION}",
                "Accept":
                    "application/octet-stream"
            }
        )

        sha256 = hashlib.sha256()

        with urlopen(
            request,
            timeout=60
        ) as response:

            with open(
                destination,
                "wb"
            ) as output:

                while True:

                    chunk = response.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    output.write(
                        chunk
                    )

                    sha256.update(
                        chunk
                    )

        # ----------------------------------------------------
        # VALIDAR SHA256 SE EXISTIR
        # ----------------------------------------------------

        if expected_sha256:

            calculated = (
                sha256.hexdigest()
                .lower()
            )

            if calculated != (
                expected_sha256.lower()
            ):

                try:
                    Path(destination).unlink(
                        missing_ok=True
                    )
                except Exception:
                    pass

                return False

        return (
            Path(destination).exists()
            and
            Path(destination).stat().st_size > 0
        )

    except Exception:

        try:

            Path(destination).unlink(
                missing_ok=True
            )

        except Exception:
            pass

        return False

def create_update_script(
    current_exe,
    new_exe
):
    """
    Cria o updater temporário do OpenDis.

    O updater:
        1. Aguarda o OpenDis antigo fechar.
        2. Cria o backup.
        3. Substitui o OpenDis.exe.
        4. Define PYINSTALLER_RESET_ENVIRONMENT=1.
        5. Abre o novo OpenDis.exe.
        6. Remove os arquivos temporários.

    Não utiliza:
        - CMD
        - find
        - tasklist
        - Shell.Application
        - ShellExecute
        - runas

    O PYINSTALLER_RESET_ENVIRONMENT informa ao bootloader
    do PyInstaller que o novo processo deve ser tratado como
    uma nova instância da aplicação.
    """

    current_exe = Path(
        current_exe
    ).resolve()

    new_exe = Path(
        new_exe
    ).resolve()

    updater = (
        Path(tempfile.gettempdir())
        /
        f"OpenDisUpdater_{os.getpid()}.vbs"
    )

    backup_exe = (
        current_exe.parent
        /
        f"{current_exe.stem}_backup.exe"
    )

    current = str(
        current_exe
    ).replace(
        '"',
        '""'
    )

    new = str(
        new_exe
    ).replace(
        '"',
        '""'
    )

    backup = str(
        backup_exe
    ).replace(
        '"',
        '""'
    )

    updater_file = str(
        updater
    ).replace(
        '"',
        '""'
    )

    script = f'''Option Explicit

Dim shell
Dim fso

Dim currentExe
Dim newExe
Dim backupExe
Dim updaterFile

Dim i
Dim started

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

currentExe = "{current}"
newExe = "{new}"
backupExe = "{backup}"
updaterFile = "{updater_file}"

started = False

' ============================================================
' AGUARDAR O OPENDIS ANTIGO FECHAR
' ============================================================

WScript.Sleep 2500

' ============================================================
' TENTAR ATUALIZAÇÃO
' ============================================================

For i = 1 To 30

    On Error Resume Next

    Err.Clear

    ' ========================================================
    ' VERIFICAR SE O NOVO ARQUIVO EXISTE
    ' ========================================================

    If Not fso.FileExists(newExe) Then

        WScript.Sleep 1000

    Else

        ' ====================================================
        ' REMOVER BACKUP ANTIGO
        ' ====================================================

        If fso.FileExists(backupExe) Then

            Err.Clear

            fso.DeleteFile _
                backupExe, _
                True

        End If

        ' ====================================================
        ' CRIAR BACKUP
        ' ====================================================

        Err.Clear

        fso.CopyFile _
            currentExe, _
            backupExe, _
            True

        If Err.Number = 0 Then

            ' =================================================
            ' SUBSTITUIR OPENDIS.EXE
            ' =================================================

            Err.Clear

            fso.CopyFile _
                newExe, _
                currentExe, _
                True

            If Err.Number = 0 Then

                ' =============================================
                ' VALIDAR NOVO EXECUTÁVEL
                ' =============================================

                If fso.FileExists(currentExe) Then

                    If fso.GetFile(currentExe).Size > 100000 Then

                        ' =====================================
                        ' IMPORTANTE:
                        '
                        ' O OpenDis será iniciado com:
                        '
                        ' PYINSTALLER_RESET_ENVIRONMENT=1
                        '
                        ' Isso faz o bootloader do PyInstaller
                        ' tratar o processo como uma nova
                        ' instância.
                        '
                        ' NÃO usar runas.
                        ' NÃO usar ShellExecute.
                        ' NÃO usar CMD.
                        ' =====================================

                        Err.Clear

                        shell.Environment("Process")("PYINSTALLER_RESET_ENVIRONMENT") = "1"

                        If Err.Number = 0 Then

                            ' =================================
                            ' INICIAR NOVO OPENDIS
                            ' =================================

                            Err.Clear

                            shell.Run _
                                Chr(34) & currentExe & Chr(34), _
                                1, _
                                False

                            If Err.Number = 0 Then

                                started = True

                            End If

                        End If

                        Err.Clear

                        If started Then

                            ' =================================
                            ' O NOVO OPENDIS FOI INICIADO
                            ' =================================

                            On Error GoTo 0

                            WScript.Sleep 4000

                            ' =================================
                            ' REMOVER NOVA VERSÃO TEMPORÁRIA
                            ' =================================

                            On Error Resume Next

                            If fso.FileExists(newExe) Then

                                fso.DeleteFile _
                                    newExe, _
                                    True

                            End If

                            ' =================================
                            ' REMOVER BACKUP
                            ' =================================

                            If fso.FileExists(backupExe) Then

                                fso.DeleteFile _
                                    backupExe, _
                                    True

                            End If

                            ' =================================
                            ' APAGAR O PRÓPRIO VBS
                            '
                            ' Não aparece janela.
                            ' =================================

                            shell.Run _
                                "wscript.exe " & _
                                Chr(34) & _
                                updaterFile & _
                                Chr(34) & _
                                " /delete", _
                                0, _
                                False

                            WScript.Quit 0

                        End If

                    End If

                End If

            End If

            ' =================================================
            ' SE CHEGOU AQUI, FALHOU
            ' RESTAURAR BACKUP
            ' =================================================

            Err.Clear

            If fso.FileExists(backupExe) Then

                fso.CopyFile _
                    backupExe, _
                    currentExe, _
                    True

            End If

        End If

    End If

    On Error GoTo 0

    WScript.Sleep 1000

Next

' ============================================================
' FALHA DEFINITIVA
' ============================================================

On Error Resume Next

If fso.FileExists(newExe) Then

    fso.DeleteFile _
        newExe, _
        True

End If

If fso.FileExists(backupExe) Then

    fso.DeleteFile _
        backupExe, _
        True

End If

WScript.Quit 1
'''

    updater.write_text(
        script,
        encoding="utf-8"
    )

    return updater

def launch_update(
    download_url,
    expected_sha256=None
):
    """
    Baixa a nova versão e prepara a substituição
    do executável atual.

    Retorna:
        True  -> updater iniciado
        False -> falha
    """

    try:

        if not getattr(
            sys,
            "frozen",
            False
        ):

            mb.showinfo(
                "Atualização",
                "A atualização automática funciona "
                "somente na versão .exe."
            )

            return False

        current_exe = Path(
            sys.executable
        ).resolve()

        if not current_exe.exists():

            return False

        temp_dir = Path(
            tempfile.gettempdir()
        )

        new_exe = (
            temp_dir
            /
            f"OpenDis_new_{os.getpid()}.exe"
        )

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        success = download_update(
            download_url,
            new_exe,
            expected_sha256
        )

        if not success:

            return False

        # ----------------------------------------------------
        # CRIAR UPDATER
        # ----------------------------------------------------

        updater = create_update_script(
            current_exe,
            new_exe
        )

        # ----------------------------------------------------
        # EXECUTAR ESCONDIDO
        # ----------------------------------------------------

        subprocess.Popen(
            [
                "cmd.exe",
                "/c",
                str(updater)
            ],
            cwd=str(
                current_exe.parent
            ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
            )
        )

        return True

    except Exception:

        return False

def restart_as_admin():
    """
    Reinicia o OpenDis com privilégios administrativos.

    A elevação acontece antes da interface gráfica ser criada.
    Assim o usuário não perde perfil, usuário, senha ou estado.

    Em modo .exe:
        executa o próprio OpenDis.exe.

    Em modo .py:
        utiliza pythonw.exe para evitar janela CMD.
    """

    if os.name != "nt":
        return True

    if is_running_as_admin():
        return True

    try:
        import ctypes

        # ========================================================
        # MODO EXECUTÁVEL
        # ========================================================

        if getattr(sys, "frozen", False):

            executable = sys.executable

            parameters = ""

            # Preserva argumentos caso existam
            if len(sys.argv) > 1:

                parameters = " ".join(
                    f'"{arg}"'
                    for arg in sys.argv[1:]
                )

        # ========================================================
        # MODO PYTHON
        # ========================================================

        else:

            python_exe = sys.executable

            # ----------------------------------------------------
            # Trocar python.exe por pythonw.exe
            # ----------------------------------------------------

            if python_exe.lower().endswith(
                "python.exe"
            ):

                pythonw = (
                    python_exe[:-10]
                    + "pythonw.exe"
                )

                if os.path.exists(pythonw):

                    python_exe = pythonw

            executable = python_exe

            script = os.path.abspath(
                sys.argv[0]
            )

            arguments = [
                f'"{script}"'
            ]

            arguments.extend(
                f'"{arg}"'
                for arg in sys.argv[1:]
            )

            parameters = " ".join(
                arguments
            )

        # ========================================================
        # SOLICITAR UAC
        # ========================================================

        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            parameters,
            str(BASE_DIR),
            1
        )

        # ========================================================
        # RESULTADO
        # ========================================================

        if result > 32:
            return True

        return False

    except Exception:
        return False

def ensure_admin():
    """
    Garante que o OpenDis esteja executando como administrador
    antes de criar a interface gráfica.

    Retorna:

        True  -> já é administrador
        False -> elevação falhou ou foi cancelada
    """

    if os.name != "nt":
        return True

    if is_running_as_admin():
        return True

    return restart_as_admin()

# ============================================================
# VPNBOOK
# ============================================================

def vpnbook_fetch_page():
    """
    Baixa a página oficial do VPNBook.

    Retorna o HTML ou None.
    """

    request = Request(
        VPNBOOK_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/149.0.0.0 "
                "Safari/537.36"
            ),
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8"
            ),
            "Accept-Language": (
                "pt-BR,pt;q=0.9,en;q=0.8"
            ),
        }
    )

    try:

        with urlopen(
            request,
            timeout=30
        ) as response:

            data = response.read()

            if not data:
                return None

            return data.decode(
                "utf-8",
                errors="ignore"
            )

    except Exception:

        return None

def vpnbook_get_credentials():
    """
    Obtém as credenciais atuais do VPNBook.

    Usuário:
        vpnbook

    A senha é obtida diretamente da página
    oficial do VPNBook.

    Retorna:

        ("vpnbook", "senha")

    ou:

        (None, None)
    """

    html = vpnbook_fetch_page()

    if not html:

        return None, None

    html = unescape(
        html
    )

    password = None

    patterns = [

        # ----------------------------------------------------
        # HTML atual
        # ----------------------------------------------------

        r'(?is)'
        r'(?:Senha|Password)'
        r'.{0,500}?'
        r'<code[^>]*>'
        r'\s*([^<\s]+)'
        r'\s*</code>',

        # ----------------------------------------------------
        # strong
        # ----------------------------------------------------

        r'(?is)'
        r'(?:Senha|Password)'
        r'.{0,500}?'
        r'<strong[^>]*>'
        r'\s*([^<\s]+)'
        r'\s*</strong>',

        # ----------------------------------------------------
        # texto simples
        # ----------------------------------------------------

        r'(?is)'
        r'(?:Senha|Password)'
        r'\s*[:\-]?\s*'
        r'([A-Za-z0-9]{4,})',
    ]

    for pattern in patterns:

        try:

            match = re.search(
                pattern,
                html
            )

            if not match:
                continue

            candidate = (
                match.group(1)
                .strip()
            )

            # ----------------------------------------------
            # Evitar capturar palavras da página
            # ----------------------------------------------

            if candidate.lower() in {
                "copiar",
                "password",
                "senha",
                "vpnbook",
            }:
                continue

            if (
                len(candidate) >= 4
                and
                re.fullmatch(
                    r"[A-Za-z0-9]+",
                    candidate
                )
            ):

                password = candidate

                break

        except Exception:

            continue

    if not password:

        return None, None

    return (
        "vpnbook",
        password
    )

def vpnbook_find_profile(
    server=VPNBOOK_DEFAULT_SERVER,
    protocol=VPNBOOK_DEFAULT_PROTOCOL
):
    """
    Procura um perfil VPNBook específico.

    Exemplo:

        us16.vpnbook.com
        tcp443

    Resultado:

        vpnbook-us16.vpnbook.com-tcp443.ovpn
    """

    server = (
        str(server)
        .strip()
        .lower()
    )

    protocol = (
        str(protocol)
        .strip()
        .lower()
    )

    # --------------------------------------------------------
    # Nome principal
    # --------------------------------------------------------

    filename = (
        f"vpnbook-"
        f"{server}-"
        f"{protocol}.ovpn"
    )

    direct = (
        VPNBOOK_DIR /
        filename
    )

    if direct.exists():

        return direct

    # --------------------------------------------------------
    # Compatibilidade com arquivos antigos
    # --------------------------------------------------------

    candidates = [
        f"*{server}*{protocol}*.ovpn",
        f"*us16*{protocol}*.ovpn",
    ]

    for pattern in candidates:

        matches = sorted(
            VPNBOOK_DIR.glob(
                pattern
            ),
            key=lambda p: p.name.lower()
        )

        if matches:

            return matches[0]

    return None


def vpnbook_download_profile(
    server=VPNBOOK_DEFAULT_SERVER,
    protocol=VPNBOOK_DEFAULT_PROTOCOL
):
    """
    Baixa diretamente um perfil OpenVPN do VPNBook
    usando a API oficial.

    Padrão:

        US Server 1
        us16.vpnbook.com
        TCP 443

    Retorna:

        Path do arquivo .ovpn
    """

    server = (
        str(server)
        .strip()
        .lower()
    )

    protocol = (
        str(protocol)
        .strip()
        .lower()
    )

    if not server:

        raise RuntimeError(
            "Servidor VPNBook não informado."
        )

    if protocol not in {
        "tcp443",
        "tcp80",
        "udp53",
        "udp25000",
    }:

        raise RuntimeError(
            f"Protocolo VPNBook inválido: {protocol}"
        )

    # --------------------------------------------------------
    # RESOLVER IP ATUAL DO SERVIDOR
    # --------------------------------------------------------

    try:

        server_ip = socket.gethostbyname(
            server
        )

    except Exception as e:

        raise RuntimeError(
            "Não foi possível resolver o servidor "
            f"{server}:\n{e}"
        )

    # --------------------------------------------------------
    # MONTAR URL DA API
    # --------------------------------------------------------

    from urllib.parse import urlencode

    params = urlencode(
        {
            "hostname": server,
            "protocol": protocol,
            "ip": server_ip,
        }
    )

    url = (
        VPNBOOK_API_URL
        + "?"
        + params
    )

    # --------------------------------------------------------
    # REQUISIÇÃO
    # --------------------------------------------------------

    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/149.0.0.0 "
                "Safari/537.36"
            ),
            "Accept": (
                "application/x-openvpn-profile,"
                "application/octet-stream,"
                "*/*"
            ),
            "Referer": VPNBOOK_URL,
        }
    )

    try:

        with urlopen(
            request,
            timeout=45
        ) as response:

            data = response.read()

            content_type = (
                response.headers.get(
                    "Content-Type",
                    ""
                )
                .lower()
            )

            content_disposition = (
                response.headers.get(
                    "Content-Disposition",
                    ""
                )
            )

    except Exception as e:

        raise RuntimeError(
            "Falha ao baixar o perfil OpenVPN "
            f"do VPNBook:\n{e}"
        )

    # --------------------------------------------------------
    # VALIDAR RESPOSTA
    # --------------------------------------------------------

    if not data:

        raise RuntimeError(
            "VPNBook retornou um arquivo vazio."
        )

    # --------------------------------------------------------
    # CONVERTER PARA TEXTO
    # --------------------------------------------------------

    try:

        profile_text = data.decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:

        profile_text = ""

    # --------------------------------------------------------
    # VERIFICAR SE REALMENTE É OVPN
    # --------------------------------------------------------

    ovpn_markers = [

        "client",

        "remote ",

        "dev ",

        "proto ",

        "auth-user-pass",

        "<ca>",

        "<cert>",

        "<key>",
    ]

    valid_profile = any(
        marker.lower()
        in profile_text.lower()
        for marker in ovpn_markers
    )

    if not valid_profile:

        preview = (
            profile_text[:500]
            .replace("\r", " ")
            .replace("\n", " ")
        )

        raise RuntimeError(
            "A resposta do VPNBook não parece "
            "ser um perfil OpenVPN válido.\n\n"
            f"Content-Type: {content_type}\n"
            f"Resposta: {preview}"
        )

    # --------------------------------------------------------
    # NOME PADRÃO
    # --------------------------------------------------------

    filename = (
        f"vpnbook-"
        f"{server}-"
        f"{protocol}.ovpn"
    )

    # --------------------------------------------------------
    # TENTAR PEGAR NOME DO HEADER
    # --------------------------------------------------------

    match = re.search(
        r'filename=["\']?([^"\';]+)',
        content_disposition,
        re.IGNORECASE
    )

    if match:

        header_name = (
            match.group(1)
            .strip()
        )

        if header_name.lower().endswith(
            ".ovpn"
        ):

            filename = header_name

    # --------------------------------------------------------
    # SANITIZAR NOME
    # --------------------------------------------------------

    filename = re.sub(
        r'[^A-Za-z0-9._-]',
        "_",
        filename
    )

    if not filename.lower().endswith(
        ".ovpn"
    ):

        filename += ".ovpn"

    # --------------------------------------------------------
    # DESTINO
    # --------------------------------------------------------

    VPNBOOK_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    destination = (
        VPNBOOK_DIR /
        filename
    )

    # --------------------------------------------------------
    # SALVAR
    # --------------------------------------------------------

    destination.write_text(
        profile_text,
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # VALIDAÇÃO FINAL
    # --------------------------------------------------------

    if not destination.exists():

        raise RuntimeError(
            "O perfil foi baixado, mas não "
            "foi possível salvá-lo."
        )

    if destination.stat().st_size < 100:

        try:
            destination.unlink()
        except Exception:
            pass

        raise RuntimeError(
            "O perfil baixado pelo VPNBook "
            "ficou pequeno demais para ser válido."
        )

    return destination

def vpnbook_get_saved_profiles():
    """
    Retorna perfis VPNBook salvos.

    O perfil padrão utilizado pela VPN aleatória
    é US Server 1 / TCP 443.
    """

    VPNBOOK_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    return sorted(
        VPNBOOK_DIR.glob(
            "*.ovpn"
        ),
        key=lambda p: p.name.lower()
    )
def vpnbook_get_random_profile(
    use_saved=True
):
    """
    Obtém o perfil VPNBook utilizado pelo botão
    "VPN ALEATÓRIA".

    Atualmente o padrão é:

        US Server 1
        us16.vpnbook.com
        TCP 443

    Fluxo:

        1. Obtém credenciais atuais
        2. Procura perfil salvo
        3. Se existir, reutiliza
        4. Caso contrário, chama a API
        5. Salva o .ovpn
        6. Retorna perfil + credenciais

    Retorna:

        (
            profile_path,
            username,
            password
        )
    """

    # ========================================================
    # 1. CREDENCIAIS
    # ========================================================

    username, password = (
        vpnbook_get_credentials()
    )

    if not username or not password:

        raise RuntimeError(
            "Não foi possível obter as "
            "credenciais atuais do VPNBook."
        )

    # ========================================================
    # 2. PERFIL SALVO
    # ========================================================

    if use_saved:

        saved = vpnbook_find_profile(
            VPNBOOK_DEFAULT_SERVER,
            VPNBOOK_DEFAULT_PROTOCOL
        )

        if saved:

            return (
                saved,
                username,
                password
            )

    # ========================================================
    # 3. BAIXAR VIA API
    # ========================================================

    profile = vpnbook_download_profile(
        server=VPNBOOK_DEFAULT_SERVER,
        protocol=VPNBOOK_DEFAULT_PROTOCOL
    )

    if not profile:

        raise RuntimeError(
            "VPNBook não retornou um perfil .ovpn."
        )

    # ========================================================
    # 4. RETORNAR
    # ========================================================

    return (
        profile,
        username,
        password
    )
def vpnbook_get_random_saved_profile():
    """
    Retorna o perfil salvo padrão do VPNBook.

    Padrão:

        US Server 1
        us16.vpnbook.com
        TCP 443
    """

    profile = vpnbook_find_profile(
        VPNBOOK_DEFAULT_SERVER,
        VPNBOOK_DEFAULT_PROTOCOL
    )

    if profile:

        return profile

    return None

# ============================================================
# APP
# ============================================================

class OpenDisApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title(
            f"{APP_NAME} - v{APP_VERSION}"
        )

        self.geometry(
            "480x620"
        )

        self.resizable(
            False,
            False
        )

        self.vpn_process = None
        self.vpn_log_file = None
        self.current_profile = None
        self.current_public_ip = None
        self.ovpn_username = ""
        self.ovpn_password = ""
        self.is_vpnbook_profile = False
        self.random_vpn_button = None
        self.save_vpnbook_var = None
        self.save_vpnbook_checkbox = None

        self.center_window()

        self.container = ctk.CTkFrame(
            self,
            fg_color="#1e1e2e",
            corner_radius=0
        )

        self.container.pack(
            fill="both",
            expand=True
        )

        self.footer = ctk.CTkLabel(
            self,
            text="powered by MagnataTile",
            font=ctk.CTkFont(
                size=10,
                underline=True
            ),
            text_color="#7289da",
            cursor="hand2"
        )

        self.footer.bind(
            "<Button-1>",
            lambda event: webbrowser.open(
                "https://github.com/MagnataTile/OpenDis"
            )
        )

        self.footer.place(
            relx=0.5,
            rely=0.98,
            anchor="center"
        )

        self.show_splash()


    # ========================================================
    # CENTRALIZAR
    # ========================================================

    def center_window(self):

        self.update_idletasks()

        x = (
            self.winfo_screenwidth()
            // 2
        ) - (
            480 // 2
        )

        y = (
            self.winfo_screenheight()
            // 2
        ) - (
            620 // 2
        )

        self.geometry(
            f"480x620+{x}+{y}"
        )


    # ========================================================
    # LIMPAR
    # ========================================================

    def clear(self):

        for widget in self.container.winfo_children():

            widget.destroy()


    # ========================================================
    # SPLASH
    # ========================================================

    def show_splash(self):

        self.clear()

        ctk.CTkLabel(
            self.container,
            text="🛡️ OpenDis",
            font=ctk.CTkFont(
                size=36,
                weight="bold"
            ),
            text_color="#5865F2"
        ).pack(
            pady=(60, 5)
        )

        ctk.CTkLabel(
            self.container,
            text="OpenVPN + Discord",
            font=ctk.CTkFont(
                size=14
            ),
            text_color="#a0a0b0"
        ).pack(
            pady=(0, 40)
        )

        self.status_label = ctk.CTkLabel(
            self.container,
            text="🔍 Verificando OpenVPN...",
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#cccccc"
        )

        self.status_label.pack(
            pady=10
        )

        self.progress = ctk.CTkProgressBar(
            self.container,
            width=300,
            mode="indeterminate"
        )

        self.progress.pack(
            pady=10
        )

        self.progress.start()

        self.after(
            500,
            self.check_for_update_ui
        )

    def bring_to_front(self):

        try:

            self.deiconify()
            self.lift()

            self.attributes(
                "-topmost",
                True
            )

            self.after(
                150,
                lambda: self.attributes(
                    "-topmost",
                    False
                )
            )

            self.focus_force()

        except Exception:
            pass
    # ========================================================
    # REQUISITOS
    # ========================================================

    def check_for_update_ui(self):

        self.status_label.configure(
            text="🔄 Verificando atualizações..."
        )

        self.progress.start()

        threading.Thread(
            target=self._check_update_worker,
            daemon=True
        ).start()

    def _check_update_worker(self):

        update = check_for_update()

        self.after(
            0,
            lambda: self._finish_update_check(
                update
            )
        )

    def _finish_update_check(
            self,
            update
    ):

        if not update:
            self.status_label.configure(
                text="⚠️ Não foi possível verificar atualizações"
            )

            self.progress.stop()

            self.after(
                800,
                self.check_requirements
            )

            return

        # --------------------------------------------------------
        # JÁ ESTÁ ATUALIZADO
        # --------------------------------------------------------

        if not update.get(
                "available",
                False
        ):
            self.status_label.configure(
                text="✅ OpenDis atualizado"
            )

            self.progress.stop()

            self.after(
                600,
                self.check_requirements
            )

            return

        # --------------------------------------------------------
        # UPDATE ENCONTRADO
        # --------------------------------------------------------

        new_version = update.get(
            "version",
            "?"
        )

        download_url = update.get(
            "download_url"
        )

        sha256 = update.get(
            "sha256"
        )

        self.progress.stop()

        # --------------------------------------------------------
        # NÃO EXISTE EXE NO RELEASE
        # --------------------------------------------------------

        if not download_url:
            self.status_label.configure(
                text="⚠️ Atualização encontrada, "
                     "mas o EXE não está disponível."
            )

            self.after(
                1200,
                self.check_requirements
            )

            return

        # --------------------------------------------------------
        # PERGUNTAR AO USUÁRIO
        # --------------------------------------------------------

        answer = mb.askyesno(
            "Nova atualização disponível",
            (
                f"Uma nova versão do OpenDis está disponível.\n\n"
                f"Versão atual: v{APP_VERSION}\n"
                f"Nova versão: v{new_version}\n\n"
                f"Deseja atualizar agora?"
            )
        )

        if not answer:
            self.status_label.configure(
                text="⏭️ Atualização ignorada"
            )

            self.after(
                700,
                self.check_requirements
            )

            return

        # --------------------------------------------------------
        # USUÁRIO ACEITOU
        # --------------------------------------------------------

        self.status_label.configure(
            text=f"⬇️ Baixando v{new_version}..."
        )

        self.progress.start()

        threading.Thread(
            target=self._download_update_worker,
            args=(
                download_url,
                sha256,
                new_version
            ),
            daemon=True
        ).start()

    def _download_update_worker(
            self,
            download_url,
            sha256,
            new_version
    ):
        """
        Baixa e instala a nova versão.

        O OpenDis não tenta substituir o próprio EXE.
        Ele entrega a operação para um updater externo.
        """

        try:

            # ========================================================
            # VERIFICAR SE ESTÁ RODANDO COMO EXE
            # ========================================================

            if not getattr(
                    sys,
                    "frozen",
                    False
            ):
                raise RuntimeError(
                    "A atualização automática funciona "
                    "somente na versão .exe."
                )

            # ========================================================
            # EXECUTÁVEL ATUAL
            # ========================================================

            current_exe = Path(
                sys.executable
            ).resolve()

            if not current_exe.exists():
                raise RuntimeError(
                    "Não foi possível localizar "
                    "o OpenDis.exe atual."
                )

            # ========================================================
            # ARQUIVO TEMPORÁRIO
            # ========================================================

            temp_dir = Path(
                tempfile.gettempdir()
            )

            new_exe = (
                    temp_dir
                    /
                    f"OpenDis_new_{os.getpid()}.exe"
            )

            # ========================================================
            # LIMPAR ARQUIVO TEMPORÁRIO ANTIGO
            # ========================================================

            try:

                new_exe.unlink(
                    missing_ok=True
                )

            except Exception:
                pass

            # ========================================================
            # DOWNLOAD
            # ========================================================

            self.after(
                0,
                lambda:
                self.status_label.configure(
                    text=f"⬇️ Baixando v{new_version}..."
                )
            )

            success = download_update(
                download_url,
                new_exe,
                sha256
            )

            if not success:
                raise RuntimeError(
                    "Não foi possível baixar ou validar "
                    "a nova versão."
                )

            # ========================================================
            # VERIFICAR TAMANHO
            # ========================================================

            if not new_exe.exists():
                raise RuntimeError(
                    "O arquivo da nova versão não foi encontrado."
                )

            if new_exe.stat().st_size < 100000:
                raise RuntimeError(
                    "O arquivo baixado parece inválido."
                )

            # ========================================================
            # PREPARAR UPDATER
            # ========================================================

            self.after(
                0,
                lambda:
                self.status_label.configure(
                    text="🔄 Preparando atualização..."
                )
            )

            updater = create_update_script(
                current_exe,
                new_exe
            )

            if not updater.exists():
                raise RuntimeError(
                    "Não foi possível criar "
                    "o atualizador."
                )

            # ========================================================
            # INICIAR UPDATER
            # ========================================================

            subprocess.Popen(
                [
                    "wscript.exe",
                    str(updater)
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # ========================================================
            # IMPORTANTE:
            #
            # Não esperar o updater.
            # Não apagar o EXE.
            # Não executar mais nada aqui.
            #
            # O updater fará:
            #
            #   fechar OpenDis
            #       ↓
            #   backup
            #       ↓
            #   substituir
            #       ↓
            #   iniciar novo OpenDis
            # ========================================================

            self.after(
                0,
                lambda:
                self.status_label.configure(
                    text="✅ Atualização preparada. Reiniciando..."
                )
            )

            # Pequeno intervalo para garantir que o updater
            # recebeu o comando antes de destruirmos a janela.

            time.sleep(1)

            self.after(
                0,
                self.destroy
            )

        except Exception as e:

            error = str(e)

            self.after(
                0,
                lambda msg=error:
                self._update_failed_with_message(
                    msg
                )
            )

    def _update_failed(self):

        try:

            self.progress.stop()

        except Exception:
            pass

        self.status_label.configure(
            text="❌ Falha ao atualizar"
        )

        mb.showerror(
            "Atualização",
            (
                "Não foi possível instalar "
                "a nova versão.\n\n"
                "O OpenDis continuará usando "
                "a versão atual."
            )
        )

        self.after(
            500,
            self.check_requirements
        )

    def _update_failed_with_message(
            self,
            message
    ):
        try:

            self.progress.stop()

        except Exception:
            pass

        self.status_label.configure(
            text="❌ Falha ao atualizar"
        )

        mb.showerror(
            "Atualização",
            (
                "Não foi possível instalar "
                "a nova versão.\n\n"
                f"{message[:1000]}\n\n"
                "O OpenDis continuará usando "
                "a versão atual."
            )
        )

        self.after(
            500,
            self.check_requirements
        )
    def check_requirements(self):

        self.progress.stop()

        self.progress.pack_forget()

        openvpn = find_openvpn_executable()

        if not openvpn:

            self.show_missing_openvpn()

            return

        self.status_label.configure(
            text="OK: OpenVPN encontrado"
        )

        discord = find_discord_executable()

        if not discord:

            self.after(
                800,
                self.show_missing_discord
            )

            return

        self.status_label.configure(
            text="OK: OpenVPN + Discord detectados"
        )

        self.after(
            800,
            self.show_profile_screen
        )


    # ========================================================
    # OPENVPN AUSENTE
    # ========================================================

    def show_missing_openvpn(self):

        self.clear()

        ctk.CTkLabel(
            self.container,
            text="FAIL: OpenVPN não encontrado",
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            ),
            text_color="#ff6b6b"
        ).pack(
            pady=(70, 15)
        )

        ctk.CTkLabel(
            self.container,
            text=(
                "O OpenDis precisa do OpenVPN Community\n"
                "para estabelecer a conexão VPN."
            ),
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#a0a0b0",
            justify="center"
        ).pack(
            pady=10
        )

        ctk.CTkButton(
            self.container,
            text="📥 Instalar OpenVPN automaticamente",
            command=self.install_openvpn_ui,
            fg_color="#5865F2",
            hover_color="#4752C4",
            height=45,
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        ).pack(
            pady=20
        )

        ctk.CTkButton(
            self.container,
            text="❌ Sair",
            command=self.destroy,
            fg_color="#ed4245",
            hover_color="#c03538",
            height=35
        ).pack()


    def install_openvpn_ui(self):

        self.clear()

        self.status_label = ctk.CTkLabel(
            self.container,
            text="📥 Instalando OpenVPN...",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            ),
            text_color="#cccccc"
        )

        self.status_label.pack(
            pady=(100, 20)
        )

        self.progress = ctk.CTkProgressBar(
            self.container,
            width=300,
            mode="indeterminate"
        )

        self.progress.pack(
            pady=10
        )

        self.progress.start()

        threading.Thread(
            target=self._install_openvpn_worker,
            daemon=True
        ).start()


    def _install_openvpn_worker(self):

        ok, result = install_openvpn()

        self.after(
            0,
            lambda: self._finish_openvpn_install(
                ok,
                result
            )
        )


    def _finish_openvpn_install(
        self,
        ok,
        result
    ):

        self.progress.stop()

        if ok:

            self.status_label.configure(
                text="OK: OpenVPN instalado!"
            )

            self.after(
                1200,
                self.check_requirements
            )

        else:

            self.status_label.configure(
                text="❌ Falha na instalação"
            )

            mb.showerror(
                "OpenVPN",
                str(result)[:1000]
            )

            self.after(
                1000,
                self.show_missing_openvpn
            )


    # ========================================================
    # DISCORD AUSENTE
    # ========================================================

    def show_missing_discord(self):

        self.clear()

        ctk.CTkLabel(
            self.container,
            text="FAIL: Discord não encontrado",
            font=ctk.CTkFont(
                size=22,
                weight="bold"
            ),
            text_color="#ff6b6b"
        ).pack(
            pady=(70, 15)
        )

        ctk.CTkLabel(
            self.container,
            text=(
                "O OpenDis precisa encontrar o Discord\n"
                "antes de iniciar o procedimento."
            ),
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#a0a0b0",
            justify="center"
        ).pack(
            pady=10
        )

        ctk.CTkButton(
            self.container,
            text="📥 Instalar Discord automaticamente",
            command=self.install_discord_ui,
            fg_color="#5865F2",
            hover_color="#4752C4",
            height=45,
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        ).pack(
            pady=20
        )

        ctk.CTkButton(
            self.container,
            text="❌ Sair",
            command=self.destroy,
            fg_color="#ed4245",
            hover_color="#c03538",
            height=35
        ).pack()


    def install_discord_ui(self):

        self.clear()

        self.status_label = ctk.CTkLabel(
            self.container,
            text="📥 Instalando Discord...",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            ),
            text_color="#cccccc"
        )

        self.status_label.pack(
            pady=(100, 20)
        )

        self.progress = ctk.CTkProgressBar(
            self.container,
            width=300,
            mode="indeterminate"
        )

        self.progress.pack(
            pady=10
        )

        self.progress.start()

        threading.Thread(
            target=self._install_discord_worker,
            daemon=True
        ).start()


    def _install_discord_worker(self):

        ok, result = install_discord()

        self.after(
            0,
            lambda: self._finish_discord_install(
                ok,
                result
            )
        )


    def _finish_discord_install(
        self,
        ok,
        result
    ):

        self.progress.stop()

        if ok:

            self.status_label.configure(
                text="OK: Discord instalado!"
            )

            self.after(
                1200,
                self.check_requirements
            )

        else:

            self.status_label.configure(
                text="❌ Falha na instalação"
            )

            mb.showerror(
                "Discord",
                str(result)[:1000]
            )

            self.after(
                1000,
                self.show_missing_discord
            )


    # ========================================================
    # PERFIL OVPN
    # ========================================================

    def show_profile_screen(self):

        self.clear()

        ctk.CTkLabel(
            self.container,
            text="🔐 Configuração VPN",
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            ),
            text_color="#cccccc"
        ).pack(
            pady=(40, 5)
        )

        ctk.CTkLabel(
            self.container,
            text="Selecione como deseja conectar",
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#a0a0b0"
        ).pack(
            pady=(5, 15)
        )

        # ========================================================
        # VPN ALEATÓRIA
        # ========================================================

        self.random_vpn_button = ctk.CTkButton(
            self.container,
            text="🎲 VPN ALEATÓRIA VPNBook",
            command=self.random_vpn_ui,
            fg_color="#3ba55d",
            hover_color="#2d7d46",
            width=330,
            height=45,
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
            corner_radius=22
        )

        self.random_vpn_button.pack(
            pady=(5, 10)
        )

        # ========================================================
        # GUARDAR REDE
        # ========================================================

        self.save_vpnbook_var = ctk.BooleanVar(
            value=True
        )

        self.save_vpnbook_checkbox = (
            ctk.CTkCheckBox(
                self.container,
                text="Guardar rede VPNBook",
                variable=self.save_vpnbook_var,
                font=ctk.CTkFont(
                    size=12
                ),
                text_color="#cccccc",
                fg_color="#5865F2",
                hover_color="#4752C4",
                border_color="#666675",
                border_width=2
            )
        )

        self.save_vpnbook_checkbox.pack(
            pady=(3, 3)
        )

        ctk.CTkLabel(
            self.container,
            text=(
                "O perfil .ovpn será salvo para "
                "não precisar baixá-lo novamente."
            ),
            font=ctk.CTkFont(
                size=10
            ),
            text_color="#666675"
        ).pack(
            pady=(0, 15)
        )

        # ========================================================
        # SEPARADOR
        # ========================================================

        ctk.CTkLabel(
            self.container,
            text="— ou selecione manualmente —",
            font=ctk.CTkFont(
                size=11
            ),
            text_color="#666675"
        ).pack(
            pady=(0, 10)
        )

        # ========================================================
        # PERFIS MANUAIS
        # ========================================================

        files = get_ovpn_files()

        self.ovpn_var = ctk.StringVar()

        if files:

            names = [
                f.name
                for f in files
            ]

            self.ovpn_var.set(
                names[0]
            )

            self.ovpn_menu = ctk.CTkOptionMenu(
                self.container,
                variable=self.ovpn_var,
                values=names,
                width=330,
                height=40,
                command=lambda _: self.refresh_profile_info()
            )

            self.ovpn_menu.pack(
                pady=8
            )

        else:

            self.ovpn_var.set("")

            self.ovpn_menu = None

            ctk.CTkLabel(
                self.container,
                text=(
                    "Nenhum .ovpn manual encontrado em:\n"
                    f"{VPN_DIR}"
                ),
                font=ctk.CTkFont(
                    size=11
                ),
                text_color="#666675",
                justify="center"
            ).pack(
                pady=8
            )

        # ========================================================
        # IMPORTAR
        # ========================================================

        ctk.CTkButton(
            self.container,
            text="📂 Adicionar / selecionar .ovpn",
            command=self.import_profile,
            fg_color="#2f3136",
            hover_color="#40444b",
            width=330,
            height=38
        ).pack(
            pady=8
        )

        # ========================================================
        # INFORMAÇÃO
        # ========================================================

        self.credentials_hint = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(
                size=12
            ),
            text_color="#a0a0b0"
        )

        self.credentials_hint.pack(
            pady=5
        )

        self.username_entry = None
        self.password_entry = None

        # ========================================================
        # CONTINUAR
        # ========================================================

        self.continue_btn = ctk.CTkButton(
            self.container,
            text="➡️ CONTINUAR",
            command=self.profile_selected,
            fg_color="#5865F2",
            hover_color="#4752C4",
            height=46,
            width=330,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            ),
            corner_radius=23
        )

        self.continue_btn.pack(
            pady=15
        )

        self.refresh_profile_info()


    def import_profile(self):

        path = import_ovpn_file()

        if not path:
            return

        self.show_profile_screen()


    def selected_profile_path(self):

        if not self.ovpn_var:
            return None

        name = self.ovpn_var.get().strip()

        if not name:
            return None

        path = VPN_DIR / name

        if not path.exists():
            return None

        return path


    def refresh_profile_info(self):

        profile = self.selected_profile_path()

        if not profile:
            self.credentials_hint.configure(
                text="⚠️ Selecione um perfil .ovpn"
            )

            return

        requires = profile_requires_credentials(
            profile
        )

        if requires:

            self.credentials_hint.configure(
                text="🔐 Este perfil solicita usuário e senha."
            )

        else:

            self.credentials_hint.configure(
                text="✅ Este perfil não solicita credenciais."
            )


    # ========================================================
    # CREDENCIAIS
    # ========================================================

    def profile_selected(self):

        profile = self.selected_profile_path()

        if not profile:

            mb.showwarning(
                "Perfil",
                "Selecione um arquivo .ovpn."
            )

            return

        self.current_profile = profile

        if profile_requires_credentials(
            profile
        ):

            self.show_credentials_screen()

        else:

            self.show_connect_screen()

    def show_credentials_screen(self):

        self.clear()

        ctk.CTkLabel(
            self.container,
            text="🔐 Credenciais OpenVPN",
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            ),
            text_color="#cccccc"
        ).pack(
            pady=(45, 10)
        )

        ctk.CTkLabel(
            self.container,
            text=(
                "Este perfil exige autenticação.\n"
                "Informe as credenciais do OpenVPN."
            ),
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#a0a0b0",
            justify="center"
        ).pack(
            pady=10
        )

        # ========================================================
        # USUÁRIO
        # ========================================================

        ctk.CTkLabel(
            self.container,
            text="Usuário",
            font=ctk.CTkFont(
                size=12
            ),
            text_color="#cccccc"
        ).pack(
            pady=(8, 3)
        )

        self.username_entry = ctk.CTkEntry(
            self.container,
            width=320,
            height=40,
            placeholder_text="Usuário OpenVPN"
        )

        self.username_entry.pack(
            pady=5
        )

        # ========================================================
        # SENHA
        # ========================================================

        ctk.CTkLabel(
            self.container,
            text="Senha",
            font=ctk.CTkFont(
                size=12
            ),
            text_color="#cccccc"
        ).pack(
            pady=(8, 3)
        )

        self.password_entry = ctk.CTkEntry(
            self.container,
            width=320,
            height=40,
            show="*",
            placeholder_text="Senha OpenVPN"
        )

        self.password_entry.pack(
            pady=5
        )

        # ========================================================
        # LEMBRAR CREDENCIAIS
        # ========================================================

        self.remember_credentials_var = ctk.BooleanVar(
            value=False
        )

        self.remember_credentials_checkbox = ctk.CTkCheckBox(
            self.container,
            text="Lembrar credenciais",
            variable=self.remember_credentials_var,
            font=ctk.CTkFont(
                size=12
            ),
            text_color="#cccccc",
            fg_color="#5865F2",
            hover_color="#4752C4",
            border_color="#666675",
            border_width=2
        )

        self.remember_credentials_checkbox.pack(
            pady=(10, 5)
        )

        ctk.CTkLabel(
            self.container,
            text="🔒 As credenciais são protegidas pelo Windows.",
            font=ctk.CTkFont(
                size=10
            ),
            text_color="#666675"
        ).pack(
            pady=(0, 8)
        )

        # ========================================================
        # CARREGAR CREDENCIAL SALVA
        # ========================================================

        saved_credentials = None

        try:

            if self.current_profile:
                saved_credentials = load_saved_credentials(
                    self.current_profile
                )

        except Exception:

            saved_credentials = None

        # ========================================================
        # PREENCHER CREDENCIAL SALVA
        # ========================================================

        if saved_credentials:

            username = saved_credentials.get(
                "username",
                ""
            )

            password = saved_credentials.get(
                "password",
                ""
            )

            if username:
                self.username_entry.insert(
                    0,
                    username
                )

            if password:
                self.password_entry.insert(
                    0,
                    password
                )

            self.remember_credentials_var.set(
                True
            )

        # ========================================================
        # CONTINUAR
        # ========================================================

        ctk.CTkButton(
            self.container,
            text="➡️ CONTINUAR",
            command=self.credentials_submitted,
            fg_color="#5865F2",
            hover_color="#4752C4",
            height=48,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            ),
            corner_radius=25
        ).pack(
            pady=(15, 8)
        )

        # ========================================================
        # VOLTAR
        # ========================================================

        ctk.CTkButton(
            self.container,
            text="← VOLTAR",
            command=self.back_to_profile_screen,
            fg_color="#4a4a5a",
            hover_color="#383846",
            width=180,
            height=35,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            corner_radius=18
        ).pack(
            pady=(0, 10)
        )

    def credentials_submitted(self):

        username = self.username_entry.get().strip()

        password = self.password_entry.get()

        # ========================================================
        # VALIDAR
        # ========================================================

        if not username or not password:
            mb.showwarning(
                "Credenciais",
                "Informe usuário e senha."
            )

            return

        # ========================================================
        # GUARDAR NA MEMÓRIA DA SESSÃO
        # ========================================================

        self.ovpn_username = username
        self.ovpn_password = password

        # ========================================================
        # LEMBRAR CREDENCIAIS
        # ========================================================

        remember = False

        try:

            remember = bool(
                self.remember_credentials_var.get()
            )

        except Exception:

            remember = False

        # ========================================================
        # SALVAR
        # ========================================================

        if remember:

            if not self.current_profile:
                mb.showerror(
                    "Credenciais",
                    "Nenhum perfil .ovpn foi selecionado."
                )

                return

            saved = save_credentials(
                self.current_profile,
                username,
                password
            )

            if not saved:
                mb.showwarning(
                    "Credenciais",
                    (
                        "Não foi possível salvar as credenciais.\n\n"
                        "Você poderá continuar normalmente, "
                        "mas será necessário digitá-las novamente "
                        "na próxima execução."
                    )
                )

        # ========================================================
        # NÃO LEMBRAR
        # ========================================================

        else:

            if self.current_profile:
                delete_saved_credentials(
                    self.current_profile
                )

                # ========================================================
                # CONTINUAR
                # ========================================================

                ctk.CTkButton(
                    self.container,
                    text="➡️ CONTINUAR",
                    command=self.credentials_submitted,
                    fg_color="#5865F2",
                    hover_color="#4752C4",
                    height=48,
                    font=ctk.CTkFont(
                        size=16,
                        weight="bold"
                    ),
                    corner_radius=25
                ).pack(
                    pady=(15, 8)
                )

                # ========================================================
                # VOLTAR
                # ========================================================

                ctk.CTkButton(
                    self.container,
                    text="← VOLTAR",
                    command=self.back_to_profile_screen,
                    fg_color="#4a4a5a",
                    hover_color="#383846",
                    width=180,
                    height=35,
                    font=ctk.CTkFont(
                        size=13,
                        weight="bold"
                    ),
                    corner_radius=18
                ).pack(
                    pady=(0, 10)
                )

        self.show_connect_screen()


    # ========================================================
    # TELA DE EXECUÇÃO
    # ========================================================
    def back_to_profile_screen(self):
        """
        Volta para a tela de seleção/configuração da VPN.
        """
        self.current_profile = None
        self.ovpn_username = ""
        self.ovpn_password = ""
        self.is_vpnbook_profile = False

        self.show_profile_screen()

    def show_connect_screen(self):
        self.clear()

        ctk.CTkLabel(
            self.container,
            text="🚀 Pronto para iniciar!",
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            ),
            text_color="#cccccc"
        ).pack(
            pady=(45, 5)
        )

        ctk.CTkLabel(
            self.container,
            text=(
                "Clique em Iniciar para:\n"
                "Conectar VPN\n"
                "Abrir Discord\n"
                "Aguardar conexão\n"
                "Desconectar VPN\n"
                "Estabilizar Discord"
            ),
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#a0a0b0",
            justify="center"
        ).pack(
            pady=(10, 20)
        )

        # ========================================================
        # LOG
        # ========================================================

        self.log_text = ctk.CTkTextbox(
            self.container,
            width=360,
            height=120,
            font=ctk.CTkFont(
                size=12
            ),
            fg_color="#12121a",
            text_color="#8e9297"
        )

        self.log_text.pack(
            pady=(5, 10)
        )

        self.log_text.insert(
            "1.0",
            "[] Aguardando início...\n"
        )

        self.log_text.configure(
            state="disabled"
        )

        # ========================================================
        # PORCENTAGEM
        # ========================================================

        self.progress_label = ctk.CTkLabel(
            self.container,
            text="0%",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            text_color="#cccccc"
        )

        self.progress_label.pack(
            pady=(5, 2)
        )

        # ========================================================
        # BARRA DE PROGRESSO
        # ========================================================

        self.progress_bar = ctk.CTkProgressBar(
            self.container,
            width=360,
            height=12,
            mode="determinate"
        )

        self.progress_bar.set(
            0
        )

        self.progress_bar.pack(
            pady=(0, 10)
        )

        # ========================================================
        # BOTÃO PRINCIPAL
        # ========================================================

        self.start_btn = ctk.CTkButton(
            self.container,
            text="⚡ INICIAR",
            command=self.run_unlock,
            fg_color="#5865F2",
            hover_color="#4752C4",
            height=50,
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            ),
            corner_radius=25
        )

        self.start_btn.pack(
            pady=10
        )

        # ========================================================
        # STATUS FINAL
        # ========================================================

        self.final_status = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(
                size=14
            ),
            text_color="#cccccc"
        )

        self.final_status.pack(
            pady=5
        )
        self.activity_bar = ctk.CTkProgressBar(
            self.container,
            width=160,
            height=6,
            mode="indeterminate"
        )

        self.activity_bar.pack(
            pady=(0, 8)
        )


        # ========================================================
        # ESTADO INICIAL
        # ========================================================

        self.set_progress(
            0,
            "Aguardando início..."
        )

    def bring_to_front(self):
        """
        Traz o OpenDis para frente depois que o Discord foi aberto
        e a VPN foi desconectada.

        Não recria a interface e não limpa o log.
        """

        try:

            self.deiconify()

            self.lift()

            # Coloca temporariamente acima das outras janelas
            self.attributes(
                "-topmost",
                True
            )

            self.focus_force()

            # Depois remove o topmost para não deixar
            # o OpenDis permanentemente sobre todas as janelas.
            self.after(
                1200,
                lambda: self.attributes(
                    "-topmost",
                    False
                )
            )

        except Exception:
            pass

    def set_progress(
            self,
            percent,
            status=None
    ):
        """
        Atualiza visualmente o progresso da operação.

        percent:
            0 até 100

        status:
            Texto opcional exibido abaixo/acima da barra.
        """

        try:

            percent = max(
                0,
                min(
                    100,
                    int(percent)
                )
            )

            # ----------------------------------------------------
            # Barra
            # ----------------------------------------------------

            if hasattr(
                    self,
                    "progress_bar"
            ):
                self.progress_bar.set(
                    percent / 100
                )

            # ----------------------------------------------------
            # Porcentagem
            # ----------------------------------------------------

            if hasattr(
                    self,
                    "progress_label"
            ):
                self.progress_label.configure(
                    text=f"{percent}%"
                )

            # ----------------------------------------------------
            # Status
            # ----------------------------------------------------

            if (
                    status
                    and
                    hasattr(
                        self,
                        "final_status"
                    )
            ):
                self.final_status.configure(
                    text=status
                )

        except Exception:
            pass
    # ========================================================
    # LOG UI
    # ========================================================

    def log(self, message):

        timestamp = time.strftime(
            "%H:%M:%S"
        )

        line = (
            f"[{timestamp}] "
            f"{message}"
        )

        try:

            self.log_text.configure(
                state="normal"
            )

            self.log_text.insert(
                "end",
                line + "\n"
            )

            self.log_text.see(
                "end"
            )

            self.log_text.configure(
                state="disabled"
            )

        except Exception:
            pass

        # ========================================================
        # VPN ALEATÓRIA
        # ========================================================

    def random_vpn_ui(self):

        try:

            self.random_vpn_button.configure(
                state="disabled",
                text="🔄 Obtendo VPN..."
            )

            self.save_vpnbook_checkbox.configure(
                state="disabled"
            )

        except Exception:
            pass

        threading.Thread(
            target=self._random_vpn_worker,
            daemon=True
        ).start()

    def _random_vpn_worker(self):

        try:

            # ----------------------------------------------------
            # Verificar opção guardar
            # ----------------------------------------------------

            save_network = True

            try:

                save_network = bool(
                    self.save_vpnbook_var.get()
                )

            except Exception:

                pass

            # ----------------------------------------------------
            # Informar o que está fazendo
            # ----------------------------------------------------

            self.after(
                0,
                lambda:
                self.log(
                    "🌐 VPNBook: US Server 1"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🔌 Protocolo: TCP 443"
                )
            )

            # ----------------------------------------------------
            # Procurar perfil salvo
            # ----------------------------------------------------

            profile = None

            if save_network:
                profile = (
                    vpnbook_find_profile(
                        VPNBOOK_DEFAULT_SERVER,
                        VPNBOOK_DEFAULT_PROTOCOL
                    )
                )

            # ----------------------------------------------------
            # Perfil já existente
            # ----------------------------------------------------

            if profile:

                self.after(
                    0,
                    lambda p=profile:
                    self.log(
                        f"💾 Rede salva encontrada: {p.name}"
                    )
                )

                username, password = (
                    vpnbook_get_credentials()
                )

                if not username or not password:
                    raise RuntimeError(
                        "Não foi possível obter "
                        "a senha atual do VPNBook."
                    )

                result = (
                    profile,
                    username,
                    password
                )

            # ----------------------------------------------------
            # Baixar novo perfil
            # ----------------------------------------------------

            else:

                self.after(
                    0,
                    lambda:
                    self.log(
                        "📥 Baixando configuração OpenVPN..."
                    )
                )

                result = (
                    vpnbook_get_random_profile(
                        use_saved=False
                    )
                )

                profile, username, password = (
                    result
                )

                self.after(
                    0,
                    lambda p=profile:
                    self.log(
                        f"✅ .ovpn baixado: {p.name}"
                    )
                )

            # ----------------------------------------------------
            # Atualizar GUI
            # ----------------------------------------------------

            self.after(
                0,
                lambda p=profile,
                       u=username,
                       pw=password:
                self._random_vpn_success(
                    p,
                    u,
                    pw
                )
            )

        except Exception as e:

            error = str(e)

            self.after(
                0,
                lambda msg=error:
                self._random_vpn_error(
                    msg
                )
            )

    def _random_vpn_success(
            self,
            profile,
            username,
            password
    ):

        # ----------------------------------------------------
        # Perfil atual
        # ----------------------------------------------------

        self.current_profile = Path(
            profile
        )

        # ----------------------------------------------------
        # Credenciais
        # ----------------------------------------------------

        self.ovpn_username = (
            username
        )

        self.ovpn_password = (
            password
        )

        # ----------------------------------------------------
        # Origem
        # ----------------------------------------------------

        self.is_vpnbook_profile = True

        # ----------------------------------------------------
        # Mostrar informações
        # ----------------------------------------------------

        try:

            self.log(
                "🎲 VPNBook preparada."
            )

            self.log(
                "🇺🇸 Servidor: US Server 1"
            )

            self.log(
                "🔌 Protocolo: TCP 443"
            )

            self.log(
                f"📄 Perfil: {self.current_profile.name}"
            )

            self.log(
                f"👤 Usuário: {username}"
            )

        except Exception:

            pass

        # ----------------------------------------------------
        # Continuar
        # ----------------------------------------------------

        self.show_connect_screen()

    def _random_vpn_error(
            self,
            error
    ):

        try:

            self.random_vpn_button.configure(
                state="normal",
                text="🎲 VPN ALEATÓRIA"
            )

            self.save_vpnbook_checkbox.configure(
                state="normal"
            )

        except Exception:
            pass

        mb.showerror(
            "VPN Aleatória",
            (
                "Não foi possível obter uma VPN "
                "aleatória do VPNBook.\n\n"
                f"{error[:1500]}"
            )
        )
    # ========================================================
    # INICIAR
    # ========================================================

    def run_unlock(self):
        """
        Inicia a operação.

        A elevação administrativa NÃO acontece aqui.

        O OpenDis já deve ter sido iniciado como administrador
        antes da interface gráfica aparecer.
        """

        # ========================================================
        # VERIFICAÇÃO DE SEGURANÇA
        # ========================================================

        if os.name == "nt" and not is_running_as_admin():
            mb.showerror(
                "OpenDis",
                (
                    "O OpenDis não está executando como Administrador.\n\n"
                    "Feche o programa e abra novamente."
                )
            )

            return

        # ========================================================
        # BLOQUEAR BOTÃO
        # ========================================================

        self.start_btn.configure(
            state="disabled",
            text="🔄 INICIANDO..."
        )

        # ========================================================
        # PROGRESSO INICIAL
        # ========================================================

        self.set_progress(
            5,
            "Preparando operação..."
        )

        self.log(
            "🚀 Iniciando procedimento..."
        )

        # ========================================================
        # EXECUÇÃO
        # ========================================================

        threading.Thread(
            target=self._run_unlock,
            daemon=True
        ).start()
        self.activity_bar.start()

    # ========================================================
    # EXECUÇÃO PRINCIPAL
    # ========================================================

    def _run_unlock(self):
        """
        Execução principal do OpenDis.

        Fluxo:

            detectar OpenVPN
            detectar Discord
            validar .ovpn
            criar log
            conectar OpenVPN
            aguardar Initialization Sequence Completed
            confirmar mudança de IP
            abrir Discord
            aguardar Discord
            desconectar VPN
            voltar para tela principal
            aguardar estabilização do Discord
            mostrar CONCLUIR E FECHAR

        """

        vpn_connected = False
        credentials_file = None
        process = None
        log_handle = None
        keep_log_file = False

        try:

            # ====================================================
            # 1. LOCALIZAR OPENVPN
            # ====================================================

            self.after(
                0,
                lambda: self.set_progress(
                    10,
                    "Localizando OpenVPN..."
                )
            )

            openvpn = find_openvpn_executable()

            if not openvpn:
                raise RuntimeError(
                    "OpenVPN Community não foi encontrado."
                )

            self.after(
                0,
                lambda p=openvpn:
                self.log(
                    f"🔎 OpenVPN: {p}"
                )
            )

            # ====================================================
            # 2. LOCALIZAR DISCORD
            # ====================================================

            self.after(
                0,
                lambda: self.set_progress(
                    15,
                    "Localizando Discord..."
                )
            )

            discord = find_discord_executable()

            if not discord:
                raise RuntimeError(
                    "Discord não foi encontrado."
                )

            self.after(
                0,
                lambda p=discord:
                self.log(
                    f"🔎 Discord: {p}"
                )
            )

            # ====================================================
            # 3. PERFIL OVPN
            # ====================================================

            self.after(
                0,
                lambda: self.set_progress(
                    20,
                    "Validando perfil VPN..."
                )
            )

            profile = getattr(
                self,
                "current_profile",
                None
            )

            if not profile:
                raise RuntimeError(
                    "Nenhum perfil .ovpn selecionado."
                )

            profile = Path(
                profile
            )

            if not profile.exists():
                raise RuntimeError(
                    f"Perfil não encontrado:\n{profile}"
                )

            if profile.suffix.lower() != ".ovpn":
                raise RuntimeError(
                    "O arquivo selecionado não é um perfil .ovpn."
                )

            self.after(
                0,
                lambda p=profile.name:
                self.log(
                    f"📄 Perfil: {p}"
                )
            )

            # ====================================================
            # 4. IP INICIAL
            # ====================================================

            self.after(
                0,
                lambda: self.set_progress(
                    25,
                    "Obtendo IP atual..."
                )
            )

            self.current_public_ip = get_public_ip(
                timeout=10
            )

            if self.current_public_ip:
                self.after(
                    0,
                    lambda ip=self.current_public_ip:
                    self.log(
                        f"🌐 IP inicial: {ip}"
                    )
                )

            # ====================================================
            # 5. PREPARAÇÃO DO OPENVPN
            # ====================================================

            self.after(
                0,
                lambda: self.set_progress(
                    30,
                    "Preparando conexão VPN..."
                )
            )


            command = [
                openvpn,
                "--config",
                str(profile),
                "--disable-dco",
            ]

            if profile_requires_credentials(profile):

                username = getattr(
                    self,
                    "ovpn_username",
                    ""
                )

                password = getattr(
                    self,
                    "ovpn_password",
                    ""
                )

                if not username or not password:
                    raise RuntimeError(
                        "Este perfil exige usuário e senha."
                    )

                credentials_file = (
                        LOG_DIR
                        /
                        f".credentials_{os.getpid()}_{int(time.time())}.tmp"
                )

                credentials_file.write_text(
                    f"{username}\n{password}\n",
                    encoding="utf-8"
                )

                try:

                    os.chmod(
                        credentials_file,
                        0o600
                    )

                except Exception:
                    pass

                command.extend(
                    [
                        "--auth-user-pass",
                        str(credentials_file)
                    ]
                )

            # ====================================================
            # 6. PREPARAR PROCESSO
            # ====================================================

            creation_flags = 0
            startupinfo = None

            if os.name == "nt":
                creation_flags = (
                        subprocess.CREATE_NO_WINDOW
                        |
                        subprocess.CREATE_NEW_PROCESS_GROUP
                )

                startupinfo = subprocess.STARTUPINFO()

                startupinfo.dwFlags |= (
                    subprocess.STARTF_USESHOWWINDOW
                )

                startupinfo.wShowWindow = (
                    subprocess.SW_HIDE
                )

            # ====================================================
            # 7. LOG OPENVPN
            # ====================================================

            self.vpn_log_file = create_log_file()

            log_handle = open(
                self.vpn_log_file,
                "a",
                encoding="utf-8",
                errors="replace"
            )

            # ====================================================
            # 8. INICIAR OPENVPN
            # ====================================================

            self.after(
                0,
                lambda: self.set_progress(
                    35,
                    "Conectando à VPN..."
                )
            )

            self.after(
                0,
                lambda: self.log(
                    "🔌 Iniciando OpenVPN..."
                )
            )

            process = subprocess.Popen(
                command,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=creation_flags,
                startupinfo=startupinfo,
                cwd=str(profile.parent)
            )

            self.vpn_process = process

            # ====================================================
            # 9. AGUARDAR VPN
            # ====================================================

            self.after(
                0,
                lambda: self.log(
                    "⏳ Aguardando conexão VPN..."
                )
            )

            vpn_deadline = (
                    time.time()
                    +
                    WAIT_VPN_TIMEOUT
            )

            connection_confirmed = False

            while time.time() < vpn_deadline:

                if process.poll() is not None:
                    raise RuntimeError(
                        "OpenVPN encerrou antes de concluir a conexão.\n"
                        "Feche o programa e abra novamente..\n\n"
                        "Considere reiniciar o OpenVPN ou o Computador\n\n"
                    )

                try:

                    with open(
                            self.vpn_log_file,
                            "r",
                            encoding="utf-8",
                            errors="ignore"
                    ) as f:

                        log_content = f.read()

                except Exception:

                    log_content = ""

                if (
                        "Initialization Sequence Completed"
                        in log_content
                ):
                    connection_confirmed = True

                    break

                fatal_patterns = {
                    "Exiting due to fatal error": (
                        "Erro inesperado na conexão VPN.\n"
                        "O OpenVPN encontrou um problema e não conseguiu iniciar a conexão."
                    ),

                    "AUTH_FAILED": (
                        "Usuário ou senha incorretos.\n"
                        "Verifique suas credenciais da VPN e tente novamente."
                    ),

                    "TLS Error": (
                        "Não foi possível estabelecer comunicação segura com o servidor VPN.\n"
                        "Tente outro servidor ou perfil .ovpn."
                    ),

                    "Cannot open TUN/TAP": (
                        "O adaptador de rede da VPN não pôde ser iniciado.\n"
                        "Verifique a instalação do OpenVPN e tente novamente."
                    ),

                    "All TAP-Windows adapters": (
                        "Nenhum adaptador de rede VPN está disponível.\n"
                        "Reinstale ou repare o OpenVPN."
                    ),

                    "Options error:": (
                        "O perfil VPN possui uma configuração inválida ou incompatível.\n"
                        "Verifique o arquivo .ovpn selecionado."
                    ),

                    "Connection failed": (
                        "Não foi possível conectar ao servidor VPN.\n"
                        "O servidor pode estar indisponível ou o perfil pode estar com problema."
                    ),
                }

                fatal_error = None
                user_error = None

                for pattern, message in fatal_patterns.items():

                    if pattern.lower() in log_content.lower():
                        fatal_error = pattern
                        user_error = message

                        break

                if fatal_error:
                    raise RuntimeError(
                        user_error
                    )

                if fatal_error:
                    raise RuntimeError(
                        f"OpenVPN falhou: {fatal_error}"
                    )

                # progresso visual durante a conexão
                elapsed = (
                        WAIT_VPN_TIMEOUT
                        -
                        max(
                            0,
                            vpn_deadline - time.time()
                        )
                )

                progress = int(
                    35
                    +
                    (
                            elapsed
                            /
                            WAIT_VPN_TIMEOUT
                    )
                    *
                    20
                )

                self.after(
                    0,
                    lambda p=progress:
                    self.set_progress(
                        p,
                        "Estabelecendo túnel VPN..."
                    )
                )

                time.sleep(
                    0.25
                )

            if not connection_confirmed:
                raise RuntimeError(
                    "Tempo limite aguardando conexão VPN."
                )

            # ====================================================
            # 10. VPN CONECTADA
            # ====================================================

            vpn_connected = True

            self.after(
                0,
                lambda: self.set_progress(
                    55,
                    "VPN conectada."
                )
            )

            self.after(
                0,
                lambda: self.log(
                    "✅ OpenVPN conectado."
                )
            )

            # ====================================================
            # 11. CONFIRMAR IP
            # ====================================================

            self.after(
                0,
                lambda: self.set_progress(
                    60,
                    "Confirmando alteração de rede..."
                )
            )

            self.after(
                0,
                lambda: self.log(
                    "🌐 Confirmando alteração de rede..."
                )
            )

            new_ip = None

            ip_deadline = (
                    time.time()
                    +
                    IP_CHECK_TIMEOUT
            )

            while time.time() < ip_deadline:

                try:

                    new_ip = get_public_ip(
                        timeout=5
                    )

                except Exception:

                    new_ip = None

                if new_ip:

                    if (
                            not self.current_public_ip
                            or
                            new_ip != self.current_public_ip
                    ):
                        break

                time.sleep(
                    1
                )

            if new_ip:

                self.after(
                    0,
                    lambda ip=new_ip:
                    self.log(
                        f"🌐 IP atual: {ip}"
                    )
                )

                self.after(
                    0,
                    lambda: self.log(
                        "✅ Rede VPN confirmada."
                    )
                )

            else:

                self.after(
                    0,
                    lambda: self.log(
                        "⚠️ Não foi possível confirmar o IP externo."
                    )
                )

            # ====================================================
            # 12. ABRIR DISCORD
            # ====================================================

            self.after(
                0,
                lambda: self.set_progress(
                    70,
                    "Abrindo Discord..."
                )
            )

            self.after(
                0,
                lambda: self.log(
                    "💬 Abrindo Discord..."
                )
            )

            subprocess.Popen(
                [discord],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if os.name == "nt"
                    else 0
                )
            )

            # ====================================================
            # 13. CONFIRMAR DISCORD
            # ====================================================

            discord_deadline = (
                    time.time()
                    +
                    20
            )

            discord_found = False

            while time.time() < discord_deadline:

                if discord_process_running():
                    discord_found = True

                    break

                time.sleep(
                    0.5
                )

            if not discord_found:
                raise RuntimeError(
                    "Discord não iniciou corretamente."
                )

            self.after(
                0,
                lambda: self.set_progress(
                    75,
                    "Discord iniciado."
                )
            )

            self.after(
                0,
                lambda: self.log(
                    "✅ Discord aberto."
                )
            )

            # ====================================================
            # 14. MANTER VPN / ESTABILIZAR DISCORD
            # ====================================================

            self.after(
                0,
                lambda: self.log(
                    "⏳ Aguardando Discord estabilizar..."
                )
            )

            countdown_start = time.time()

            for remaining in range(
                    WAIT_DISCORD,
                    -1,
                    -1
            ):

                elapsed = int(
                    time.time() - countdown_start
                )

                # ------------------------------------------------
                # TRAZER OPENDIS PARA FRENTE
                # 40s / 20s / 0s restantes
                # ------------------------------------------------

                if remaining in {37, 29, 21, 14, 7, 4, 0}:
                    self.after(
                        0,
                        self.bring_to_front
                    )

                # ------------------------------------------------
                # LOG
                # ------------------------------------------------

                self.after(
                    0,
                    lambda s=remaining:
                    self.log(
                        f"⏳ Mantendo VPN por mais {s}s..."
                    )
                )

                # ------------------------------------------------
                # PROGRESSO
                # ------------------------------------------------

                elapsed = (
                        WAIT_DISCORD - remaining
                )

                progress = (
                        75
                        +
                        (
                                elapsed
                                /
                                WAIT_DISCORD
                        )
                        * 10
                )

                self.after(
                    0,
                    lambda p=progress:
                    self.set_progress(
                        p,
                        "Mantendo VPN..."
                    )
                )

                if remaining > 0:
                    time.sleep(1)

            # ====================================================
            # 14. DESCONECTAR VPN
            # ====================================================

            self.after(
                0,
                lambda: self.set_progress(
                    85,
                    "Desconectando VPN..."
                )
            )

            self.after(
                0,
                lambda: self.log(
                    "🔓 Desconectando VPN..."
                )
            )

            self.disconnect_vpn()

            vpn_connected = False

            # ====================================================
            # 15. CONFIRMAR DESCONEXÃO
            # ====================================================

            self.after(
                0,
                lambda: self.log(
                    "🔍 Confirmando desconexão..."
                )
            )

            time.sleep(3)

            if (
                    self.vpn_process
                    and
                    self.vpn_process.poll() is None
            ):
                self.after(
                    0,
                    lambda: self.log(
                        "⚠️ VPN ainda ativa. Forçando encerramento..."
                    )
                )

                self.disconnect_vpn()

            self.after(
                0,
                lambda: self.log(
                    "✅ VPN desconectada."
                )
            )



            # ====================================================
            # TRAZER OPENDIS PARA FRENTE
            # ====================================================

            self.after(
                0,
                self.bring_to_front
            )

            time.sleep(
                0.5
            )

            # ====================================================
            # ESTABILIZAÇÃO DO DISCORD
            # ====================================================

            self.after(
                0,
                lambda: self.start_btn.configure(
                    state="disabled",
                    text="🔄 ESTABILIZANDO DISCORD..."
                )
            )

            self.after(
                0,
                lambda: self.log(
                    "ℹ️ Seu Discord pode demorar um pouco para estabelecer a conexão novamente."
                )
            )

            self.after(
                0,
                lambda: self.log(
                    "⏳ Aguarde; se necessário, espere alguns instantes."
                )
            )

            # ====================================================
            # TEMPO EXTRA
            # ====================================================

            for elapsed in range(
                    DISCORD_STABILIZE_DELAY + 1
            ):

                remaining = (
                        DISCORD_STABILIZE_DELAY
                        -
                        elapsed
                )

                progress = int(
                    85
                    +
                    (
                            elapsed
                            /
                            DISCORD_STABILIZE_DELAY
                    )
                    *
                    15
                )

                # ------------------------------------------------
                # STATUS + PORCENTAGEM
                # ------------------------------------------------

                if remaining > 0:

                    status = (
                        f"Estabilizando a Conexão... {remaining}s"
                    )

                else:

                    status = (
                        "Discord estabilizado."
                    )

                self.after(
                    0,
                    lambda p=progress,
                           s=status:
                    self.set_progress(
                        p,
                        s
                    )
                )

                # ------------------------------------------------
                # LOG
                # ------------------------------------------------

                if remaining > 0:

                    self.after(
                        0,
                        lambda r=remaining:
                        self.log(
                            f"⏳ Estabilizando a Conexão... {r}s"
                        )
                    )

                else:

                    self.after(
                        0,
                        lambda:
                        self.log(
                            "✅ Discord estabilizado."
                        )
                    )

                    self.after(
                        0,
                        self.activity_bar.stop
                    )

                if remaining > 0:
                    time.sleep(
                        1
                    )

            # ====================================================
            # FINAL
            # ====================================================

            self.after(
                0,
                self.show_completed
            )


        except Exception as e:

            # ====================================================

            # ERRO → MANTER LOG PARA DIAGNÓSTICO

            # ====================================================

            keep_log_file = True

            error_text = str(e)

            self.after(

                0,

                lambda msg=error_text:

                self.log(

                    f"❌ {msg[:300]}"

                )

            )

            # ====================================================

            # SEMPRE LIMPAR VPN

            # ====================================================

            if (

                    vpn_connected

                    or

                    getattr(

                        self,

                        "vpn_process",

                        None

                    )

            ):

                self.after(

                    0,

                    lambda: self.log(

                        "🛑 Limpando conexão VPN..."

                    )

                )

                try:

                    self.disconnect_vpn()


                except Exception:

                    pass

            self.after(

                0,

                lambda msg=error_text:

                mb.showerror(

                    "OpenDis",

                    f"Ocorreu um erro:\n\n{msg[:1000]}"

                )

            )

            self.after(

                0,

                self.reset_start_button

            )


        finally:

            # ====================================================

            # FECHAR LOG

            # ====================================================

            try:

                if log_handle:
                    log_handle.flush()

                    log_handle.close()


            except Exception:

                pass

            # ====================================================

            # APAGAR LOG SE NÃO HOUVE ERRO

            # ====================================================

            if (

                    not keep_log_file

                    and

                    self.vpn_log_file

            ):

                try:

                    self.vpn_log_file.unlink(

                        missing_ok=True

                    )


                except Exception:

                    pass

            # ====================================================

            # APAGAR CREDENCIAL TEMPORÁRIA

            # ====================================================

            if credentials_file:

                try:

                    credentials_file.unlink(

                        missing_ok=True

                    )


                except Exception:

                    pass

                credentials_file = None


    # ========================================================
    # DESCONECTAR VPN
    # ========================================================

    def disconnect_vpn(self):

        process = getattr(
            self,
            "vpn_process",
            None
        )

        if not process:
            return True

        # ========================================================
        # JÁ ENCERRADO
        # ========================================================

        if process.poll() is not None:

            try:
                process.wait(timeout=2)
            except Exception:
                pass

            if getattr(
                    self,
                    "vpn_process",
                    None
            ) is process:
                self.vpn_process = None

            return True

        # ========================================================
        # WINDOWS
        # ========================================================

        if os.name == "nt":

            try:

                process.send_signal(
                    signal.CTRL_BREAK_EVENT
                )

            except Exception:

                pass


        else:

            try:

                process.terminate()

            except Exception:

                pass

        # ========================================================
        # AGUARDAR ENCERRAMENTO NORMAL
        # ========================================================

        deadline = (
                time.time() + 10
        )

        while time.time() < deadline:

            if process.poll() is not None:
                break

            time.sleep(0.25)

        # ========================================================
        # SEGUNDO ESTÁGIO
        # ========================================================

        if process.poll() is None:

            try:

                process.terminate()

            except Exception:

                pass

            try:

                process.wait(
                    timeout=5
                )

            except subprocess.TimeoutExpired:

                pass

        # ========================================================
        # ÚLTIMO RECURSO
        # ========================================================

        if process.poll() is None:

            try:

                process.kill()

            except Exception:

                pass

            try:

                process.wait(
                    timeout=5
                )

            except Exception:

                pass

        # ========================================================
        # RESULTADO
        # ========================================================

        disconnected = (
                process.poll() is not None
        )

        if getattr(
                self,
                "vpn_process",
                None
        ) is process:
            self.vpn_process = None

        return disconnected


    # ========================================================
    # FINAL
    # ========================================================

    def show_completed(self):

        self.set_progress(
            100,
            "Discord estabilizado. Tudo pronto!"
        )

        self.log(
            "🎉 Operação concluída com sucesso!"
        )

        self.final_status.configure(
            text="✅ Discord Aberto!",
            text_color="#57F287"
        )

        self.start_btn.configure(
            state="normal",
            text="✓ CONCLUIR E FECHAR",
            fg_color="#3ba55d",
            hover_color="#2d7d46",
            command=self.destroy
        )


    # ========================================================
    # RESET
    # ========================================================

    def reset_start_button(self):

        try:

            self.start_btn.configure(
                state="normal",
                text="⚡ INICIAR",
                fg_color="#5865F2",
                hover_color="#4752C4",
                command=self.run_unlock
            )

        except Exception:
            pass


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # GARANTIR ADMIN ANTES DA GUI
    # ========================================================

    if os.name == "nt" and not is_running_as_admin():

        if not restart_as_admin():

            mb.showerror(
                "OpenDis",
                (
                    "O OpenDis precisa de privilégios "
                    "administrativos para funcionar.\n\n"
                    "A elevação foi cancelada ou falhou."
                )
            )

            sys.exit(1)


        sys.exit(0)

    app = OpenDisApp()

    app.mainloop()