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
import shutil
import zipfile
import hashlib
import tempfile
from pathlib import Path
from ctypes import wintypes
from html import unescape
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

import customtkinter as ctk
import tkinter.messagebox as mb
from tkinter import filedialog


# ============================================================
# CONFIGURAÇÃO
# ============================================================

APP_NAME = "OpenDis"
APP_VERSION = "2.0.0"
WAIT_VPN_TIMEOUT = 60
WAIT_DISCORD = 15
WAIT_OPENDIS_FOCUS = 15
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
# DISCORD / APP VPN
# ============================================================


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


# ============================================================
# CREDENCIAIS SALVAS
# ============================================================


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

# ============================================================
# LOG
# ============================================================

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

    short_server = server.split(".", 1)[0]

    candidates = [
        f"*{server}*{protocol}*.ovpn",
        f"*{short_server}*{protocol}*.ovpn",
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

# ============================================================
# PING
# ============================================================

def ping_vpn_server(server, timeout=1000):
    """
    Mede o ping atual do servidor VPNBook usando ICMP.

    Retorna:
        int  -> ping em ms
        None -> servidor sem resposta
    """

    if os.name != "nt":
        return None

    try:
        result = subprocess.run(
            [
                "ping",
                "-n",
                "1",
                "-w",
                str(timeout),
                server
            ],
            capture_output=True,
            text=True,
            timeout=(timeout / 1000) + 2,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            return None

        output = result.stdout

        match = re.search(
            r"(?:tempo|time)[=<]\s*(\d+)\s*ms",
            output,
            re.IGNORECASE
        )

        if not match:
            match = re.search(
                r"(\d+)\s*ms",
                output,
                re.IGNORECASE
            )

        if not match:
            return None

        return int(match.group(1))

    except Exception:
        return None

def ping_status(ping):
    """
    Retorna:
        bolinha
        cor
    """

    if ping is None:
        return "●", "#ed4245"

    if ping <= 300:
        return "●", "#57F287"

    if ping <= 500:
        return "●", "#FFA500"

    return "●", "#ED4245"


# ============================================================
# DISCORD - PROCESSOS
# ============================================================

def get_discord_pids():
    """
    Retorna todos os PIDs atualmente pertencentes ao Discord.exe.

    Usa o PowerShell nativo do Windows para obter os processos.
    Não depende de biblioteca externa.

    Retorno:
        list[int]
    """

    if os.name != "nt":
        return []

    try:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            (
                "Get-Process -Name Discord -ErrorAction SilentlyContinue "
                "| Select-Object -ExpandProperty Id"
            )
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            return []

        pids = set()

        for line in (
            result.stdout or ""
        ).splitlines():

            line = line.strip()

            if not line:
                continue

            try:
                pid = int(line)

                if pid > 0:
                    pids.add(pid)

            except ValueError:
                continue

        return sorted(pids)

    except Exception:
        return []


def discord_process_running():
    """
    Retorna True quando existir pelo menos um Discord.exe ativo.
    """

    return bool(
        get_discord_pids()
    )


def get_process_name(pid):
    """
    Retorna o nome do executável de um PID.

    Retorna None se o processo não existir
    ou não puder ser consultado.
    """

    if os.name != "nt":
        return None

    try:

        command = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            (
                f"(Get-Process -Id {int(pid)} "
                f"-ErrorAction SilentlyContinue).ProcessName"
            )
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        name = (
            result.stdout or ""
        ).strip()

        if not name:
            return None

        return f"{name}.exe"

    except Exception:
        return None


# ============================================================
# DISCORD APP-VPN
# ============================================================

SINGBOX_VERSION = "1.14.0"

SINGBOX_DIR = (
    Path(os.environ.get("APPDATA", str(BASE_DIR)))
    / APP_NAME
    / "sing-box"
)

SINGBOX_EXECUTABLE = (
    SINGBOX_DIR
    / "sing-box.exe"
)

SINGBOX_CONFIG_FILE = (
    SINGBOX_DIR
    / "opendis-discord.json"
)

SINGBOX_LOG_FILE = (
    LOG_DIR
    / "sing-box.log"
)

def find_singbox_executable():
    """
    Localiza o sing-box utilizado pelo App-VPN.

    Ordem:
        1. instalação privada do OpenDis
        2. diretório do OpenDis
        3. PATH
    """

    candidates = [
        SINGBOX_EXECUTABLE,
        BASE_DIR / "sing-box.exe",
        BASE_DIR / "bin" / "sing-box.exe",
        BASE_DIR / "tools" / "sing-box.exe",
    ]

    for candidate in candidates:

        try:

            candidate = Path(candidate)

            if (
                candidate.exists()
                and
                candidate.is_file()
            ):
                return candidate.resolve()

        except Exception:
            continue

    path = shutil.which(
        "sing-box.exe"
    )

    if path:

        return Path(
            path
        ).resolve()

    return None


def install_singbox():
    """
    Instala uma cópia privada do sing-box 1.14.0
    dentro do AppData do OpenDis.

    Não altera PATH.
    Não instala serviço.
    Não abre CMD.
    """

    if os.name != "nt":

        raise RuntimeError(
            "O App-VPN do OpenDis suporta somente Windows."
        )

    existing = find_singbox_executable()

    if existing:
        return existing

    SINGBOX_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    architecture = (
        os.environ
        .get(
            "PROCESSOR_ARCHITECTURE",
            "AMD64"
        )
        .upper()
    )

    if architecture in {
        "ARM64",
    }:

        asset_arch = "arm64"

    else:

        asset_arch = "amd64"

    filename = (
        f"sing-box-"
        f"{SINGBOX_VERSION}-"
        f"windows-"
        f"{asset_arch}.zip"
    )

    url = (
        "https://github.com/"
        "SagerNet/sing-box/releases/download/"
        f"v{SINGBOX_VERSION}/"
        f"{filename}"
    )

    temp_zip = (
        Path(tempfile.gettempdir())
        /
        f"OpenDis_singbox_{os.getpid()}.zip"
    )

    extract_dir = (
        Path(tempfile.gettempdir())
        /
        f"OpenDis_singbox_{os.getpid()}"
    )

    try:

        temp_zip.unlink(
            missing_ok=True
        )

    except Exception:
        pass

    try:

        if extract_dir.exists():

            shutil.rmtree(
                extract_dir,
                ignore_errors=True
            )

    except Exception:
        pass

    try:

        request = Request(
            url,
            headers={
                "User-Agent":
                    f"{APP_NAME}/{APP_VERSION}"
            }
        )

        with urlopen(
            request,
            timeout=60
        ) as response:

            with open(
                temp_zip,
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

        if (
            not temp_zip.exists()
            or
            temp_zip.stat().st_size < 1000000
        ):

            raise RuntimeError(
                "O arquivo do sing-box baixado "
                "parece inválido."
            )

        extract_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        with zipfile.ZipFile(
            temp_zip,
            "r"
        ) as archive:

            archive.extractall(
                extract_dir
            )

        found = None

        for root, dirs, files in os.walk(
            extract_dir
        ):

            for filename_found in files:

                if (
                    filename_found.lower()
                    ==
                    "sing-box.exe"
                ):

                    found = (
                        Path(root)
                        /
                        filename_found
                    )

                    break

            if found:
                break

        if not found:
            raise RuntimeError(
                "sing-box.exe não foi encontrado "
                "dentro do pacote oficial."
            )

        SINGBOX_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copy2(
            found,
            SINGBOX_EXECUTABLE
        )

        if not SINGBOX_EXECUTABLE.exists():

            raise RuntimeError(
                "Não foi possível instalar sing-box.exe."
            )

        return SINGBOX_EXECUTABLE.resolve()

    finally:

        try:

            temp_zip.unlink(
                missing_ok=True
            )

        except Exception:
            pass

        try:

            if extract_dir.exists():

                shutil.rmtree(
                    extract_dir,
                    ignore_errors=True
                )

        except Exception:
            pass


def ensure_singbox_ready():
    """
    Garante que o sing-box esteja instalado e utilizável
    ANTES de o OpenVPN alterar qualquer estado de rede.

    Retorna:
        Path -> sing-box.exe válido
    """

    singbox = find_singbox_executable()

    if not singbox:
        singbox = install_singbox()

    if not singbox:
        raise RuntimeError(
            "Não foi possível preparar o componente App-VPN."
        )

    singbox = Path(singbox).resolve()

    if not singbox.exists():
        raise RuntimeError(
            f"sing-box.exe não foi encontrado:\n{singbox}"
        )

    try:

        result = subprocess.run(
            [
                str(singbox),
                "version"
            ],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            )
        )

    except Exception as e:

        raise RuntimeError(
            "Não foi possível executar sing-box.exe.\n\n"
            f"{e}"
        )

    version_text = (
        result.stdout
        or
        result.stderr
        or
        ""
    )

    match = re.search(
        r"sing-box version\s+"
        r"(\d+)\.(\d+)\.(\d+)",
        version_text,
        re.IGNORECASE
    )

    if not match:

        raise RuntimeError(
            "Não foi possível identificar "
            "a versão do sing-box."
        )

    version_tuple = (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
    )

    if version_tuple < (1, 14, 0):

        raise RuntimeError(
            "O OpenDis precisa de sing-box "
            "1.14.0 ou superior."
        )

    return singbox


def get_public_ip_retry(
    timeout=8,
    attempts=5,
    delay=1.0
):
    """
    Obtém o IP público com novas tentativas.

    É usado nas verificações fail-closed do split tunnel:
    se o IP não puder ser confirmado, o OpenDis não declara
    isolamento como seguro.
    """

    attempts = max(
        1,
        int(attempts)
    )

    for attempt in range(
        attempts
    ):

        ip = get_public_ip(
            timeout=timeout
        )

        if ip:
            return ip

        if (
            attempt
            <
            attempts - 1
        ):
            time.sleep(
                max(
                    0.1,
                    float(delay)
                )
            )

    return None


def get_windows_network_adapters():
    """
    Retorna adaptadores ativos do Windows.

    Resultado:

        [
            {
                "name": "...",
                "description": "...",
                "if_index": 12
            }
        ]
    """

    if os.name != "nt":
        return []

    powershell = (
        "$items = Get-NetAdapter "
        "-ErrorAction SilentlyContinue | "
        "Where-Object { $_.Status -eq 'Up' } | "
        "Select-Object "
        "Name, InterfaceDescription, ifIndex; "
        "$items | ConvertTo-Json -Compress"
    )

    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            powershell
        ],
        capture_output=True,
        text=True,
        timeout=15,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    if result.returncode != 0:
        return []

    text = (
        result.stdout
        or ""
    ).strip()

    if not text:
        return []

    try:

        data = json.loads(
            text
        )

    except Exception:

        return []

    if isinstance(
        data,
        dict
    ):
        data = [data]

    adapters = []

    for item in data:

        if not isinstance(
            item,
            dict
        ):
            continue

        name = str(
            item.get(
                "Name",
                ""
            )
        ).strip()

        description = str(
            item.get(
                "InterfaceDescription",
                ""
            )
        ).strip()

        try:

            if_index = int(
                item.get(
                    "ifIndex"
                )
            )

        except Exception:

            continue

        adapters.append(
            {
                "name": name,
                "description": description,
                "if_index": if_index,
            }
        )

    return adapters


def find_openvpn_adapter(
    exclude_if_indexes=None
):
    """
    Localiza a interface ativa pertencente ao OpenVPN.

    Estratégia:
        1. procura interfaces VPN ativas;
        2. se houver snapshot anterior ao OpenVPN,
           prefere interfaces que NÃO existiam/estavam ativas antes;
        3. usa nome/descrição como fallback.

    exclude_if_indexes:
        conjunto/lista de ifIndex capturados antes de iniciar
        o OpenVPN.
    """

    adapters = get_windows_network_adapters()

    excluded = set()

    if exclude_if_indexes:

        for value in exclude_if_indexes:

            try:
                excluded.add(
                    int(value)
                )
            except Exception:
                continue

    keywords = (
        "openvpn",
        "tap-windows",
        "tap windows",
        "wintun",
        "ovpn",
    )

    matches = []

    for adapter in adapters:

        searchable = (
            adapter["name"]
            +
            " "
            +
            adapter["description"]
        ).lower()

        # Nunca confundir o TUN criado pelo próprio OpenDis.
        if (
            "opendis" in searchable
            or
            "sing-box" in searchable
        ):
            continue

        if not any(
            keyword in searchable
            for keyword in keywords
        ):
            continue

        matches.append(
            adapter
        )

    if not matches:
        return None

    def sort_key(item):

        searchable = (
            item["name"]
            +
            " "
            +
            item["description"]
        ).lower()

        is_new = (
            item["if_index"]
            not in excluded
        )

        explicit_openvpn = (
            "openvpn" in searchable
            or
            "ovpn" in searchable
        )

        return (
            0 if is_new else 1,
            0 if explicit_openvpn else 1,
            item["if_index"],
        )

    matches.sort(
        key=sort_key
    )

    return matches[0]

def get_adapter_ipv4(
    if_index
):
    """
    Obtém IPv4 unicast da interface.
    """

    if os.name != "nt":
        return None

    try:

        command = (
            "Get-NetIPAddress "
            f"-InterfaceIndex {int(if_index)} "
            "-AddressFamily IPv4 "
            "-AddressState Preferred "
            "-ErrorAction SilentlyContinue | "
            "Where-Object { "
            "$_.IPAddress -notlike '169.254.*' "
            "} | "
            "Select-Object -First 1 "
            "-ExpandProperty IPAddress"
        )

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command
            ],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        value = (
            result.stdout
            or ""
        ).strip()

        if value:
            return value.splitlines()[0].strip()

    except Exception:
        pass

    return None



def get_windows_default_ipv4_routes():
    """
    Retorna as rotas default IPv4 ativas do Windows com as métricas
    efetivas de interface.

    É usado para preservar exatamente a WAN existente antes de abrir
    um perfil .ovpn manual.
    """

    if os.name != "nt":
        return []

    command = (
        "$ifMetrics = @{}; "
        "Get-NetIPInterface -AddressFamily IPv4 -ErrorAction SilentlyContinue | "
        "ForEach-Object { $ifMetrics[[int]$_.InterfaceIndex] = [int]$_.InterfaceMetric }; "
        "$routes = Get-NetRoute -AddressFamily IPv4 "
        "-DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | "
        "Where-Object { $_.State -ne 'Invalid' } | "
        "ForEach-Object { "
        "$im = 0; if ($ifMetrics.ContainsKey([int]$_.InterfaceIndex)) { "
        "$im = $ifMetrics[[int]$_.InterfaceIndex] }; "
        "[PSCustomObject]@{ "
        "DestinationPrefix = [string]$_.DestinationPrefix; "
        "InterfaceIndex = [int]$_.InterfaceIndex; "
        "NextHop = [string]$_.NextHop; "
        "RouteMetric = [int]$_.RouteMetric; "
        "InterfaceMetric = [int]$im; "
        "TotalMetric = ([int]$_.RouteMetric + [int]$im) "
        "} }; "
        "$routes | Sort-Object TotalMetric | ConvertTo-Json -Compress"
    )

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=12,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        text = (result.stdout or "").strip()

        if not text:
            return []

        data = json.loads(text)

        if isinstance(data, dict):
            data = [data]

        routes = []

        for item in data:
            if not isinstance(item, dict):
                continue

            try:
                routes.append(
                    {
                        "destination": str(
                            item.get("DestinationPrefix", "0.0.0.0/0")
                        ),
                        "if_index": int(item.get("InterfaceIndex")),
                        "next_hop": str(item.get("NextHop", "")).strip(),
                        "route_metric": int(item.get("RouteMetric", 0)),
                        "interface_metric": int(item.get("InterfaceMetric", 0)),
                        "total_metric": int(item.get("TotalMetric", 0)),
                    }
                )
            except Exception:
                continue

        return routes

    except Exception:
        return []


def restore_manual_wan_routing(
    wan_adapter,
    baseline_default_routes,
    vpn_adapter
):
    """
    Fail-safe do caminho .ovpn manual.

    O OpenVPN manual NÃO deve alterar a rota global do Windows.

    O perfil manual mantém UMA rota default controlada na interface
    VPN com métrica muito alta (>= 4000). Essa rota existe somente
    para dar ao bridge L3 do sing-box um caminho de egress pela
    interface OpenVPN. Como a WAN normal possui métrica muito menor,
    ela continua sendo a rota preferida do Windows para o computador.

    Esta função remove:
        - qualquer def1 0.0.0.0/1 e 128.0.0.0/1 da VPN;
        - qualquer default /0 da VPN com métrica baixa.

    Também garante que a rota default original da WAN continue
    presente no ActiveStore.

    Não altera o fluxo VPNBook.
    """

    if os.name != "nt":
        return True, ""

    try:
        wan_if_index = int(
            wan_adapter.get("if_index")
        )
        vpn_if_index = int(
            vpn_adapter.get("if_index")
        )
    except Exception:
        return False, "Interface WAN/VPN inválida."

    baseline_route = None

    for route in baseline_default_routes or []:
        try:
            if int(route.get("if_index")) == wan_if_index:
                baseline_route = dict(route)
                break
        except Exception:
            continue

    # Se o snapshot não trouxe a rota, não inventamos gateway.
    # Ainda assim removemos qualquer default/def1 da VPN.
    next_hop = ""
    route_metric = 0

    if baseline_route:
        next_hop = str(
            baseline_route.get("next_hop", "")
        ).strip()
        try:
            route_metric = int(
                baseline_route.get("route_metric", 0)
            )
        except Exception:
            route_metric = 0

    powershell = (
        f"$vpnIf = {vpn_if_index}; "
        f"$wanIf = {wan_if_index}; "

        # redirect-gateway def1 sempre vence uma rota /0 pela
        # especificidade do prefixo, independentemente da métrica.
        # Portanto qualquer /1 na interface VPN deve desaparecer.
        "$def1 = @('0.0.0.0/1','128.0.0.0/1'); "
        "foreach ($prefix in $def1) { "
        "Get-NetRoute -AddressFamily IPv4 -InterfaceIndex $vpnIf "
        "-DestinationPrefix $prefix -ErrorAction SilentlyContinue | "
        "Remove-NetRoute -Confirm:$false -ErrorAction SilentlyContinue; "
        "}; "

        # Uma única /0 de métrica MUITO alta é intencional. Ela dá
        # ao bridge do sing-box um next-hop pela VPN, porém não pode
        # vencer a WAN normal. Defaults VPN de métrica baixa são
        # tratadas como inseguras e removidas.
        "Get-NetRoute -AddressFamily IPv4 -InterfaceIndex $vpnIf "
        "-DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | "
        "Where-Object { [int]$_.RouteMetric -lt 4000 } | "
        "Remove-NetRoute -Confirm:$false -ErrorAction SilentlyContinue; "
    )

    if next_hop and next_hop != "0.0.0.0":
        safe_next_hop = next_hop.replace("'", "''")
        powershell += (
            f"$gw = '{safe_next_hop}'; "
            "$existing = Get-NetRoute -AddressFamily IPv4 "
            "-DestinationPrefix '0.0.0.0/0' -InterfaceIndex $wanIf "
            "-ErrorAction SilentlyContinue | "
            "Where-Object { [string]$_.NextHop -eq $gw } | "
            "Select-Object -First 1; "
            "if ($null -eq $existing) { "
            "New-NetRoute -AddressFamily IPv4 "
            "-DestinationPrefix '0.0.0.0/0' "
            "-InterfaceIndex $wanIf "
            "-NextHop $gw "
            f"-RouteMetric {max(route_metric, 0)} "
            "-PolicyStore ActiveStore "
            "-ErrorAction SilentlyContinue | Out-Null; "
            "}; "
        )

    powershell += "Clear-DnsClientCache -ErrorAction SilentlyContinue; exit 0"

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                powershell,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            return False, (
                result.stderr.strip()
                or "Falha ao restaurar a rota WAN."
            )

        return True, ""

    except Exception as e:
        return False, str(e)


def get_default_ipv4_adapter():
    """
    Descobre a interface física/normal que o Windows está usando
    para sair para a Internet ANTES do OpenVPN e do OpenDisTun.

    A estratégia usa a rota que o próprio Windows escolheria para
    1.1.1.1, sem enviar dados, e depois mapeia o IPv4 local para o
    adaptador correspondente.

    Retorna:
        {
            "name": "Ethernet" / "Wi-Fi" / ...,
            "description": "...",
            "if_index": 12,
            "ipv4": "192.168.1.20"
        }
    """

    if os.name != "nt":
        return None

    local_ip = None
    probe = None

    try:
        probe = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )
        probe.settimeout(2)
        probe.connect(
            ("1.1.1.1", 53)
        )
        local_ip = probe.getsockname()[0]

    except Exception:
        local_ip = None

    finally:
        try:
            if probe:
                probe.close()
        except Exception:
            pass

    if not local_ip:
        return None

    safe_ip = re.sub(
        r"[^0-9.]",
        "",
        local_ip
    )

    if not safe_ip:
        return None

    command = (
        f"$ip = Get-NetIPAddress "
        f"-AddressFamily IPv4 "
        f"-IPAddress '{safe_ip}' "
        f"-ErrorAction SilentlyContinue | "
        f"Select-Object -First 1; "
        f"if ($null -ne $ip) {{ "
        f"Get-NetAdapter -InterfaceIndex $ip.InterfaceIndex "
        f"-ErrorAction SilentlyContinue | "
        f"Select-Object Name,InterfaceDescription,ifIndex | "
        f"ConvertTo-Json -Compress "
        f"}}"
    )

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        text = (
            result.stdout
            or ""
        ).strip()

        if not text:
            return None

        data = json.loads(text)

        return {
            "name": str(
                data.get("Name", "")
            ).strip(),
            "description": str(
                data.get(
                    "InterfaceDescription",
                    ""
                )
            ).strip(),
            "if_index": int(
                data.get("ifIndex")
            ),
            "ipv4": local_ip,
        }

    except Exception:
        return None


def get_discord_established_connections(pids):
    """
    Retorna conexões TCP estabelecidas pertencentes aos processos
    Discord informados.

    É usado como verificação funcional: além de o processo existir,
    o Discord precisa conseguir estabelecer ao menos uma conexão.
    """

    if os.name != "nt" or not pids:
        return []

    clean_pids = []

    for pid in pids:
        try:
            value = int(pid)
            if value > 0:
                clean_pids.append(value)
        except Exception:
            continue

    if not clean_pids:
        return []

    pid_list = ",".join(
        str(pid)
        for pid in sorted(set(clean_pids))
    )

    command = (
        f"$ids = @({pid_list}); "
        f"$c = Get-NetTCPConnection "
        f"-State Established "
        f"-ErrorAction SilentlyContinue | "
        f"Where-Object {{ $ids -contains $_.OwningProcess }} | "
        f"Select-Object -First 20 "
        f"OwningProcess,RemoteAddress,RemotePort; "
        f"$c | ConvertTo-Json -Compress"
    )

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        text = (
            result.stdout
            or ""
        ).strip()

        if not text:
            return []

        data = json.loads(text)

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            return []

        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    except Exception:
        return []


def flush_windows_dns_cache():
    """
    Limpa o cache DNS do Windows silenciosamente.
    """

    if os.name != "nt":
        return True

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "Clear-DnsClientCache",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return result.returncode == 0

    except Exception:
        return False


def wait_for_adapter_to_disappear(
    adapter_name,
    timeout=8
):
    """
    Aguarda um adaptador virtual deixar de existir.
    """

    if os.name != "nt":
        return True

    deadline = time.time() + max(
        1,
        float(timeout)
    )

    safe_name = str(adapter_name).replace(
        "'",
        "''"
    )

    while time.time() < deadline:

        try:
            command = (
                f"$a = Get-NetAdapter "
                f"-Name '{safe_name}' "
                f"-ErrorAction SilentlyContinue; "
                f"if ($null -eq $a) {{ exit 0 }} "
                f"else {{ exit 1 }}"
            )

            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode == 0:
                return True

        except Exception:
            pass

        time.sleep(0.25)

    return False


def is_windows_adapter_active(
    adapter_name
):
    """
    Retorna True somente quando o adaptador informado existe E está Up.

    Um Wintun pode continuar aparecendo por alguns segundos no
    Get-NetAdapter depois que o processo responsável já terminou.
    Esse estado transitório não significa que o túnel continua ativo.
    """

    if os.name != "nt":
        return False

    safe_name = str(adapter_name).replace(
        "'",
        "''"
    )

    command = (
        f"$a = Get-NetAdapter "
        f"-Name '{safe_name}' "
        f"-ErrorAction SilentlyContinue; "
        f"if ($null -eq $a) {{ exit 1 }}; "
        f"if ($a.Status -eq 'Up') {{ exit 0 }} else {{ exit 1 }}"
    )

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return result.returncode == 0

    except Exception:
        return False


def remove_opendis_tun_fallback():
    """
    Fallback somente para a interface criada pelo próprio OpenDis.

    É usado apenas quando o sing-box já terminou e o adaptador
    OpenDisTun ficou órfão. Nunca toca em TAP-Windows6/OpenVPN.
    """

    if os.name != "nt":
        return True

    command = (
        "$a = Get-NetAdapter -Name 'OpenDisTun' "
        "-ErrorAction SilentlyContinue; "
        "if ($null -eq $a) { exit 0 }; "
        "$desc = [string]$a.InterfaceDescription; "
        "if ($desc -notmatch 'Wintun|sing-tun') { exit 2 }; "
        "$id = [string]$a.PnPDeviceID; "
        "if ([string]::IsNullOrWhiteSpace($id)) { exit 3 }; "
        "& pnputil.exe /remove-device $id | Out-Null; "
        "exit $LASTEXITCODE"
    )

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode not in (0, 1):
            return False

        removed = wait_for_adapter_to_disappear(
            "OpenDisTun",
            timeout=6
        )

        if removed:
            return True

        # O dispositivo pode continuar listado por alguns instantes,
        # porém já estar Down. Nesse caso o túnel não está mais ativo
        # e não devemos gerar um falso positivo de falha.
        return not is_windows_adapter_active(
            "OpenDisTun"
        )

    except Exception:
        return False



class DiscordVPNEngine:
    """
    Engine App-VPN real do OpenDis.

    Arquitetura:

        OpenVPN
            |
            | route-nopull
            |
            +--> interface VPN disponível,
                 mas NÃO default-route

        sing-box TUN
            |
            +--> Discord.exe
            |        |
            |        +--> bridge
            |              |
            |              +--> interface OpenVPN
            |
            +--> qualquer outro processo
                     |
                     +--> direct
                           |
                           +--> WAN normal

    Resultado pretendido:

        Discord -> VPN
        restante -> Internet normal
    """

    DISCORD_PROCESS_NAMES = [
        "Discord.exe",
        "DiscordPTB.exe",
        "DiscordCanary.exe",
    ]

    def __init__(self):

        self.openvpn_process = None
        self.profile = None

        self.discord_pids = set()

        self.running = False
        self.prepared = False

        self._lock = threading.RLock()
        self._process = None
        self._log_handle = None

        self._vpn_adapter = None
        self._wan_adapter = None
        self._singbox = None

        self._config_file = SINGBOX_CONFIG_FILE


    # ==========================================================
    # LOG
    # ==========================================================

    def _log(
        self,
        message
    ):

        try:
            print(message)
        except Exception:
            pass

    # ==========================================================
    # PREPARAR
    # ==========================================================

    def prepare(
        self,
        openvpn_process=None,
        profile=None,
        baseline_if_indexes=None,
        wan_adapter=None
    ):
        """
        Inicia o App-VPN depois que o OpenVPN estabeleceu o túnel.

        Princípios:
            - OpenVPN não vira rota padrão do Windows;
            - OpenDisTun recebe o tráfego do sistema;
            - Discord.exe é encaminhado em L3 para a interface OpenVPN;
            - o restante sai pela interface WAN que já era padrão antes
              da operação;
            - DNS continua sendo o DNS normal do Windows/WAN.
        """

        if os.name != "nt":
            raise RuntimeError(
                "O App-VPN funciona somente no Windows."
            )

        if not is_running_as_admin():
            raise RuntimeError(
                "O OpenDis precisa estar executando como Administrador."
            )

        if (
            openvpn_process is None
            or
            openvpn_process.poll() is not None
        ):
            raise RuntimeError(
                "O OpenVPN não está conectado."
            )

        self.cleanup(
            silent=True
        )

        self.openvpn_process = openvpn_process
        self.profile = profile

        # ------------------------------------------------------
        # SING-BOX
        # ------------------------------------------------------

        self._singbox = ensure_singbox_ready()

        version_result = subprocess.run(
            [
                str(self._singbox),
                "version"
            ],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        version_text = (
            version_result.stdout
            or
            version_result.stderr
            or
            ""
        )

        match = re.search(
            r"sing-box version\s+"
            r"(\d+)\.(\d+)\.(\d+)",
            version_text,
            re.IGNORECASE
        )

        if not match:
            raise RuntimeError(
                "Não foi possível identificar a versão do sing-box."
            )

        version_tuple = (
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
        )

        if version_tuple < (1, 14, 0):
            raise RuntimeError(
                "O OpenDis precisa de sing-box 1.14.0 ou superior."
            )

        if "with_gvisor" not in version_text.lower():
            raise RuntimeError(
                "O sing-box encontrado não possui suporte gVisor.\n\n"
                "Use o binário oficial do sing-box para Windows."
            )

        # ------------------------------------------------------
        # WAN ORIGINAL
        # ------------------------------------------------------

        if not wan_adapter:
            wan_adapter = get_default_ipv4_adapter()

        if not wan_adapter:
            raise RuntimeError(
                "Não foi possível identificar a interface WAN original."
            )

        wan_name = str(
            wan_adapter.get(
                "name",
                ""
            )
        ).strip()

        if not wan_name:
            raise RuntimeError(
                "A interface WAN original não possui nome válido."
            )

        self._wan_adapter = dict(wan_adapter)

        self._log(
            f"🌐 WAN preservada: {wan_name}"
        )

        if wan_adapter.get("ipv4"):
            self._log(
                f"🌐 IPv4 WAN local: {wan_adapter['ipv4']}"
            )

        # ------------------------------------------------------
        # INTERFACE OPENVPN
        # ------------------------------------------------------

        adapter = None
        deadline = time.time() + 20

        while time.time() < deadline:

            adapter = find_openvpn_adapter(
                exclude_if_indexes=baseline_if_indexes
            )

            if adapter:
                ipv4 = get_adapter_ipv4(
                    adapter["if_index"]
                )

                if ipv4:
                    adapter["ipv4"] = ipv4
                    break

            time.sleep(0.5)

        if not adapter:
            raise RuntimeError(
                "Não foi possível localizar a interface OpenVPN ativa."
            )

        if not adapter.get("ipv4"):
            raise RuntimeError(
                "A interface OpenVPN não possui um IPv4 válido."
            )

        self._vpn_adapter = adapter

        self._log(
            "🛡️ Interface OpenVPN encontrada: "
            f"{adapter['name']}"
        )
        self._log(
            f"🛡️ ifIndex OpenVPN: {adapter['if_index']}"
        )
        self._log(
            f"🛡️ IPv4 OpenVPN: {adapter['ipv4']}"
        )

        # ------------------------------------------------------
        # CONFIGURAÇÃO
        # ------------------------------------------------------

        self._config_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        tun_cidr = "172.29.87.0/30"

        config = {
            "log": {
                "disabled": False,
                "level": "info",
                "timestamp": True,
            },

            "inbounds": [
                {
                    "type": "tun",
                    "tag": "opendis-tun",
                    "interface_name": "OpenDisTun",
                    "address": [
                        "172.29.87.1/30"
                    ],
                    "mtu": 1400,

                    # Não assumir nem bloquear o DNS do Windows.
                    "dns_mode": "disabled",

                    "auto_route": True,

                    # No Windows strict_route também instala filtros
                    # WFP para DNS. Como o OpenDis usa o DNS normal da
                    # WAN, deve ficar desligado.
                    "strict_route": False,

                    # Evita o problema do stack system no Windows em
                    # que conexões aparecem no log, mas não retornam
                    # dados ao aplicativo.
                    "stack": "gvisor",
                }
            ],

            "outbounds": [
                {
                    "type": "direct",
                    "tag": "wan-direct",

                    # Prende conexões normais explicitamente à placa
                    # que era a WAN antes do OpenDisTun existir.
                    "bind_interface": wan_name,
                },
                {
                    "type": "bridge",
                    "tag": "discord-vpn",
                    "interface": adapter["name"],
                },
            ],

            "route": {
                "default_interface": wan_name,

                "rules": [
                    # Evita o conhecido self-loop do TUN no Windows.
                    {
                        "ip_cidr": [
                            tun_cidr
                        ],
                        "action": "reject",
                        "method": "drop",
                    },

                    # Endereços locais continuam na rede normal.
                    {
                        "ip_is_private": True,
                        "action": "route",
                        "outbound": "wan-direct",
                    },

                    # O OpenVPN selecionado neste fluxo é IPv4.
                    # Bloquear IPv6 do Discord evita bypass pela WAN.
                    {
                        "process_name": self.DISCORD_PROCESS_NAMES,
                        "ip_version": 6,
                        "action": "reject",
                        "method": "drop",
                    },

                    # Discord IPv4 -> interface OpenVPN em L3.
                    {
                        "process_name": self.DISCORD_PROCESS_NAMES,
                        "ip_version": 4,
                        "preferred_by": [
                            "discord-vpn"
                        ],
                        "action": "route",
                        "outbound": "discord-vpn",
                    },
                ],

                # Todo o restante continua pela WAN original.
                "final": "wan-direct",
            },
        }

        temporary = self._config_file.with_suffix(
            ".tmp"
        )

        temporary.write_text(
            json.dumps(
                config,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        temporary.replace(
            self._config_file
        )

        # ------------------------------------------------------
        # VALIDAR CONFIGURAÇÃO
        # ------------------------------------------------------

        check_result = subprocess.run(
            [
                str(self._singbox),
                "check",
                "-c",
                str(self._config_file)
            ],
            capture_output=True,
            text=True,
            timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if check_result.returncode != 0:
            message = (
                check_result.stderr
                or
                check_result.stdout
                or
                "erro desconhecido"
            )

            raise RuntimeError(
                "A configuração App-VPN foi recusada pelo sing-box:\n\n"
                f"{message[:2500]}"
            )

        # ------------------------------------------------------
        # LOG DO ENGINE
        # ------------------------------------------------------

        SINGBOX_LOG_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self._log_handle = open(
            SINGBOX_LOG_FILE,
            "a",
            encoding="utf-8",
            errors="replace"
        )

        self._log_handle.write(
            "\n========================================\n"
            f"OpenDis App-VPN {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            "========================================\n"
        )
        self._log_handle.flush()

        # ------------------------------------------------------
        # INICIAR SING-BOX
        # ------------------------------------------------------

        creationflags = 0
        startupinfo = None

        if os.name == "nt":
            # Console próprio oculto. Isso permite tentar enviar
            # CTRL_BREAK na finalização para o sing-box executar o
            # teardown do Wintun antes do fallback terminate/kill.
            creationflags = (
                subprocess.CREATE_NEW_PROCESS_GROUP
                |
                subprocess.CREATE_NEW_CONSOLE
            )

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0

        self._process = subprocess.Popen(
            [
                str(self._singbox),
                "run",
                "-c",
                str(self._config_file)
            ],
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            startupinfo=startupinfo
        )

        # ------------------------------------------------------
        # AGUARDAR TUN
        # ------------------------------------------------------

        deadline = time.time() + 20

        while time.time() < deadline:

            if self._process.poll() is not None:
                try:
                    log_text = SINGBOX_LOG_FILE.read_text(
                        encoding="utf-8",
                        errors="replace"
                    )
                except Exception:
                    log_text = ""

                raise RuntimeError(
                    "O engine App-VPN encerrou durante a inicialização.\n\n"
                    f"{log_text[-3000:]}"
                )

            if self._find_opendis_tun():
                break

            time.sleep(0.25)

        if not self._find_opendis_tun():
            raise RuntimeError(
                "A interface OpenDisTun não foi criada."
            )

        # O TUN foi criado; limpar respostas DNS antigas evita o
        # Discord reutilizar falhas da tentativa anterior.
        flush_windows_dns_cache()

        self.running = True
        self.prepared = True

        self._log(
            "🛡️ App-VPN iniciado."
        )
        self._log(
            "💬 Discord.exe -> OpenVPN"
        )
        self._log(
            f"🌐 demais processos -> {wan_name}"
        )

        return True


    # ==========================================================
    # LOCALIZAR TUN OPENDIS
    # ==========================================================

    def _find_opendis_tun(
        self
    ):

        try:

            adapters = (
                get_windows_network_adapters()
            )

            for adapter in adapters:

                text = (
                    adapter["name"]
                    +
                    " "
                    +
                    adapter["description"]
                ).lower()

                if (
                    "opendistun"
                    in text
                    or
                    "opendis"
                    in text
                ):
                    return adapter

        except Exception:
            pass

        return None

    # ==========================================================
    # ASSOCIAR PROCESSOS
    # ==========================================================

    def attach_processes(
        self,
        pids
    ):
        """
        O sing-box associa por nome/path do processo.

        Mantemos os PIDs aqui para:
            - integração com seu monitor atual
            - diagnóstico
            - verify()
        """

        if not self.prepared:

            raise RuntimeError(
                "O engine App-VPN "
                "ainda não foi preparado."
            )

        if not pids:
            return False

        accepted = []

        with self._lock:

            for pid in pids:

                try:

                    pid = int(
                        pid
                    )

                except Exception:
                    continue

                if pid <= 0:
                    continue

                name = (
                    get_process_name(
                        pid
                    )
                )

                if not name:
                    continue

                if name.lower() not in {
                    item.lower()
                    for item
                    in self.DISCORD_PROCESS_NAMES
                }:

                    continue

                self.discord_pids.add(
                    pid
                )

                accepted.append(
                    pid
                )

        if accepted:

            self._log(
                "🛡️ Discord protegido: "
                f"{sorted(self.discord_pids)}"
            )

            return True

        return False

    # ==========================================================
    # VERIFICAÇÃO
    # ==========================================================

    def verify(
        self,
        pids
    ):
        """
        Valida a estrutura ativa do isolamento.

        A verificação funcional da conexão do Discord é feita pelo
        OpenDis depois de o aplicativo ser iniciado.
        """

        if not self.prepared or not self.running:
            return False

        if (
            not self._process
            or
            self._process.poll() is not None
        ):
            return False

        if (
            not self.openvpn_process
            or
            self.openvpn_process.poll() is not None
        ):
            return False

        if not self._find_opendis_tun():
            return False

        if not self._vpn_adapter or not self._wan_adapter:
            return False

        active_adapters = get_windows_network_adapters()
        active_indexes = {
            int(item["if_index"])
            for item in active_adapters
            if item.get("if_index") is not None
        }

        if int(self._vpn_adapter["if_index"]) not in active_indexes:
            return False

        if int(self._wan_adapter["if_index"]) not in active_indexes:
            return False

        if not pids:
            return False

        valid_pids = set()

        for pid in pids:
            try:
                pid = int(pid)
            except Exception:
                continue

            name = get_process_name(pid)

            if not name:
                continue

            if name.lower() in {
                item.lower()
                for item in self.DISCORD_PROCESS_NAMES
            }:
                valid_pids.add(pid)

        if not valid_pids:
            return False

        with self._lock:
            if not (
                valid_pids
                <=
                self.discord_pids
            ):
                return False

        try:
            config = json.loads(
                self._config_file.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            return False

        outbounds = config.get(
            "outbounds",
            []
        )

        direct_ok = False
        bridge_ok = False

        for outbound in outbounds:
            if not isinstance(outbound, dict):
                continue

            if (
                outbound.get("tag") == "wan-direct"
                and
                outbound.get("bind_interface")
                ==
                self._wan_adapter["name"]
            ):
                direct_ok = True

            if (
                outbound.get("tag") == "discord-vpn"
                and
                outbound.get("interface")
                ==
                self._vpn_adapter["name"]
            ):
                bridge_ok = True

        if not direct_ok or not bridge_ok:
            return False

        rules = config.get(
            "route",
            {}
        ).get(
            "rules",
            []
        )

        discord_rule_found = False

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            processes = rule.get(
                "process_name",
                []
            )

            if isinstance(processes, str):
                processes = [processes]

            processes_lower = {
                str(item).lower()
                for item in processes
            }

            if (
                "discord.exe" in processes_lower
                and
                rule.get("outbound") == "discord-vpn"
                and
                "discord-vpn" in rule.get("preferred_by", [])
            ):
                discord_rule_found = True
                break

        return discord_rule_found


    # ==========================================================
    # LIMPEZA
    # ==========================================================

    def _request_graceful_singbox_stop(
        self,
        process
    ):
        """
        Tenta entregar CTRL_BREAK ao console oculto do sing-box.

        Se não for possível, cleanup() continua com terminate/kill.
        """

        if os.name != "nt" or not process:
            return False

        try:
            kernel32 = ctypes.windll.kernel32

            had_console = bool(
                kernel32.GetConsoleWindow()
            )

            # Desanexa temporariamente o OpenDis do console atual,
            # caso esteja rodando como .py em um terminal.
            try:
                kernel32.FreeConsole()
            except Exception:
                pass

            attached = bool(
                kernel32.AttachConsole(
                    int(process.pid)
                )
            )

            if not attached:
                if had_console:
                    try:
                        kernel32.AttachConsole(
                            0xFFFFFFFF
                        )
                    except Exception:
                        pass
                return False

            try:
                # O OpenDis não deve receber o evento que está enviando.
                kernel32.SetConsoleCtrlHandler(
                    None,
                    True
                )

                result = bool(
                    kernel32.GenerateConsoleCtrlEvent(
                        int(signal.CTRL_BREAK_EVENT),
                        int(process.pid)
                    )
                )

                time.sleep(0.15)

                return result

            finally:
                try:
                    kernel32.FreeConsole()
                except Exception:
                    pass

                try:
                    kernel32.SetConsoleCtrlHandler(
                        None,
                        False
                    )
                except Exception:
                    pass

                if had_console:
                    try:
                        kernel32.AttachConsole(
                            0xFFFFFFFF
                        )
                    except Exception:
                        pass

        except Exception:
            return False

    def cleanup(
        self,
        silent=False
    ):
        """
        Encerra a camada App-VPN e devolve o Windows ao estado
        anterior ao OpenDisTun.

        Não encerra o OpenVPN; isso é responsabilidade do fluxo
        principal, para manter a ordem correta:

            1. remover OpenDisTun
            2. encerrar OpenVPN
            3. voltar integralmente à WAN original
        """

        self.running = False
        self.prepared = False

        process = self._process
        process_stopped = True

        if process:
            process_stopped = False

            try:
                if process.poll() is None:
                    self._request_graceful_singbox_stop(
                        process
                    )

                    try:
                        process.wait(
                            timeout=6
                        )
                    except subprocess.TimeoutExpired:
                        pass

                if process.poll() is None:
                    try:
                        process.terminate()
                    except Exception:
                        pass

                    try:
                        process.wait(
                            timeout=4
                        )
                    except subprocess.TimeoutExpired:
                        pass

                if process.poll() is None:
                    try:
                        process.kill()
                    except Exception:
                        pass

                    try:
                        process.wait(
                            timeout=4
                        )
                    except Exception:
                        pass

                process_stopped = (
                    process.poll() is not None
                )

            except Exception:
                process_stopped = (
                    process.poll() is not None
                )

        self._process = None

        try:
            if self._log_handle:
                self._log_handle.flush()
                self._log_handle.close()
        except Exception:
            pass

        self._log_handle = None

        # O Wintun normalmente remove a interface quando o processo
        # fecha corretamente. O Windows, porém, pode manter o adaptador
        # listado como Down por alguns segundos mesmo depois do túnel já
        # ter sido encerrado. Esse estado não é falha de limpeza.
        tun_removed = wait_for_adapter_to_disappear(
            "OpenDisTun",
            timeout=4
        )

        if not tun_removed:

            tun_still_active = is_windows_adapter_active(
                "OpenDisTun"
            )

            if tun_still_active:
                tun_removed = remove_opendis_tun_fallback()
            else:
                # Adaptador residual/inativo: tráfego já não passa
                # pelo OpenDisTun. Consideramos o teardown concluído
                # e deixamos o Windows remover o objeto residual.
                tun_removed = True

        flush_windows_dns_cache()

        with self._lock:
            self.discord_pids.clear()

        self._vpn_adapter = None
        self._wan_adapter = None

        if not silent:
            if tun_removed:
                self._log(
                    "🧹 OpenDisTun removido."
                )
            else:
                self._log(
                    "⚠️ OpenDisTun ainda aparece no Windows; "
                    "o processo do engine já foi encerrado."
                )

            self._log(
                "🧹 App-VPN encerrado."
            )

        # Para a restauração de rede, o critério importante é o TUN
        # não permanecer ativo. Em alguns builds do Windows o handle do
        # processo pode demorar um pouco para refletir o encerramento,
        # mesmo com a interface já desmontada. Não transformamos isso
        # em falso positivo para o usuário.
        return tun_removed



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

        # --------------------------------------------------------
        # ESTADO DA OPERAÇÃO
        # --------------------------------------------------------

        self.vpn_process = None
        self.vpn_log_file = None
        self.current_profile = None
        self.current_public_ip = None
        self.ovpn_username = ""
        self.ovpn_password = ""
        self.is_vpnbook_profile = False

        self.discord_process = None
        self.discord_pids = []

        self.operation_active = False
        self.shutdown_in_progress = False
        self.operation_stop_event = threading.Event()

        # --------------------------------------------------------
        # APP-VPN
        # --------------------------------------------------------

        self.vpn_engine = DiscordVPNEngine()

        # --------------------------------------------------------
        # VPNBOOK / PING AO VIVO
        # --------------------------------------------------------

        self.random_vpn_button = None
        self.save_vpnbook_var = None
        self.save_vpnbook_checkbox = None

        self.vpn_ping_stop_event = None
        self.vpn_ping_thread = None
        self.vpn_ping_widgets = {}
        self.vpn_selection_servers = []
        self.best_ping_label = None
        self.best_vpn_button = None

        # --------------------------------------------------------
        # UI FINAL
        # --------------------------------------------------------

        self.stop_vpn_btn = None

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

        # O X da janela também deve desfazer a VPN quando houver
        # uma operação ativa, evitando processos órfãos.
        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_window_close
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
    # MONITORAR PROCESSOS DO DISCORD
    # ========================================================

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

        self.stop_vpn_ping_monitor()
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

        # Seleção manual não pode herdar estado do fluxo VPNBook.
        # Isto é importante porque o perfil manual usa uma política
        # de rotas mais restritiva no runtime do OpenVPN.
        self.selected_vpn_server = None
        self.is_vpnbook_profile = False

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
        self.selected_vpn_server = None

        self.show_profile_screen()

    def show_vpn_selection_screen(self, servers):
        """
        Exibe os servidores VPNBook e mantém o ping sendo atualizado
        continuamente enquanto esta tela estiver aberta.
        """

        self.stop_vpn_ping_monitor()
        self.clear()

        self.vpn_selection_servers = [
            dict(item)
            for item in servers
        ]

        self.vpn_ping_widgets = {}

        ctk.CTkLabel(
            self.container,
            text="🌐 Escolha sua VPN",
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            ),
            text_color="#cccccc"
        ).pack(
            pady=(22, 4)
        )

        ctk.CTkLabel(
            self.container,
            text="Ping atualizado continuamente",
            font=ctk.CTkFont(
                size=12
            ),
            text_color="#888899"
        ).pack(
            pady=(0, 4)
        )

        self.best_ping_label = ctk.CTkLabel(
            self.container,
            text="🔄 Calculando melhor servidor...",
            font=ctk.CTkFont(
                size=11,
                weight="bold"
            ),
            text_color="#57F287"
        )

        self.best_ping_label.pack(
            pady=(0, 8)
        )

        list_frame = ctk.CTkFrame(
            self.container,
            fg_color="#12121a",
            corner_radius=12
        )

        list_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(2, 7)
        )

        header = ctk.CTkFrame(
            list_frame,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=10,
            pady=(8, 5)
        )

        ctk.CTkLabel(
            header,
            text="SERVIDOR",
            width=145,
            anchor="w",
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            ),
            text_color="#666675"
        ).pack(
            side="left"
        )

        ctk.CTkLabel(
            header,
            text="PING",
            width=65,
            anchor="center",
            font=ctk.CTkFont(
                size=10,
                weight="bold"
            ),
            text_color="#666675"
        ).pack(
            side="left"
        )

        ctk.CTkLabel(
            header,
            text="",
            width=25
        ).pack(
            side="left"
        )

        scroll_frame = ctk.CTkScrollableFrame(
            list_frame,
            fg_color="transparent",
            corner_radius=8
        )

        scroll_frame.pack(
            fill="both",
            expand=True,
            padx=6,
            pady=(0, 6)
        )

        self.vpn_scroll_frame = scroll_frame

        for item in self.vpn_selection_servers:

            row = ctk.CTkFrame(
                scroll_frame,
                fg_color="#1e1e2e",
                corner_radius=8
            )

            row.pack(
                fill="x",
                padx=2,
                pady=4
            )

            server_name = item.get(
                "name",
                "VPN"
            )

            server_host = item.get(
                "server",
                ""
            )

            ping = item.get("ping")
            dot, dot_color = ping_status(ping)

            name_frame = ctk.CTkFrame(
                row,
                fg_color="transparent",
                width=145
            )

            name_frame.pack(
                side="left",
                padx=(8, 0),
                pady=8
            )

            name_frame.pack_propagate(False)

            ctk.CTkLabel(
                name_frame,
                text=server_name,
                anchor="w",
                font=ctk.CTkFont(
                    size=11,
                    weight="bold"
                ),
                text_color="#dddddd"
            ).pack(fill="x")

            ctk.CTkLabel(
                name_frame,
                text=server_host,
                anchor="w",
                font=ctk.CTkFont(size=9),
                text_color="#777788"
            ).pack(fill="x")

            ping_label = ctk.CTkLabel(
                row,
                text=(
                    f"{ping} ms"
                    if ping is not None
                    else "..."
                ),
                width=65,
                font=ctk.CTkFont(
                    size=11,
                    weight="bold"
                ),
                text_color="#cccccc"
            )

            ping_label.pack(side="left")

            dot_label = ctk.CTkLabel(
                row,
                text=dot,
                width=25,
                font=ctk.CTkFont(
                    size=17,
                    weight="bold"
                ),
                text_color=dot_color
            )

            dot_label.pack(side="left")

            select_button = ctk.CTkButton(
                row,
                text="SELECIONAR",
                width=92,
                height=30,
                font=ctk.CTkFont(
                    size=10,
                    weight="bold"
                ),
                corner_radius=15,
                fg_color="#5865F2",
                hover_color="#4752C4",
                command=lambda s=item:
                self.select_vpn_server(s)
            )

            select_button.pack(
                side="right",
                padx=8
            )

            self.vpn_ping_widgets[
                server_host.lower()
            ] = {
                "ping_label": ping_label,
                "dot_label": dot_label,
                "select_button": select_button,
            }

        self.best_vpn_button = ctk.CTkButton(
            self.container,
            text="⚡ USAR MENOR PING AGORA",
            command=self.select_best_vpn_server,
            fg_color="#3ba55d",
            hover_color="#2d7d46",
            width=250,
            height=36,
            font=ctk.CTkFont(
                size=12,
                weight="bold"
            ),
            corner_radius=18
        )

        self.best_vpn_button.pack(
            pady=(3, 4)
        )

        ctk.CTkButton(
            self.container,
            text="← VOLTAR",
            command=self.back_from_vpn_selection,
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
            pady=(2, 9)
        )

        self.start_vpn_ping_monitor()

    def start_vpn_ping_monitor(self):
        """
        Inicia a atualização contínua dos pings da tela VPNBook.
        """

        self.stop_vpn_ping_monitor()

        if not self.vpn_selection_servers:
            return

        stop_event = threading.Event()
        self.vpn_ping_stop_event = stop_event

        self.vpn_ping_thread = threading.Thread(
            target=self._vpn_ping_worker,
            args=(stop_event,),
            daemon=True
        )

        self.vpn_ping_thread.start()

    def stop_vpn_ping_monitor(self):
        """
        Encerra o monitor de ping sem bloquear a interface.
        """

        event = getattr(
            self,
            "vpn_ping_stop_event",
            None
        )

        if event:
            event.set()

        self.vpn_ping_stop_event = None
        self.vpn_ping_thread = None

    def _vpn_ping_worker(self, stop_event):
        """
        Mede cada servidor repetidamente. Com três servidores,
        cada linha recebe um valor novo a cada poucos segundos.
        """

        while not stop_event.is_set():

            for item in list(
                self.vpn_selection_servers
            ):

                if stop_event.is_set():
                    return

                host = str(
                    item.get(
                        "server",
                        ""
                    )
                ).strip()

                if not host:
                    continue

                ping = ping_vpn_server(
                    host,
                    timeout=900
                )

                item["ping"] = ping

                self.after(
                    0,
                    lambda h=host, p=ping:
                    self._apply_live_ping(
                        h,
                        p
                    )
                )

                # Pequeno intervalo entre hosts para não gerar uma
                # sequência contínua de processos ping.exe.
                if stop_event.wait(0.20):
                    return

            # Atualização quase contínua sem consumo desnecessário.
            if stop_event.wait(1.0):
                return

    def _apply_live_ping(self, host, ping):
        """
        Atualiza os widgets de um servidor e destaca o melhor atual.
        """

        try:
            key = str(host).lower()
            widgets = self.vpn_ping_widgets.get(key)

            if widgets:
                ping_text = (
                    f"{ping} ms"
                    if ping is not None
                    else "Offline"
                )

                dot, dot_color = ping_status(ping)

                widgets["ping_label"].configure(
                    text=ping_text
                )

                widgets["dot_label"].configure(
                    text=dot,
                    text_color=dot_color
                )

            available = [
                item
                for item in self.vpn_selection_servers
                if item.get("ping") is not None
            ]

            best = None

            if available:
                best = min(
                    available,
                    key=lambda item: item["ping"]
                )

            best_host = (
                str(best.get("server", "")).lower()
                if best
                else ""
            )

            for server_host, data in self.vpn_ping_widgets.items():
                if server_host == best_host:
                    data["select_button"].configure(
                        text="★ MELHOR"
                    )
                else:
                    data["select_button"].configure(
                        text="SELECIONAR"
                    )

            if self.best_ping_label:
                if best:
                    self.best_ping_label.configure(
                        text=(
                            f"★ Melhor agora: "
                            f"{best.get('name', 'VPN')} • "
                            f"{best.get('ping')} ms"
                        )
                    )
                else:
                    self.best_ping_label.configure(
                        text="🔴 Nenhum servidor respondeu agora"
                    )

        except Exception:
            # A tela pode ter sido destruída entre o ping e o callback.
            pass

    def select_best_vpn_server(self):
        """
        Seleciona o servidor com o menor ping medido neste instante.
        """

        available = [
            item
            for item in self.vpn_selection_servers
            if item.get("ping") is not None
        ]

        if not available:
            mb.showwarning(
                "VPNBook",
                "Nenhum servidor respondeu ao ping neste momento."
            )
            return

        best = min(
            available,
            key=lambda item: item["ping"]
        )

        self.select_vpn_server(best)

    def back_from_vpn_selection(self):
        self.stop_vpn_ping_monitor()
        self.show_profile_screen()


    def select_vpn_server(self, server):
        """
        Define o servidor VPNBook escolhido usando o valor de ping
        mais recente disponível na tela ao vivo.
        """

        self.stop_vpn_ping_monitor()

        self.selected_vpn_server = dict(server)
        self.current_profile = None
        self.ovpn_username = ""
        self.ovpn_password = ""
        self.is_vpnbook_profile = True

        self.log(
            f"🌐 VPN selecionada: "
            f"{server.get('name', 'VPN')}"
        )
        self.log(
            f"🔌 Servidor: "
            f"{server.get('server', '')}"
        )
        self.log(
            f"📡 Ping atual: "
            f"{server.get('ping', 'N/A')} ms"
        )
        self.log(
            "⏳ Preparando perfil VPN..."
        )

        try:
            for widget in self.vpn_scroll_frame.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkButton):
                        child.configure(state="disabled")
        except Exception:
            pass

        if self.best_vpn_button:
            try:
                self.best_vpn_button.configure(
                    state="disabled"
                )
            except Exception:
                pass

        threading.Thread(
            target=self._prepare_selected_vpn,
            daemon=True
        ).start()


    def _prepare_selected_vpn(self):
        """
        Localiza ou baixa o perfil correspondente
        ao servidor VPNBook selecionado.
        """

        try:

            # ====================================================
            # SERVIDOR
            # ====================================================

            server = getattr(
                self,
                "selected_vpn_server",
                None
            )

            if not server:
                raise RuntimeError(
                    "Nenhum servidor VPN foi selecionado."
                )

            self.after(
                0,
                lambda:
                self.log(
                    f"🔧 Preparando: "
                    f"{server.get('name', 'VPN')}"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    f"🌐 Host: "
                    f"{server.get('server', '')}"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    f"🔌 Protocolo: "
                    f"{server.get('protocol', '')}"
                )
            )

            # ====================================================
            # CREDENCIAIS
            # ====================================================

            self.after(
                0,
                lambda:
                self.log(
                    "🔐 Obtendo credenciais atuais do VPNBook..."
                )
            )

            username, password = (
                vpnbook_get_credentials()
            )

            if not username or not password:
                raise RuntimeError(
                    "Não foi possível obter "
                    "as credenciais atuais do VPNBook."
                )

            # ====================================================
            # PROCURAR PERFIL
            # ====================================================

            self.after(
                0,
                lambda:
                self.log(
                    "🔎 Procurando perfil .ovpn salvo..."
                )
            )

            profile = vpnbook_find_profile(
                server["server"],
                server["protocol"]
            )

            # ====================================================
            # BAIXAR SE NECESSÁRIO
            # ====================================================

            if not profile:

                self.after(
                    0,
                    lambda:
                    self.log(
                        "📥 Perfil não encontrado."
                    )
                )

                self.after(
                    0,
                    lambda:
                    self.log(
                        "📥 Baixando configuração OpenVPN..."
                    )
                )

                profile = vpnbook_download_profile(
                    server=server["server"],
                    protocol=server["protocol"]
                )

            else:

                self.after(
                    0,
                    lambda p=profile:
                    self.log(
                        f"💾 Perfil encontrado: "
                        f"{p.name}"
                    )
                )

            # ====================================================
            # VALIDAR
            # ====================================================

            if not profile:
                raise RuntimeError(
                    "O perfil VPN não foi encontrado."
                )

            profile = Path(
                profile
            )

            if not profile.exists():
                raise RuntimeError(
                    f"Perfil VPN não existe:\n{profile}"
                )

            if profile.suffix.lower() != ".ovpn":
                raise RuntimeError(
                    "O arquivo baixado não é um "
                    "perfil OpenVPN válido."
                )

            # ====================================================
            # PRONTO
            # ====================================================

            self.after(
                0,
                lambda p=profile:
                self.log(
                    f"✅ Perfil pronto: {p.name}"
                )
            )

            self.after(
                0,
                lambda p=profile,
                       u=username,
                       pw=password:
                self._selected_vpn_ready(
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

    def _selected_vpn_ready(
            self,
            profile,
            username,
            password
    ):
        """
        Define o perfil selecionado e segue
        para a tela de preparação.
        """

        self.current_profile = Path(
            profile
        )

        self.ovpn_username = username
        self.ovpn_password = password

        self.is_vpnbook_profile = True

        server = getattr(
            self,
            "selected_vpn_server",
            None
        )

        # ========================================================
        # LOG
        # ========================================================

        self.log(
            "========================================"
        )

        self.log(
            "✅ VPN preparada com sucesso."
        )

        if server:
            self.log(
                f"🌐 VPN: "
                f"{server.get('name', 'VPN')}"
            )

            self.log(
                f"📡 Host: "
                f"{server.get('server', '')}"
            )

            self.log(
                f"📶 Ping: "
                f"{server.get('ping', 'N/A')} ms"
            )

            self.log(
                f"🔌 Protocolo: "
                f"{server.get('protocol', '')}"
            )

        self.log(
            f"📄 Perfil: "
            f"{self.current_profile.name}"
        )

        self.log(
            "========================================"
        )

        # ========================================================
        # IR PARA PREPARAÇÃO
        # ========================================================

        self.after(
            0,
            self.show_connect_screen
        )

    def show_connect_screen(self):
        self.stop_vpn_ping_monitor()
        self.clear()

        server = getattr(
            self,
            "selected_vpn_server",
            None
        )

        server_name = (
            server["name"]
            if server
            else "VPN selecionada"
        )

        server_host = (
            server["server"]
            if server
            else ""
        )

        ping = (
            server.get("ping")
            if server
            else None
        )

        ctk.CTkLabel(
            self.container,
            text="🚀 Pronto para iniciar!",
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            ),
            text_color="#cccccc"
        ).pack(
            pady=(32, 5)
        )

        ctk.CTkLabel(
            self.container,
            text=(
                f"VPN: {server_name}\n"
                f"{server_host}\n"
                f"Ping mais recente: {ping} ms"
                if ping is not None
                else
                f"VPN: {server_name}\n"
                f"{server_host}"
            ),
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            text_color="#a0a0b0",
            justify="center"
        ).pack(
            pady=(5, 12)
        )

        self.log_text = ctk.CTkTextbox(
            self.container,
            width=360,
            height=150,
            font=ctk.CTkFont(size=12),
            fg_color="#12121a",
            text_color="#8e9297"
        )

        self.log_text.pack(
            pady=(5, 8)
        )

        self.log_text.insert(
            "1.0",
            "[] Aguardando início...\n"
        )

        self.log_text.configure(
            state="disabled"
        )

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
            pady=(4, 2)
        )

        self.progress_bar = ctk.CTkProgressBar(
            self.container,
            width=360,
            height=12,
            mode="determinate"
        )

        self.progress_bar.set(0)
        self.progress_bar.pack(
            pady=(0, 8)
        )

        self.start_btn = ctk.CTkButton(
            self.container,
            text="⚡ INICIAR",
            command=self.run_unlock,
            fg_color="#5865F2",
            hover_color="#4752C4",
            height=48,
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            ),
            corner_radius=24
        )

        self.start_btn.pack(
            pady=(8, 5)
        )

        self.stop_vpn_btn = ctk.CTkButton(
            self.container,
            text="⛔ FECHAR E ENCERRAR VPN",
            command=self.request_shutdown_and_exit,
            fg_color="#ed4245",
            hover_color="#c03538",
            height=40,
            width=300,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            corner_radius=20
        )

        # Só aparece quando a operação estiver concluída.

        self.final_status = ctk.CTkLabel(
            self.container,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        )

        self.final_status.pack(
            pady=4
        )

        self.activity_bar = ctk.CTkProgressBar(
            self.container,
            width=160,
            height=6,
            mode="indeterminate"
        )

        self.activity_bar.pack(
            pady=(0, 6)
        )

        self.set_progress(
            0,
            "Aguardando início..."
        )


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
        """
        Busca todos os servidores VPNBook,
        mede o ping inicial e abre a tela de atualização ao vivo.
        """

        self.stop_vpn_ping_monitor()

        try:

            self.random_vpn_button.configure(
                state="disabled",
                text="🔄 TESTANDO SERVIDORES..."
            )

            self.save_vpnbook_checkbox.configure(
                state="disabled"
            )

        except Exception:
            pass

        threading.Thread(
            target=self._scan_vpnbook_servers,
            daemon=True
        ).start()

    def _scan_vpnbook_servers(self):
        """
        Testa todos os servidores configurados no VPNBook.
        """

        try:

            servers = []

            for base_server in VPNBOOK_SERVERS:

                server = dict(
                    base_server
                )

                host = server["server"]

                self.after(
                    0,
                    lambda h=host:
                    self.log(
                        f"📡 Testando ping: {h}"
                    )
                )

                ping = ping_vpn_server(
                    host
                )

                server["ping"] = ping

                if ping is None:

                    self.after(
                        0,
                        lambda h=host:
                        self.log(
                            f"🔴 {h}: sem resposta"
                        )
                    )

                else:

                    self.after(
                        0,
                        lambda h=host,
                               p=ping:
                        self.log(
                            f"📡 {h}: {p} ms"
                        )
                    )

                servers.append(
                    server
                )

            # ----------------------------------------------------
            # Ordenar pelo menor ping
            # ----------------------------------------------------

            servers.sort(
                key=lambda item:
                (
                    item["ping"]
                    if item["ping"] is not None
                    else 999999
                )
            )

            self.after(
                0,
                lambda s=servers:
                self.show_vpn_selection_screen(s)
            )

        except Exception as e:

            error = str(e)

            self.after(
                0,
                lambda msg=error:
                self._random_vpn_error(msg)
            )
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

        self.operation_stop_event.clear()
        self.shutdown_in_progress = False

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
        Fluxo principal:

            1. Localiza OpenVPN
            2. Localiza Discord
            3. Valida perfil .ovpn
            4. Obtém IP inicial
            5. Prepara credenciais
            6. Inicia OpenVPN
            7. Aguarda túnel
            8. Confirma IP da VPN
            9. Prepara isolamento App-VPN
            10. Inicia Discord
            11. Obtém PID(s) do Discord
            12. Anexa Discord ao engine
            13. Verifica isolamento
            14. Aguarda estabilização
            15. Mantém VPN conectada
            16. Finaliza operação

        Em caso de erro:
            - limpa o engine
            - desconecta a VPN se necessário
            - mantém o log para diagnóstico
            - remove credenciais temporárias
        """

        vpn_connected = False
        credentials_file = None
        runtime_profile = None
        process = None
        log_handle = None
        keep_log_file = False

        try:

            # ========================================================
            # 1. LOCALIZAR OPENVPN
            # ========================================================

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

            # ========================================================
            # 2. LOCALIZAR DISCORD
            # ========================================================

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

            if discord_process_running():
                raise RuntimeError(
                    "O Discord já está aberto.\n\n"
                    "Feche completamente o Discord antes de iniciar "
                    "o OpenDis. Isso garante que nenhuma conexão antiga "
                    "permaneça fora da VPN."
                )

            # ========================================================
            # 2.1 PREPARAR DEPENDÊNCIA APP-VPN ANTES DA VPN
            # ========================================================

            self.after(
                0,
                lambda:
                self.set_progress(
                    17,
                    "Preparando componente App-VPN..."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "📦 Verificando componente App-VPN..."
                )
            )

            singbox_path = ensure_singbox_ready()

            self.after(
                0,
                lambda p=singbox_path:
                self.log(
                    f"✅ App-VPN pronto: {p.name}"
                )
            )

            # ========================================================
            # 2.2 IDENTIFICAR A WAN ORIGINAL
            # ========================================================

            wan_adapter = get_default_ipv4_adapter()

            if not wan_adapter:
                raise RuntimeError(
                    "Não foi possível identificar a interface "
                    "de Internet original do Windows."
                )

            self.after(
                0,
                lambda a=wan_adapter:
                self.log(
                    f"🌐 WAN original: {a['name']} "
                    f"({a.get('ipv4', 'sem IPv4')})"
                )
            )

            # Snapshot das interfaces ativas antes do OpenVPN.
            baseline_adapters = get_windows_network_adapters()

            baseline_if_indexes = {
                int(item["if_index"])
                for item in baseline_adapters
                if item.get("if_index") is not None
            }

            # Snapshot das rotas default antes de qualquer perfil VPN.
            # O caminho manual usa isto como fail-safe para restaurar
            # imediatamente a WAN caso o servidor tente instalar def1.
            baseline_default_routes = get_windows_default_ipv4_routes()

            # ========================================================
            # 3. PERFIL VPN
            # ========================================================

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

            profile = Path(profile)

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
                    f"📄 Perfil VPN: {p}"
                )
            )

            # ========================================================
            # 4. SERVIDOR SELECIONADO
            # ========================================================

            selected_server = getattr(
                self,
                "selected_vpn_server",
                None
            )

            if selected_server:
                self.after(
                    0,
                    lambda:
                    self.log(
                        "========================================"
                    )
                )

                self.after(
                    0,
                    lambda s=selected_server:
                    self.log(
                        f"🌐 VPN: {s.get('name', 'VPN')}"
                    )
                )

                self.after(
                    0,
                    lambda s=selected_server:
                    self.log(
                        f"🔌 Host: {s.get('server', '')}"
                    )
                )

                self.after(
                    0,
                    lambda s=selected_server:
                    self.log(
                        f"📡 Ping medido: "
                        f"{s.get('ping', 'N/A')} ms"
                    )
                )

            # ========================================================
            # 5. IP INICIAL
            # ========================================================

            self.after(
                0,
                lambda: self.set_progress(
                    25,
                    "Obtendo IP atual..."
                )
            )

            self.current_public_ip = get_public_ip_retry(
                timeout=8,
                attempts=5,
                delay=1.0
            )

            if not self.current_public_ip:

                raise RuntimeError(
                    "Não foi possível confirmar o IP público "
                    "da conexão normal antes de iniciar a VPN.\n\n"
                    "O OpenDis cancelou a operação porque não "
                    "consegue validar o split tunnel com segurança."
                )

            self.after(
                0,
                lambda ip=self.current_public_ip:
                self.log(
                    f"🌐 IP inicial: {ip}"
                )
            )

            # ========================================================
            # 6. PREPARAR CREDENCIAIS
            # ========================================================

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

            if username and password:

                self.after(
                    0,
                    lambda:
                    self.log(
                        "🔐 Credenciais disponíveis."
                    )
                )

                fd, credentials_path = tempfile.mkstemp(
                    prefix="opendis_",
                    suffix=".txt"
                )

                os.close(fd)

                credentials_file = Path(
                    credentials_path
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

                self.after(
                    0,
                    lambda:
                    self.log(
                        "🔐 Arquivo temporário de credenciais criado."
                    )
                )

            # ========================================================
            # 7. PERFIL RUNTIME + COMANDO OPENVPN
            # ========================================================
            #
            # O perfil original nunca é alterado. Criamos uma cópia
            # temporária AO LADO dele para preservar caminhos relativos
            # de CA/cert/key/auth files.
            #
            # Removemos diretivas capazes de transformar a VPN em rota
            # global ou trocar o DNS/WAN. No fluxo manual a sanitização
            # é mais rígida: nenhuma rota declarada pelo perfil é instalada.
            # O fluxo VPNBook mantém o comportamento anterior.
            # ========================================================

            self.after(
                0,
                lambda: self.set_progress(
                    30,
                    "Iniciando conexão VPN..."
                )
            )

            manual_profile = not bool(
                getattr(
                    self,
                    "is_vpnbook_profile",
                    False
                )
            )

            if manual_profile:
                self.after(
                    0,
                    lambda:
                    self.log(
                        "🛡️ Perfil manual: modo split-tunnel estrito."
                    )
                )

            try:
                original_text = profile.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                sanitized_lines = []
                removed_runtime_options = []

                for original_line in original_text.splitlines():

                    stripped = original_line.strip()
                    lowered = stripped.lower()

                    if not stripped or stripped.startswith(("#", ";")):
                        sanitized_lines.append(original_line)
                        continue

                    # ------------------------------------------------
                    # O OpenDis controla estas opções em runtime.
                    # ------------------------------------------------

                    first_token = lowered.split(None, 1)[0]

                    if first_token in {
                        "redirect-gateway",
                        "redirect-private",
                        "route-nopull",
                        "route-noexec",
                        "block-outside-dns",
                        "block-ipv6",
                        "pull-filter",
                    }:
                        removed_runtime_options.append(first_token)
                        continue

                    # Não permitir que o perfil troque DNS do Windows.
                    if lowered.startswith("dhcp-option "):
                        removed_runtime_options.append("dhcp-option")
                        continue

                    if (
                        manual_profile
                        and
                        first_token in {
                            "register-dns",
                            "dhcp-renew",
                            "up",
                            "down",
                            "route-up",
                            "route-pre-down",
                            "ipchange",
                            "plugin",
                            "script-security",
                            "up-delay",
                            "up-restart",
                            "down-pre",
                        }
                    ):
                        removed_runtime_options.append(first_token)
                        continue

                    # O Discord deste fluxo é IPv4. Rotas IPv6 do perfil
                    # não devem alterar o restante do computador.
                    if lowered.startswith("route-ipv6 "):
                        removed_runtime_options.append("route-ipv6")
                        continue

                    # Perfil manual: nenhuma rota declarada pelo .ovpn
                    # pode ser instalada no Windows. O bridge do sing-box
                    # envia o Discord diretamente pela interface OpenVPN,
                    # então não precisamos transformar a VPN em gateway do PC.
                    #
                    # VPNBook mantém o comportamento anterior: só retiramos
                    # default/def1, preservando rotas específicas do perfil.
                    if lowered.startswith("route "):

                        if manual_profile:
                            removed_runtime_options.append("route")
                            continue

                        parts = re.split(r"\s+", lowered)

                        network = parts[1] if len(parts) > 1 else ""
                        netmask = parts[2] if len(parts) > 2 else ""

                        is_full_default = (
                            network in {"default", "0.0.0.0"}
                            and
                            netmask in {"", "default", "0.0.0.0"}
                        )

                        is_def1_half = (
                            (
                                network == "0.0.0.0"
                                and netmask == "128.0.0.0"
                            )
                            or
                            (
                                network == "128.0.0.0"
                                and netmask == "128.0.0.0"
                            )
                        )

                        if is_full_default or is_def1_half:
                            removed_runtime_options.append("route-default")
                            continue

                    # Se vamos fornecer auth por CLI, removemos a diretiva
                    # do perfil runtime para não haver duas fontes.
                    if (
                        credentials_file
                        and lowered.startswith("auth-user-pass")
                    ):
                        removed_runtime_options.append("auth-user-pass")
                        continue

                    sanitized_lines.append(original_line)

                fd, runtime_profile_path = tempfile.mkstemp(
                    prefix=".opendis_runtime_",
                    suffix=".ovpn",
                    dir=str(profile.parent)
                )
                os.close(fd)

                runtime_profile = Path(runtime_profile_path)

                runtime_profile.write_text(
                    "\n".join(sanitized_lines) + "\n",
                    encoding="utf-8"
                )

                if removed_runtime_options:
                    removed_text = ", ".join(
                        sorted(set(removed_runtime_options))
                    )

                    self.after(
                        0,
                        lambda t=removed_text:
                        self.log(
                            f"🛡️ Perfil runtime sanitizado: {t}"
                        )
                    )

            except Exception as e:
                raise RuntimeError(
                    "Não foi possível criar o perfil OpenVPN "
                    f"temporário seguro:\n{e}"
                )

            command = [
                str(openvpn),
                "--config",
                str(runtime_profile),

                # Bloqueia TODAS as rotas/DNS empurradas pelo servidor.
                # As propriedades do TUN/TAP (ifconfig/topology) continuam
                # sendo recebidas, conforme comportamento do OpenVPN.
                "--route-nopull",

                # Defesa adicional para redirect padrão, inclusive em
                # servidores/perfis com comportamento diferente.
                "--pull-filter",
                "ignore",
                "redirect-gateway",

                "--pull-filter",
                "ignore",
                "redirect-private",

                "--pull-filter",
                "ignore",
                "dhcp-option",

                "--pull-filter",
                "ignore",
                "block-outside-dns",

                "--pull-filter",
                "ignore",
                "block-ipv6",

                "--pull-filter",
                "ignore",
                "route-ipv6",

                # Não manter usuário/senha em cache após autenticação.
                "--auth-nocache",

                # VPNBook/net30 atualmente precisa do TAP convencional.
                "--disable-dco",
            ]

            if manual_profile:
                # ----------------------------------------------------
                # PERFIL .OVPN MANUAL
                # ----------------------------------------------------
                # O servidor NÃO pode instalar redirect-gateway/def1,
                # DNS ou rotas próprias. Porém o bridge L3 do sing-box
                # precisa que a interface OpenVPN tenha um caminho de
                # egress para destinos públicos.
                #
                # Por isso criamos SOMENTE uma default-route controlada
                # com métrica 5000. Como ela possui o mesmo prefixo /0
                # da WAN, a rota WAN normal (métrica muito menor) vence
                # para o restante do computador. O fail-safe logo após
                # a conexão remove qualquer /1 ou /0 de métrica baixa.
                command.extend(
                    [
                        "--pull-filter",
                        "ignore",
                        "redirect",

                        "--pull-filter",
                        "ignore",
                        "register-dns",

                        "--pull-filter",
                        "ignore",
                        "dns",

                        # Rota de egress exclusiva para o bridge.
                        # NÃO vira a rota preferida do Windows.
                        "--route",
                        "0.0.0.0",
                        "0.0.0.0",
                        "vpn_gateway",
                        "5000",
                    ]
                )

                self.after(
                    0,
                    lambda:
                    self.log(
                        "✅ Perfil manual com rota de egress VPN "
                        "controlada (métrica 5000)."
                    )
                )

            else:
                # ----------------------------------------------------
                # VPNBOOK
                # ----------------------------------------------------
                # Mantém exatamente a rota de egress que já funciona
                # no caminho VPNBook existente. A métrica alta evita
                # que ela substitua a rota principal nesse perfil.
                command.extend(
                    [
                        "--route",
                        "0.0.0.0",
                        "0.0.0.0",
                        "vpn_gateway",
                        "5000",
                    ]
                )

            if credentials_file:
                command.extend(
                    [
                        "--auth-user-pass",
                        str(credentials_file)
                    ]
                )

            self.after(
                0,
                lambda:
                self.log(
                    "🚀 Iniciando OpenVPN..."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🖥️ OpenVPN será mantido ativo até o encerramento."
                )
            )

            # ========================================================
            # 8. CRIAR LOG OPENVPN
            # ========================================================
            #
            # CORREÇÃO DO BUG:
            #
            # self.vpn_log_file era None porque a criação
            # do caminho estava comentada.
            #
            # Agora garantimos que ele seja um Path válido.
            # ========================================================

            self.vpn_log_file = (
                    LOG_DIR
                    / f"openvpn_{int(time.time())}_{os.getpid()}.log"
            )

            self.vpn_log_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            log_handle = open(
                self.vpn_log_file,
                "a",
                encoding="utf-8",
                errors="replace"
            )

            self.after(
                0,
                lambda p=self.vpn_log_file:
                self.log(
                    f"📝 Log OpenVPN: {p.name}"
                )
            )

            # ========================================================
            # 9. INICIAR OPENVPN
            # ========================================================

            creationflags = 0

            if os.name == "nt":
                creationflags = (
                        subprocess.CREATE_NEW_PROCESS_GROUP
                        |
                        subprocess.CREATE_NO_WINDOW
                )

            process = subprocess.Popen(
                command,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags
            )

            self.vpn_process = process
            self.operation_active = True

            self.after(
                0,
                lambda p=process.pid:
                self.log(
                    f"🔌 OpenVPN PID: {p}"
                )
            )

            # ========================================================
            # 10. AGUARDAR VPN
            # ========================================================

            self.after(
                0,
                lambda:
                self.set_progress(
                    40,
                    "Conectando à VPN..."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "⏳ Aguardando Initialization Sequence Completed..."
                )
            )

            vpn_deadline = (
                    time.time()
                    +
                    WAIT_VPN_TIMEOUT
            )

            vpn_ready = False

            while time.time() < vpn_deadline:

                if self.operation_stop_event.is_set():
                    raise RuntimeError(
                        "Operação cancelada pelo usuário."
                    )

                if process.poll() is not None:
                    raise RuntimeError(
                        "O OpenVPN encerrou antes de "
                        "estabelecer a conexão."
                    )

                try:

                    log_text = (
                        self.vpn_log_file.read_text(
                            encoding="utf-8",
                            errors="replace"
                        )
                    )

                except Exception:

                    log_text = ""

                if (
                        "Initialization Sequence Completed"
                        in log_text
                ):
                    vpn_ready = True
                    break

                time.sleep(
                    0.5
                )

            if not vpn_ready:
                raise RuntimeError(
                    "Tempo limite aguardando "
                    "a conexão VPN."
                )

            vpn_connected = True

            self.after(
                0,
                lambda:
                self.log(
                    "========================================"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "✅ Initialization Sequence Completed"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🔒 Túnel VPN estabelecido."
                )
            )

            # ========================================================
            # 11. ESTABILIZAÇÃO VPN
            # ========================================================

            self.after(
                0,
                lambda:
                self.set_progress(
                    50,
                    "Estabilizando VPN..."
                )
            )

            time.sleep(
                2
            )

            # ========================================================
            # 11.1 FAIL-SAFE DE ROTA PARA PERFIL MANUAL
            # ========================================================
            #
            # Alguns provedores (ex.: Proton VPN) empurram
            # redirect-gateway def1. route-nopull + pull-filter devem
            # impedir a instalação. Mesmo assim removemos explicitamente
            # qualquer /1 e qualquer /0 de métrica baixa que apareça na
            # interface VPN, preservando somente a /0 controlada de
            # métrica 5000 usada pelo bridge do sing-box.
            #
            # O fluxo VPNBook NÃO passa por esta rotina.
            # ========================================================

            if manual_profile:

                manual_vpn_adapter = find_openvpn_adapter(
                    exclude_if_indexes=baseline_if_indexes
                )

                if not manual_vpn_adapter:
                    raise RuntimeError(
                        "A VPN conectou, mas a interface OpenVPN manual "
                        "não pôde ser identificada para validar as rotas."
                    )

                self.after(
                    0,
                    lambda a=manual_vpn_adapter:
                    self.log(
                        "🛡️ Validando rotas do perfil manual na interface "
                        f"{a['name']}..."
                    )
                )

                route_ok, route_error = restore_manual_wan_routing(
                    wan_adapter=wan_adapter,
                    baseline_default_routes=baseline_default_routes,
                    vpn_adapter=manual_vpn_adapter
                )

                if not route_ok:
                    raise RuntimeError(
                        "Não foi possível garantir a rota WAN original "
                        "depois de conectar o perfil manual.\n\n"
                        f"{route_error}"
                    )

                self.after(
                    0,
                    lambda:
                    self.log(
                        "✅ Def1 bloqueado; egress VPN controlado mantido."
                    )
                )

                # Diagnóstico explícito da /0 controlada. Assim o log
                # confirma que o bridge tem egress pela VPN sem que essa
                # rota tenha prioridade sobre a WAN normal.
                current_default_routes = get_windows_default_ipv4_routes()
                vpn_default_routes = [
                    item
                    for item in current_default_routes
                    if int(item.get("if_index", -1))
                    == int(manual_vpn_adapter["if_index"])
                ]

                for vpn_route in vpn_default_routes:
                    self.after(
                        0,
                        lambda r=dict(vpn_route):
                        self.log(
                            "🧭 Egress VPN /0: "
                            f"next-hop={r.get('next_hop', '?')} • "
                            f"métrica rota={r.get('route_metric', '?')} • "
                            f"métrica total={r.get('total_metric', '?')}"
                        )
                    )

                # Dar um pequeno intervalo para o Windows recalcular
                # a melhor rota após eventual remoção de def1.
                time.sleep(0.8)

            # ========================================================
            # 12. CONFIRMAR QUE A WAN CONTINUA NORMAL
            # ========================================================

            self.after(
                0,
                lambda:
                self.set_progress(
                    55,
                    "Confirmando isolamento da rota principal..."
                )
            )

            wan_after_vpn = get_public_ip_retry(
                timeout=8,
                attempts=5,
                delay=1.0
            )

            if not wan_after_vpn:

                raise RuntimeError(
                    "Não foi possível confirmar o IP WAN "
                    "depois que o túnel OpenVPN foi criado.\n\n"
                    "O OpenDis cancelou a operação para não "
                    "arriscar rotear outras aplicações pela VPN."
                )

            self.after(
                0,
                lambda ip=wan_after_vpn:
                self.log(
                    f"🌐 IP do computador após criar túnel: {ip}"
                )
            )

            if (
                wan_after_vpn
                !=
                self.current_public_ip
            ):

                # Perfil manual recebe uma última tentativa fail-closed
                # de restauração antes de abortar. Isso cobre provedores
                # que alterem a tabela de rotas alguns instantes depois
                # do Initialization Sequence Completed.
                if manual_profile:

                    self.after(
                        0,
                        lambda:
                        self.log(
                            "⚠️ Alteração WAN detectada; restaurando "
                            "rota original imediatamente..."
                        )
                    )

                    manual_vpn_adapter = find_openvpn_adapter(
                        exclude_if_indexes=baseline_if_indexes
                    )

                    if manual_vpn_adapter:
                        restore_manual_wan_routing(
                            wan_adapter=wan_adapter,
                            baseline_default_routes=baseline_default_routes,
                            vpn_adapter=manual_vpn_adapter
                        )

                        time.sleep(1.0)

                        repaired_ip = get_public_ip_retry(
                            timeout=8,
                            attempts=4,
                            delay=0.7
                        )

                        if repaired_ip == self.current_public_ip:
                            wan_after_vpn = repaired_ip

                            self.after(
                                0,
                                lambda ip=repaired_ip:
                                self.log(
                                    f"✅ WAN restaurada automaticamente: {ip}"
                                )
                            )

                if wan_after_vpn != self.current_public_ip:
                    raise RuntimeError(
                        "A rota principal do computador foi alterada "
                        "pela VPN.\n\n"
                        f"IP antes: {self.current_public_ip}\n"
                        f"IP depois: {wan_after_vpn}\n\n"
                        "O isolamento foi cancelado para evitar que "
                        "outras aplicações utilizem a VPN."
                    )

            self.after(
                0,
                lambda:
                self.log(
                    "✅ Rota principal preservada."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "✅ O computador NÃO entrou na VPN."
                )
            )

            # ========================================================
            # 13. PREPARAR ENGINE APP-VPN
            # ========================================================

            self.after(
                0,
                lambda:
                self.set_progress(
                    65,
                    "Preparando isolamento do Discord..."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🛡️ Preparando camada App-VPN..."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🛡️ Objetivo: Discord → VPN / restante → WAN."
                )
            )

            vpn_engine = getattr(
                self,
                "vpn_engine",
                None
            )

            if vpn_engine is None:
                self.after(
                    0,
                    lambda:
                    self.log(
                        "⚠️ Engine WFP ainda não carregado."
                    )
                )

                raise RuntimeError(
                    "Engine WFP/App-VPN não está instalado."
                )

            self.after(
                0,
                lambda:
                self.log(
                    "🛡️ Engine App-VPN detectado."
                )
            )

            prepare_method = getattr(
                vpn_engine,
                "prepare",
                None
            )

            if callable(
                    prepare_method
            ):
                prepare_method(
                    openvpn_process=process,
                    profile=profile,
                    baseline_if_indexes=baseline_if_indexes,
                    wan_adapter=wan_adapter
                )

                self.after(
                    0,
                    lambda:
                    self.log(
                        "🛡️ Engine preparado."
                    )
                )

            # ========================================================
            # 13.1 CONFIRMAR WAN DEPOIS DO OPENDISTUN
            # ========================================================

            wan_after_engine = get_public_ip_retry(
                timeout=6,
                attempts=4,
                delay=0.8
            )

            if not wan_after_engine:
                raise RuntimeError(
                    "O OpenDisTun foi criado, mas a conexão normal "
                    "do Windows não pôde ser confirmada."
                )

            if wan_after_engine != self.current_public_ip:
                raise RuntimeError(
                    "O App-VPN alterou a saída normal do computador.\n\n"
                    f"IP antes: {self.current_public_ip}\n"
                    f"IP agora: {wan_after_engine}"
                )

            self.after(
                0,
                lambda ip=wan_after_engine:
                self.log(
                    f"✅ WAN continua normal após OpenDisTun: {ip}"
                )
            )

            # ========================================================
            # 14. ABRIR DISCORD
            # ========================================================

            self.after(
                0,
                lambda:
                self.set_progress(
                    70,
                    "Abrindo Discord na VPN..."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "💬 Iniciando Discord..."
                )
            )

            discord_process = subprocess.Popen(
                [str(discord)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    |
                    subprocess.CREATE_NO_WINDOW
                    if os.name == "nt"
                    else 0
                )
            )

            self.discord_process = (
                discord_process
            )

            # Após o Discord assumir o foco, o OpenDis volta para a
            # frente em 15 segundos. O tempo é independente da detecção
            # de PID e usa a mesma janela curta pedida para estabilização.
            self.after(
                int(WAIT_OPENDIS_FOCUS * 1000),
                self.focus_opendis_after_discord
            )

            self.after(
                0,
                lambda p=discord_process.pid:
                self.log(
                    f"💬 Processo inicial do Discord: PID {p}"
                )
            )

            # ========================================================
            # 15. AGUARDAR DISCORD
            # ========================================================

            self.after(
                0,
                lambda:
                self.set_progress(
                    75,
                    "Detectando processos do Discord..."
                )
            )

            discord_deadline = (
                    time.time()
                    +
                    30
            )

            discord_pids = []

            while time.time() < discord_deadline:

                discord_pids = get_discord_pids()

                if discord_pids:
                    break

                time.sleep(
                    0.5
                )

            if not discord_pids:
                raise RuntimeError(
                    "Discord foi iniciado, mas nenhum "
                    "Discord.exe foi encontrado."
                )

            self.after(
                0,
                lambda pids=discord_pids:
                self.log(
                    f"💬 Discord PIDs detectados: {pids}"
                )
            )

            # ========================================================
            # 16. ANEXAR DISCORD AO ENGINE
            # ========================================================

            self.after(
                0,
                lambda:
                self.set_progress(
                    80,
                    "Aplicando isolamento VPN..."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🛡️ Associando Discord à VPN..."
                )
            )

            attach_method = getattr(
                vpn_engine,
                "attach_processes",
                None
            )

            if not callable(
                    attach_method
            ):
                raise RuntimeError(
                    "O engine App-VPN não possui "
                    "attach_processes()."
                )

            attach_result = attach_method(
                pids=discord_pids
            )

            if attach_result is False:
                raise RuntimeError(
                    "O engine App-VPN recusou "
                    "o isolamento do Discord."
                )

            self.after(
                0,
                lambda:
                self.log(
                    "🛡️ Discord associado à camada App-VPN."
                )
            )

            # ========================================================
            # 17. VERIFICAR ISOLAMENTO
            # ========================================================

            self.after(
                0,
                lambda:
                self.set_progress(
                    85,
                    "Verificando isolamento..."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🔍 Verificando isolamento do Discord..."
                )
            )

            verify_method = getattr(
                vpn_engine,
                "verify",
                None
            )

            if not callable(
                    verify_method
            ):
                raise RuntimeError(
                    "O engine App-VPN não possui "
                    "verify()."
                )

            verified = verify_method(
                pids=discord_pids
            )

            if verified is not True:
                raise RuntimeError(
                    "Não foi possível confirmar que "
                    "o Discord está isolado na VPN."
                )

            # ========================================================
            # 17.1 VERIFICAR CONEXÃO REAL DO DISCORD
            # ========================================================

            self.after(
                0,
                lambda:
                self.log(
                    "🌐 Aguardando conexão TCP real do Discord..."
                )
            )

            connection_deadline = time.time() + 20
            discord_connections = []

            while time.time() < connection_deadline:

                if self.operation_stop_event.is_set():
                    raise RuntimeError(
                        "Operação cancelada pelo usuário."
                    )

                if process.poll() is not None:
                    raise RuntimeError(
                        "A VPN caiu enquanto o Discord conectava."
                    )

                current_pids = get_discord_pids()

                if current_pids:
                    new_pids = [
                        pid
                        for pid in current_pids
                        if pid not in discord_pids
                    ]

                    if new_pids:
                        attach_method(
                            pids=new_pids
                        )
                        discord_pids = current_pids

                    discord_connections = (
                        get_discord_established_connections(
                            current_pids
                        )
                    )

                    if discord_connections:
                        break

                time.sleep(0.5)

            if not discord_connections:
                try:
                    engine_tail = SINGBOX_LOG_FILE.read_text(
                        encoding="utf-8",
                        errors="replace"
                    )[-2500:]
                except Exception:
                    engine_tail = ""

                raise RuntimeError(
                    "O Discord foi iniciado, mas não conseguiu "
                    "estabelecer conexão de rede pelo App-VPN.\n\n"
                    "Último log do engine:\n"
                    f"{engine_tail}"
                )

            first_connection = discord_connections[0]

            self.after(
                0,
                lambda c=first_connection:
                self.log(
                    "✅ Discord estabeleceu conexão: "
                    f"{c.get('RemoteAddress', '?')}:"
                    f"{c.get('RemotePort', '?')}"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "========================================"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "✅ ISOLAMENTO CONFIRMADO"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "💬 Discord → VPN"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🌐 Demais aplicações → WAN normal"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🔒 VPN permanecerá conectada."
                )
            )

            # ========================================================
            # 18. ESTABILIZAÇÃO DISCORD
            # ========================================================

            self.after(
                0,
                lambda:
                self.set_progress(
                    90,
                    "Discord conectado pela VPN..."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "⏳ Aguardando Discord estabilizar..."
                )
            )

            for remaining in range(
                    WAIT_DISCORD,
                    -1,
                    -1
            ):

                if self.operation_stop_event.is_set():
                    raise RuntimeError(
                        "Operação cancelada pelo usuário."
                    )

                # ----------------------------------------------------
                # verificar OpenVPN
                # ----------------------------------------------------

                if process.poll() is not None:
                    raise RuntimeError(
                        "A VPN caiu durante a estabilização "
                        "do Discord."
                    )

                # ----------------------------------------------------
                # verificar Discord
                # ----------------------------------------------------

                current_pids = get_discord_pids()

                if not current_pids:
                    raise RuntimeError(
                        "O Discord foi encerrado durante "
                        "a estabilização."
                    )

                # ----------------------------------------------------
                # proteger novos processos
                # ----------------------------------------------------

                if current_pids != discord_pids:

                    new_pids = [
                        pid
                        for pid in current_pids
                        if pid not in discord_pids
                    ]

                    if new_pids:
                        self.after(
                            0,
                            lambda pids=new_pids:
                            self.log(
                                f"💬 Novos processos Discord: {pids}"
                            )
                        )

                        attach_method(
                            pids=new_pids
                        )

                        discord_pids = current_pids

                # ----------------------------------------------------
                # LOG
                # ----------------------------------------------------

                self.after(
                    0,
                    lambda s=remaining:
                    self.log(
                        f"⏳ Discord/VPN estabilizando: "
                        f"{s}s"
                    )
                )

                # ----------------------------------------------------
                # PROGRESSO
                # ----------------------------------------------------

                elapsed = (
                        WAIT_DISCORD
                        -
                        remaining
                )

                progress = (
                        90
                        +
                        (
                                elapsed
                                /
                                max(
                                    WAIT_DISCORD,
                                    1
                                )
                        )
                        *
                        8
                )

                self.after(
                    0,
                    lambda p=progress:
                    self.set_progress(
                        p,
                        "Discord conectado pela VPN..."
                    )
                )

                if remaining > 0:
                    time.sleep(1)

            # ========================================================
            # 19. ESTADO FINAL
            # ========================================================

            self.after(
                0,
                lambda:
                self.log(
                    "========================================"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🎉 OPERAÇÃO CONCLUÍDA"
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "💬 Discord permanece aberto."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🔒 VPN permanece conectada."
                )
            )

            self.after(
                0,
                lambda:
                self.log(
                    "🌐 O restante do computador permanece "
                    "na conexão normal."
                )
            )

            self.after(
                0,
                self.show_completed
            )

            # ========================================================
            # SUCESSO
            # ========================================================

            vpn_connected = True

            # Não apagar o log em caso de sucesso.
            # O fluxo existente pode alterar isso conforme
            # a política de logs desejada.
            keep_log_file = False

        except Exception as e:

            error = str(e)

            keep_log_file = True

            self.after(
                0,
                lambda:
                self.log(
                    "========================================"
                )
            )

            self.after(
                0,
                lambda msg=error:
                self.log(
                    f"❌ ERRO: {msg}"
                )
            )

            # ========================================================
            # LIMPEZA ENGINE
            # ========================================================

            try:

                vpn_engine = getattr(
                    self,
                    "vpn_engine",
                    None
                )

                cleanup_method = getattr(
                    vpn_engine,
                    "cleanup",
                    None
                )

                if callable(
                        cleanup_method
                ):
                    cleanup_method()

                    self.after(
                        0,
                        lambda:
                        self.log(
                            "🧹 Engine App-VPN limpo."
                        )
                    )

            except Exception as cleanup_error:

                self.after(
                    0,
                    lambda e=cleanup_error:
                    self.log(
                        f"⚠️ Erro limpando App-VPN: {e}"
                    )
                )

            # ========================================================
            # ERRO → DESCONECTAR VPN
            # ========================================================

            if (
                process is not None
                and
                process.poll() is None
            ):

                self.after(
                    0,
                    lambda:
                    self.log(
                        "🔓 Falha detectada. "
                        "Desconectando VPN..."
                    )
                )

                try:
                    self.disconnect_vpn()
                except Exception:
                    pass

                vpn_connected = False

            self.operation_active = False

            # ========================================================
            # MOSTRAR ERRO
            # ========================================================

            self.after(
                0,
                lambda msg=error:
                mb.showerror(
                    "OpenDis",
                    (
                        "A operação não pôde ser concluída.\n\n"
                        f"{msg[:2000]}"
                    )
                )
            )

            self.after(
                0,
                self.reset_start_button
            )

        finally:

            # ========================================================
            # FECHAR HANDLE DO LOG
            # ========================================================

            try:

                if log_handle:
                    log_handle.flush()
                    log_handle.close()

            except Exception:
                pass

            # ========================================================
            # CREDENCIAL TEMPORÁRIA
            # ========================================================

            if credentials_file:

                try:

                    credentials_file.unlink(
                        missing_ok=True
                    )

                except Exception:
                    pass

            # ========================================================
            # PERFIL OPENVPN TEMPORÁRIO
            # ========================================================

            if runtime_profile:

                try:
                    runtime_profile.unlink(
                        missing_ok=True
                    )
                except Exception:
                    pass

            # ========================================================
            # LIMPAR LOG SE NÃO FOR PARA MANTER
            # ========================================================

            if (
                    not keep_log_file
                    and
                    getattr(
                        self,
                        "vpn_log_file",
                        None
                    )
            ):

                try:

                    self.vpn_log_file.unlink(
                        missing_ok=True
                    )

                except Exception:
                    pass


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

    def focus_opendis_after_discord(self):
        """
        Traz o OpenDis de volta para a frente após o intervalo
        configurado, sem encerrar ou alterar os processos de rede.
        """

        if self.shutdown_in_progress:
            return

        try:
            self.deiconify()
            self.lift()

            # Pulso curto de topmost ajuda o Windows a devolver o foco
            # depois que o Discord abriu e roubou a janela ativa.
            self.attributes(
                "-topmost",
                True
            )

            if os.name == "nt":
                try:
                    hwnd = int(
                        self.winfo_id()
                    )

                    # SW_RESTORE = 9
                    ctypes.windll.user32.ShowWindow(
                        hwnd,
                        9
                    )
                    ctypes.windll.user32.SetForegroundWindow(
                        hwnd
                    )
                except Exception:
                    pass

            self.focus_force()

            self.after(
                250,
                lambda:
                self.attributes(
                    "-topmost",
                    False
                )
            )

        except Exception:
            pass


    def show_completed(self):
        """
        Estado final ativo.

        A operação NÃO é encerrada aqui. O OpenDis permanece vivo,
        é minimizado e mantém OpenVPN + App-VPN ativos. Para voltar ao
        estado normal existe o botão FECHAR E ENCERRAR VPN.
        """

        self.operation_active = True

        try:
            self.activity_bar.stop()
        except Exception:
            pass

        self.set_progress(
            100,
            "Discord conectado pela VPN."
        )

        self.log(
            "🎉 Operação concluída com sucesso!"
        )
        self.log(
            "🔒 Discord permanece na VPN."
        )
        self.log(
            "🌐 Demais aplicações permanecem na conexão normal."
        )
        self.log(
            "🪟 OpenDis será minimizado."
        )
        self.log(
            "⛔ Restaure a janela e use FECHAR E ENCERRAR VPN "
            "para desfazer toda a operação."
        )

        self.final_status.configure(
            text="✅ CONCLUÍDO — Discord na VPN",
            text_color="#57F287"
        )

        self.start_btn.configure(
            state="disabled",
            text="✓ CONCLUÍDO",
            fg_color="#3ba55d",
            hover_color="#3ba55d"
        )

        try:
            if self.stop_vpn_btn:
                self.stop_vpn_btn.pack(
                    pady=(2, 5)
                )
        except Exception:
            pass

        self.after(
            1400,
            self.minimize_completed
        )

    def minimize_completed(self):
        """
        Minimiza a janela sem encerrar os processos de rede.
        """

        if (
            self.operation_active
            and
            not self.shutdown_in_progress
        ):
            try:
                self.iconify()
            except Exception:
                pass

    def on_window_close(self):
        """
        O X nunca deve abandonar uma VPN ativa sem limpeza.
        """

        if self.shutdown_in_progress:
            return

        engine_running = bool(
            getattr(
                self.vpn_engine,
                "running",
                False
            )
        )

        vpn_running = bool(
            self.vpn_process
            and
            self.vpn_process.poll() is None
        )

        if (
            self.operation_active
            or
            engine_running
            or
            vpn_running
        ):
            answer = mb.askyesno(
                "Encerrar OpenDis",
                (
                    "A VPN do Discord ainda está ativa.\n\n"
                    "Deseja fechar o OpenDis e encerrar a VPN, "
                    "removendo o OpenDisTun e voltando à conexão normal?"
                )
            )

            if answer:
                self.request_shutdown_and_exit()

            return

        self.stop_vpn_ping_monitor()
        self.destroy()

    def request_shutdown_and_exit(self):
        """
        Inicia a reversão completa sem bloquear a interface gráfica.
        """

        if self.shutdown_in_progress:
            return

        self.shutdown_in_progress = True
        self.operation_stop_event.set()

        try:
            self.deiconify()
            self.lift()
        except Exception:
            pass

        try:
            if self.stop_vpn_btn:
                self.stop_vpn_btn.configure(
                    state="disabled",
                    text="🔄 ENCERRANDO VPN..."
                )
        except Exception:
            pass

        try:
            self.start_btn.configure(
                state="disabled"
            )
        except Exception:
            pass

        try:
            self.final_status.configure(
                text="🔄 Restaurando conexão normal...",
                text_color="#cccccc"
            )
        except Exception:
            pass

        try:
            self.log(
                "========================================"
            )
            self.log(
                "⛔ Encerrando App-VPN e restaurando a rede..."
            )
        except Exception:
            pass

        threading.Thread(
            target=self._shutdown_and_exit_worker,
            daemon=True
        ).start()

    def _shutdown_and_exit_worker(self):
        """
        Ordem de reversão:
            1. encerra sing-box / OpenDisTun;
            2. encerra OpenVPN;
            3. limpa DNS;
            4. confirma retorno da WAN, quando possível;
            5. fecha o OpenDis.
        """

        errors = []

        try:
            engine_ok = self.vpn_engine.cleanup()

            # cleanup() pode retornar False quando algum detalhe do
            # processo demora a confirmar, mesmo depois de o Wintun já
            # ter sido realmente derrubado. Só tratar como falha de TUN
            # quando a interface OpenDisTun ainda estiver ATIVA. Se o
            # Windows apenas mantiver o dispositivo listado como Down,
            # o teardown já foi concluído e não mostramos falso positivo.
            if (
                not engine_ok
                and
                is_windows_adapter_active("OpenDisTun")
            ):
                errors.append(
                    "O App-VPN foi encerrado, mas o OpenDisTun ainda "
                    "permanece ativo no Windows."
                )

        except Exception as e:
            errors.append(
                f"Falha ao encerrar App-VPN: {e}"
            )

        try:
            vpn_ok = self.disconnect_vpn()

            if not vpn_ok:
                errors.append(
                    "O processo OpenVPN não confirmou encerramento."
                )

        except Exception as e:
            errors.append(
                f"Falha ao encerrar OpenVPN: {e}"
            )

        flush_windows_dns_cache()
        time.sleep(1.0)

        restored_ip = get_public_ip_retry(
            timeout=6,
            attempts=3,
            delay=0.8
        )

        if (
            restored_ip
            and
            self.current_public_ip
            and
            restored_ip != self.current_public_ip
        ):
            errors.append(
                "A VPN foi encerrada, mas o IP público ainda não "
                "voltou ao valor observado antes da operação."
            )

        self.operation_active = False

        self.after(
            0,
            lambda errs=errors,
                   ip=restored_ip:
            self._finish_shutdown_and_exit(
                errs,
                ip
            )
        )

    def _finish_shutdown_and_exit(
        self,
        errors,
        restored_ip
    ):
        """
        Finaliza a UI somente depois da limpeza de rede.
        """

        if restored_ip:
            try:
                self.log(
                    f"🌐 IP após encerramento: {restored_ip}"
                )
            except Exception:
                pass

        if errors:
            self.shutdown_in_progress = False

            try:
                self.final_status.configure(
                    text="⚠️ Verifique a restauração da rede",
                    text_color="#FFA500"
                )
            except Exception:
                pass

            try:
                if self.stop_vpn_btn:
                    self.stop_vpn_btn.configure(
                        state="normal",
                        text="⛔ TENTAR ENCERRAR NOVAMENTE"
                    )
            except Exception:
                pass

            mb.showwarning(
                "OpenDis",
                (
                    "A limpeza foi executada, mas uma verificação "
                    "não ficou 100% confirmada:\n\n"
                    +
                    "\n".join(
                        f"• {item}"
                        for item in errors
                    )
                )[:2500]
            )

            return

        try:
            self.log(
                "✅ OpenDisTun removido."
            )
            self.log(
                "✅ OpenVPN encerrado."
            )
            self.log(
                "✅ Conexão normal restaurada."
            )
        except Exception:
            pass

        self.destroy()



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