#!/usr/bin/env python3
"""
OpenDis
OpenVPN Community + Discord

Fluxo:
1. Detecta OpenVPN Community
2. Detecta Discord
3. Lista arquivos .ovpn em OpenDis/VPN
4. Analisa necessidade de credenciais
5. Conecta via openvpn.exe
6. Confirma túnel/IP
7. Abre Discord
8. Aguarda Discord iniciar
9. Desconecta OpenVPN
10. Mostra CONCLUÍDO
"""

import os
import sys
import re
import time
import json
import shutil
import signal
import socket
import threading
import subprocess
import webbrowser
from pathlib import Path
from urllib.request import urlopen

import customtkinter as ctk
import tkinter.messagebox as mb
from tkinter import filedialog


# ============================================================
# CONFIGURAÇÃO
# ============================================================

APP_NAME = "OpenDis"

WAIT_VPN_TIMEOUT = 60
WAIT_DISCORD = 10
IP_CHECK_TIMEOUT = 30

OPENVPN_WINGET_ID = "OpenVPNTechnologies.OpenVPN"

DISCORD_WINGET_ID = "Discord.Discord"

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
# APP
# ============================================================

class OpenDisApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        self.title(
            "OpenDis - Discord Unlock"
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

        self.ovpn_var = None
        self.username_var = None
        self.password_var = None

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
            text="powered by Magnatatile",
            font=ctk.CTkFont(size=10),
            text_color="#666675"
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
            self.check_requirements
        )


    # ========================================================
    # REQUISITOS
    # ========================================================

    def check_requirements(self):

        self.progress.stop()

        self.progress.pack_forget()

        openvpn = find_openvpn_executable()

        if not openvpn:

            self.show_missing_openvpn()

            return

        self.status_label.configure(
            text="✅ OpenVPN encontrado"
        )

        discord = find_discord_executable()

        if not discord:

            self.after(
                800,
                self.show_missing_discord
            )

            return

        self.status_label.configure(
            text="✅ OpenVPN + Discord detectados"
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
            text="📥 OpenVPN não encontrado",
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
                text="✅ OpenVPN instalado!"
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
            text="📥 Discord não encontrado",
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
                text="✅ Discord instalado!"
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
            pady=(45, 5)
        )

        ctk.CTkLabel(
            self.container,
            text="Selecione o perfil .ovpn",
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#a0a0b0"
        ).pack(
            pady=(5, 15)
        )

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
                height=40
            )

            self.ovpn_menu.pack(
                pady=10
            )

        else:

            self.ovpn_var.set("")

            ctk.CTkLabel(
                self.container,
                text=(
                    "Nenhum .ovpn encontrado em:\n"
                    f"{VPN_DIR}"
                ),
                font=ctk.CTkFont(
                    size=12
                ),
                text_color="#ffb347",
                justify="center"
            ).pack(
                pady=10
            )


        ctk.CTkButton(
            self.container,
            text="📂 Adicionar / selecionar .ovpn",
            command=self.import_profile,
            fg_color="#2f3136",
            hover_color="#40444b",
            height=40
        ).pack(
            pady=10
        )

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

        self.continue_btn = ctk.CTkButton(
            self.container,
            text="➡️ CONTINUAR",
            command=self.profile_selected,
            fg_color="#5865F2",
            hover_color="#4752C4",
            height=48,
            font=ctk.CTkFont(
                size=16,
                weight="bold"
            ),
            corner_radius=25
        )

        self.continue_btn.pack(
            pady=20
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
            pady=(55, 10)
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

        ctk.CTkLabel(
            self.container,
            text="Usuário",
            font=ctk.CTkFont(
                size=12
            ),
            text_color="#cccccc"
        ).pack(
            pady=(10, 3)
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

        ctk.CTkLabel(
            self.container,
            text="Senha",
            font=ctk.CTkFont(
                size=12
            ),
            text_color="#cccccc"
        ).pack(
            pady=(10, 3)
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
            pady=25
        )


    def credentials_submitted(self):

        username = self.username_entry.get().strip()

        password = self.password_entry.get()

        if not username or not password:

            mb.showwarning(
                "Credenciais",
                "Informe usuário e senha."
            )

            return

        self.ovpn_username = username
        self.ovpn_password = password

        self.show_connect_screen()


    # ========================================================
    # TELA DE EXECUÇÃO
    # ========================================================

    def show_connect_screen(self):

        self.clear()

        ctk.CTkLabel(
            self.container,
            text="🚀 Pronto para desbloquear!",
            font=ctk.CTkFont(
                size=24,
                weight="bold"
            ),
            text_color="#cccccc"
        ).pack(
            pady=(55, 5)
        )

        ctk.CTkLabel(
            self.container,
            text=(
                "1️- Conectar VPN\n"
                "2️- Confirmar rede\n"
                "3️- Abrir Discord\n"
                "4️- Aguardar Discord\n"
                "5️- Desconectar VPN\n"
            ) ,
            font=ctk.CTkFont(
                size=13
            ),
            text_color="#a0a0b0",
            justify="center"
        ).pack(
            pady=(10, 20)
        )

        self.log_text = ctk.CTkTextbox(
            self.container,
            width=380,
            height=150,
            font=ctk.CTkFont(
                size=12
            ),
            fg_color="#12121a",
            text_color="#8e9297"
        )

        self.log_text.pack(
            pady=10
        )

        self.log_text.insert(
            "1.0",
            "[] Aguardando início...\n"
        )

        self.log_text.configure(
            state="disabled"
        )

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
            pady=12
        )

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
            text="🔄 Executando..."
        )

        # ========================================================
        # EXECUÇÃO
        # ========================================================

        threading.Thread(
            target=self._run_unlock,
            daemon=True
        ).start()


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
            confirmar desconexão
            mostrar CONCLUÍDO

        O OpenVPN é executado de forma totalmente invisível.
        Nenhuma janela CMD é exibida.
        """

        vpn_connected = False
        credentials_file = None
        process = None

        try:

            # ====================================================
            # 1. LOCALIZAR OPENVPN
            # ====================================================

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
                    f"📄 Perfil: {p}"
                )
            )

            # ====================================================
            # 4. IP INICIAL
            # ====================================================

            self.after(
                0,
                lambda:
                self.log(
                    "🌐 Verificando IP atual..."
                )
            )

            self.current_public_ip = get_public_ip()

            if self.current_public_ip:

                self.after(
                    0,
                    lambda ip=self.current_public_ip:
                    self.log(
                        f"🌐 IP atual: {ip}"
                    )
                )

            else:

                self.after(
                    0,
                    lambda:
                    self.log(
                        "⚠️ Não foi possível obter IP inicial."
                    )
                )

            # ====================================================
            # 5. CRIAR LOG
            # ====================================================

            self.vpn_log_file = create_log_file()

            self.after(
                0,
                lambda p=self.vpn_log_file:
                self.log(
                    f"📝 Log: {p.name}"
                )
            )

            # ====================================================
            # 6. CREDENCIAIS
            # ====================================================

            command = [
                openvpn,
                "--config",
                str(profile),

                # MUITO IMPORTANTE:
                # teu perfil funciona com DCO desativado.
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

                # ------------------------------------------------
                # Arquivo temporário de credenciais
                # ------------------------------------------------

                credentials_file = (
                        LOG_DIR /
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
            # 7. PREPARAR PROCESSO
            # ====================================================

            creation_flags = 0

            startupinfo = None

            if os.name == "nt":
                # -----------------------------------------------
                # NÃO abrir janela CMD
                # -----------------------------------------------

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
            # 8. ABRIR LOG
            # ====================================================

            log_handle = open(
                self.vpn_log_file,
                "a",
                encoding="utf-8",
                errors="replace"
            )

            # ====================================================
            # 9. INICIAR OPENVPN
            # ====================================================

            self.after(
                0,
                lambda:
                self.log(
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
            # 10. AGUARDAR VPN
            # ====================================================

            self.after(
                0,
                lambda:
                self.log(
                    "⏳ Aguardando conexão VPN..."
                )
            )

            vpn_deadline = (
                    time.time() +
                    WAIT_VPN_TIMEOUT
            )

            connection_confirmed = False

            while time.time() < vpn_deadline:

                # -----------------------------------------------
                # Processo morreu?
                # -----------------------------------------------

                if process.poll() is not None:
                    raise RuntimeError(
                        "OpenVPN encerrou antes de concluir a conexão."
                    )

                # -----------------------------------------------
                # Ler log
                # -----------------------------------------------

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

                # -----------------------------------------------
                # Conexão estabelecida
                # -----------------------------------------------

                if (
                        "Initialization Sequence Completed"
                        in log_content
                ):
                    connection_confirmed = True
                    break

                # -----------------------------------------------
                # Erros fatais conhecidos
                # -----------------------------------------------

                fatal_patterns = [
                    "Exiting due to fatal error",
                    "AUTH_FAILED",
                    "TLS Error",
                    "Cannot open TUN/TAP",
                    "All TAP-Windows adapters",
                    "Options error:",
                    "Connection failed",
                ]

                fatal_error = None

                for pattern in fatal_patterns:

                    if pattern.lower() in log_content.lower():
                        fatal_error = pattern
                        break

                if fatal_error:
                    raise RuntimeError(
                        f"OpenVPN falhou: {fatal_error}"
                    )

                time.sleep(0.25)

            if not connection_confirmed:
                raise RuntimeError(
                    "Tempo limite aguardando conexão VPN."
                )

            # ====================================================
            # 11. VPN CONECTADA
            # ====================================================

            vpn_connected = True

            self.after(
                0,
                lambda:
                self.log(
                    "✅ OpenVPN conectado."
                )
            )

            # ====================================================
            # 12. CONFIRMAR MUDANÇA DE IP
            # ====================================================

            self.after(
                0,
                lambda:
                self.log(
                    "🌐 Confirmando alteração de rede..."
                )
            )

            new_ip = None

            ip_deadline = (
                    time.time() +
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

                time.sleep(1)

            if new_ip:

                self.after(
                    0,
                    lambda ip=new_ip:
                    self.log(
                        f"🌐 IP atual: {ip}"
                    )
                )

                if (
                        self.current_public_ip
                        and
                        new_ip == self.current_public_ip
                ):

                    self.after(
                        0,
                        lambda:
                        self.log(
                            "⚠️ IP não mudou, mas o túnel VPN está ativo."
                        )
                    )

                else:

                    self.after(
                        0,
                        lambda:
                        self.log(
                            "✅ Rede VPN confirmada."
                        )
                    )

            else:

                self.after(
                    0,
                    lambda:
                    self.log(
                        "⚠️ Não foi possível confirmar o IP externo."
                    )
                )

            # ====================================================
            # 13. ABRIR DISCORD
            # ====================================================

            self.after(
                0,
                lambda:
                self.log(
                    "💬 Abrindo Discord..."
                )
            )

            discord_process = subprocess.Popen(
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
            # 14. CONFIRMAR DISCORD
            # ====================================================

            discord_deadline = (
                    time.time() +
                    20
            )

            discord_found = False

            while time.time() < discord_deadline:

                try:

                    result = subprocess.run(
                        [
                            "tasklist",
                            "/FI",
                            "IMAGENAME eq Discord.exe"
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=(
                            subprocess.CREATE_NO_WINDOW
                            if os.name == "nt"
                            else 0
                        )
                    )

                    if (
                            "Discord.exe"
                            in result.stdout
                    ):
                        discord_found = True
                        break

                except Exception:
                    pass

                time.sleep(0.5)

            if not discord_found:
                raise RuntimeError(
                    "Discord não iniciou corretamente."
                )

            self.after(
                0,
                lambda:
                self.log(
                    "✅ Discord aberto."
                )
            )

            # ====================================================
            # 15. ESPERAR 5 SEGUNDOS
            # ====================================================

            self.after(
                0,
                lambda:
                self.log(
                    "⏳ Aguardando 5 segundos..."
                )
            )

            time.sleep(
                WAIT_DISCORD
            )

            # ====================================================
            # 16. DESCONECTAR VPN
            # ====================================================

            self.after(
                0,
                lambda:
                self.log(
                    "🔌 Desconectando VPN..."
                )
            )

            disconnected = self.disconnect_vpn()

            vpn_connected = False

            if not disconnected:
                raise RuntimeError(
                    "Não foi possível confirmar a desconexão da VPN."
                )

            # ====================================================
            # 17. CONFIRMAÇÃO
            # ====================================================

            self.after(
                0,
                lambda:
                self.log(
                    "✅ VPN desconectada."
                )
            )

            # ====================================================
            # 18. FINAL
            # ====================================================

            self.after(
                0,
                self.show_completed
            )


        except Exception as e:

            error_text = str(e)

            self.after(
                0,
                lambda msg=error_text:
                self.log(
                    f"❌ {msg[:300]}"
                )
            )

            # ----------------------------------------------------
            # SEMPRE limpar VPN
            # ----------------------------------------------------

            if vpn_connected or getattr(
                    self,
                    "vpn_process",
                    None
            ):

                self.after(
                    0,
                    lambda:
                    self.log(
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
            # FECHAR HANDLE DO LOG
            # ====================================================

            try:
                log_handle.close()
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

                # O processo foi criado com
                # CREATE_NEW_PROCESS_GROUP.
                #
                # CTRL_BREAK permite que o OpenVPN faça seu
                # encerramento normal e remova TAP/DCO/WFP.

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

        self.log(
            "🎉 Operação concluída com sucesso!"
        )

        self.final_status.configure(
            text="✅ CONCLUÍDO",
            text_color="#57F287"
        )

        self.start_btn.configure(
            state="normal",
            text="✓ CONCLUÍDO",
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

        # ----------------------------------------------------
        # A nova instância elevada foi iniciada.
        #
        # Esta instância NÃO deve criar a GUI.
        # ----------------------------------------------------

        sys.exit(0)

    # ========================================================
    # JÁ ESTÁ ELEVADO
    # ========================================================

    app = OpenDisApp()

    app.mainloop()