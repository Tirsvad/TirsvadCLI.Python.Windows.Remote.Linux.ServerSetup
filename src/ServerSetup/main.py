"""Copyright (C) 2024 TirsvadCLI

This file is part of ServerSetup.

ServerSetup is free software; you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation; either version 2.1 of the License, or (at your option)
any later version.

ServerSetup is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License
along with ServerSetup; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA.
"""

import os
import sys
import json
import logging
import subprocess


from pathlib import Path
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import (
    AuthenticationException,
    NoValidConnectionsError,
)

from constants import (
    SETTINGS_FILE,
    INSTANCE_LOGGING_FILE,
    NFTABLE_FILE,
    SETTINGS_TEMPLATE_FILE,
    INSTANCE_NFTABLE_FILE,
    INSTANCE_PATH,
)

from models import Settings

from ansi_code import AnsiCode

if os.name == "nt":  # Only if we are running on Windows
    from ctypes import windll

    k = windll.kernel32
    k.SetConsoleMode(k.GetStdHandle(-11), 7)


class ServerSetup:
    """Server setup where we are on a windows client connected to a linux
    server. Then we do server configuration / setup

    Raises:
        OSError: _description_
        FileNotFoundError: _description_
        ConnectionError: _description_

    Returns:
        _type_: _description_
    """

    settings: Settings
    host_ssh_port: int
    logger: logging
    ssh_askpass_require: str
    ssh_askpass: str
    ssh_client: SSHClient | None = None

    def __init__(self) -> None:
        print("\nLinux Server Setup\n")

        if not os.path.isdir(INSTANCE_PATH):
            os.makedirs(INSTANCE_PATH)
            self.init_run = True

        self._init_logger()
        self.logger.info("Host setup starting")

        self._info_to_screen("Prepare custom files")
        if not os.path.isfile(SETTINGS_FILE):
            self.copy_settings_template()
        self._info_done_to_sreen()

        self._info_to_screen("Loading settings")
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            self.settings = Settings.from_dict(json.load(f))
        self.host_ssh_port = self.settings.sshd_config.port_before_setup
        self._info_done_to_sreen()

    def _init_logger(self):
        """Initialize logger"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:"
            "%(lineno)d] %(message)s",
            datefmt="%a, %d %b %Y %H:%M:%S",
        )
        fh = logging.FileHandler(
            INSTANCE_LOGGING_FILE, mode="w", encoding="utf-8"
        )
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        sh.setLevel(logging.WARNING)
        self.logger.addHandler(sh)

    def _info_to_screen(self, msg: str):
        print(f"[......] {msg}", end="")

    def _info_done_to_sreen(self):
        print(
            f"\r{AnsiCode.CURSOR.RIGHT}{AnsiCode.FG_COLOR.GREEN} done ",
            end=f"{AnsiCode.FG_COLOR.DEFAULT}\n",
        )

    def _info_failed_to_screen(self):
        subprocess.call("", shell=True)
        print(
            f"\r{AnsiCode.CURSOR.RIGHT}{AnsiCode.FG_COLOR.RED}" f"FAILED",
            end=f"{AnsiCode.FG_COLOR.DEFAULT}\n",
        )

    def copy_settings_template(self):
        """Copy settigns.json template to custom file folder.
        Then we exit script for user have to edit settigns.json.
        """
        with open(SETTINGS_TEMPLATE_FILE, "rb") as file:
            data = file.read()
        with open(SETTINGS_FILE, "wb") as file:
            file.write(data)
        self._info_failed_to_screen()
        print(
            f"\nWe didn't find {SETTINGS_FILE}.\n"
            "We created a new template you must edit\n"
            f"You must make changes to {SETTINGS_FILE}"
        )
        sys.exit(0)

    def run(self):
        """Setting up local client connetion and do setup for host"""
        self.sshkey_check()
        if self.connect_server() == "password":
            self.ssh_key_copy_to_host()
        self.os_update_upgrade()
        self.ssh_connection_make_secure()
        self.ssh_client.close()
        self.connect_server()  # Use of new port
        self.firewall_setup()
        self.apps_install()

    def sshkey_check(self):
        """Check if client have sshkey pair for secure connection else
        we create the sshkey pair
        """
        self._info_to_screen("Check for avaible pkey if none we create one")
        if not os.path.isfile(
            f"{Path.home()}{os.path.sep}.ssh{os.path.sep}id_rsa.pub"
        ):
            self.logger.debug("Create ssh connection: Create ssh key")
            cmd = [
                f"ssh-keygen -b 4096 -t rsa "
                f"-f {Path.home()}\\.ssh\\id_rsa -N '\"\"'"
            ]
            self.powershell(cmd)
        self._info_done_to_sreen()

    def connect_server(self) -> str:
        """Connect Server through ssh. Keep connection as self.ssh_client

        Raises:
            AuthenticationException: We could not authenticate user!

        Returns:
            str: returns login method password or key
        """
        self._info_to_screen("Connect server through ssh")
        self.ssh_client = SSHClient()
        self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        # First try to connect with key
        try:
            login_method = "key"
            self.ssh_client.connect(
                self.settings.host.ip_address,
                username=self.settings.host.admin_user,
                port=self.settings.sshd_config.Port,
            )

        except NoValidConnectionsError:
            # Try to connect with password
            try:
                login_method = "password"
                self.ssh_client.connect(
                    hostname=self.settings.host.ip_address,
                    port=self.settings.sshd_config.port_before_setup,
                    username=self.settings.host.admin_user,
                    password=self.settings.host.admin_password,
                )
            except AuthenticationException as exc:
                self._info_failed_to_screen()
                raise AuthenticationException() from exc
        else:
            self.host_ssh_port = self.settings.sshd_config.Port
        self._info_done_to_sreen()
        return login_method

    def ssh_key_copy_to_host(self):
        """Copy ssh key to server and restart sshd"""
        self._info_to_screen("Copy public ssh key to server")
        with open(Path.home() / ".ssh" / "id_rsa.pub", encoding="utf-8") as f:
            data = f.read()
        self.ssh_command(
            [
                f"echo '{data}' >> ~/.ssh/authorized_keys",
                "systemctl restart sshd",
            ]
        )
        self._info_done_to_sreen()

    def ssh_connection_make_secure(self):
        """Change sshd setting on host so it only accepts key as
        authentication. No password login
        """
        self._info_to_screen("Host: Securing ssh connection")
        for key, value in self.settings.sshd_config.__dict__.items():
            if not key == "port_before_setup":
                self.ssh_command(
                    [
                        str(
                            r'sed -i "s/#\?\('
                            + str(key)
                            + r"\s*\).*$/\1 "
                            + str(value)
                            + r'/" /etc/ssh/sshd_config'
                        )
                    ]
                )
        self.ssh_command(["systemctl restart ssh"])
        self._info_done_to_sreen()

    def firewall_setup(self):
        """Simple firewall setup from template.
        Adding sshd port.
        """
        self._info_to_screen("Host: Firewall setup")
        # create nftable file
        with open(NFTABLE_FILE, "r", encoding="utf-8") as f:
            data = f.read()
            data = data.replace(
                "%SSH_PORT%", str(self.settings.sshd_config.Port)
            )
            with open(
                INSTANCE_NFTABLE_FILE, "w", newline="\n", encoding="utf-8"
            ) as file:
                file.write(data)

        self.scp(INSTANCE_NFTABLE_FILE, "/etc/")

        self.ssh_command(["/usr/sbin/nft -f /etc/nftables.conf"])
        self.ssh_command(["systemctl enable nftables"])
        self.ssh_command(["systemctl start nftables"])
        self._info_done_to_sreen()

    def os_update_upgrade(self):
        """Update and upgrade host OS"""
        self._info_to_screen("Host: Update and upgrade software")
        self.ssh_command(["apt-get -qq update && apt-get -qq upgrade"])
        self._info_done_to_sreen()

    def apps_install(self):
        """Install application from settings file to host"""
        for app_install in self.settings.app_host:
            self._info_to_screen(f"Host: Install {app_install.name}")
            self.ssh_command([f"apt-get install -qq {app_install.name}"])
            self._info_done_to_sreen()
            if hasattr(self, f"app_{app_install.name}_setup"):
                func = getattr(self, f"app_{app_install.name}_setup")
                func()

    def app_nginx_setup(self):
        """Nginx settings.
        Add firewall rules.
        """
        self._info_to_screen("HOST: Nginx setup")
        cmds = [
            "systemctl start nginx",
            "systemctl enable nginx",
        ]
        for cmd in cmds:
            self.ssh_command([cmd])

        # Firewall
        with open(
            INSTANCE_NFTABLE_FILE, "r+", newline="\n", encoding="utf-8"
        ) as f:
            new_file_contents = ""
            for line in f.readlines():
                if "##WEBHOST##" in line:
                    new_file_contents += line.replace(
                        "##WEBHOST##",
                        'tcp dport 80 accept comment "accept http"',
                    )
                    new_file_contents += (
                        "tcp dport 443 accept comment" '"accept https"\n'
                    )
                else:
                    new_file_contents += line
            f.seek(0)
            f.truncate()
            f.write(new_file_contents)
        self.scp(INSTANCE_NFTABLE_FILE, "/etc/")

        self.ssh_command(["/usr/sbin/nft -f /etc/nftables.conf"])
        self._info_done_to_sreen()

    def powershell(
        self, cmds: list, check=True
    ) -> subprocess.CompletedProcess:
        """Shell script for windows

        Args:
            cmds (list): powershell commands

        Returns:
            subprocess.CompletedProcess: _description_
        """
        cmds_reformatted = [
            cmd + "; " for cmd in cmds if not cmd.endswith(";")
        ]
        cmds_reformatted.insert(0, "pwsh")
        cmds_reformatted.insert(1, "-Command")
        self.logger.info("powershell command: %s", " ".join(cmds_reformatted))
        result = subprocess.run(
            cmds_reformatted,
            encoding="utf-8",
            capture_output=True,
            text=True,
            check=check,
        )
        return result

    def ssh_command(self, cmds: list) -> any:
        """Ssh command to host

        Args:
            cmds (list): _description_

        Returns:
            any: _description_
        """
        for cmd in cmds:
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            self.logger.info(
                "ssh command: ssh %s@%s -p %s %s",
                self.settings.host.admin_user,
                self.settings.host.ip_address,
                self.host_ssh_port,
                cmd,
            )
            if not stdout.channel.recv_exit_status() == 0:
                self._info_failed_to_screen()
                print(f"ssh command failed with code {stderr}")
                sys.exit()
        stdin.close()
        stdout.close()
        stderr.close()

    def scp(self, src: str, dst: str):
        """Copy files to host

        Args:
            src (str): source file
            dst (str): dst file
        """
        self.powershell(
            [
                f"scp -P {str(self.settings.sshd_config.Port)} "
                f"{src} {self.settings.host.admin_user}"
                f"@{self.settings.host.ip_address}:{dst}"
            ]
        )


if __name__ == "__main__":
    app = ServerSetup()
    app.run()
