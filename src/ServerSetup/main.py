"""Server setup where we are on windows and doing linux server setup

Raises:
    OSError: Client is not on a compatible OS
    ConnectionError: When we cannot connect server

Returns:
    _type_: _description_
"""

import os
import sys
import json
import logging
import subprocess
import socket
from pathlib import Path

from constants import INIT_DONE_FILE
from constants import INSTANCE_LOGGING_FILE
from constants import SETTINGS_FILE
from constants import SSH_ASKPASS_FILE
from constants import NFTABLE_FILE
from constants import SETTINGS_TEMPLATE_FILE
from constants import INSTANCE_NFTABLE_FILE

from constants import INSTANCE_PATH

from models import Settings


sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")


class Setup:
    """Server setup where we are on windows and doing linux server setup

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

    def __init__(self) -> None:
        if not os.path.isdir(INSTANCE_PATH):
            os.makedirs(INSTANCE_PATH)
        # else:
        #     for i in os.listdir(INSTANCE_PATH):
        #         os.remove(rf"{INSTANCE_PATH}\{i}")

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
        self.logger.addHandler(sh)

        self.logger.info("Host setup starting")
        if not os.name == "nt":
            raise OSError(f"OS {os.name} is not supported")

        if not os.path.isfile(INIT_DONE_FILE) or not os.path.isfile(
            SETTINGS_FILE
        ):
            with open(INIT_DONE_FILE, "w", encoding="utf-8") as file:
                pass
            with open(SETTINGS_TEMPLATE_FILE, "rb") as file:
                data = file.read()
            with open(SETTINGS_FILE, "wb") as file:
                file.write(data)
            print(
                f"We didn't find {SETTINGS_FILE}.\n"
                "We created a new template you can edit\n"
                f"You must make changes to {SETTINGS_FILE}"
            )
            sys.exit(0)

        with open(SETTINGS_FILE, encoding="utf-8") as f:
            self.settings = Settings(**json.load(f))

        powershell_path = self.powershell(
            ["(get-command pwsh.exe).Path"]
        ).stdout.strip("\n")

        # prepare for ssh with password
        self.ssh_askpass = (
            f'$Env:SSH_ASKPASS="{powershell_path} -noLogo '
            f'-ExecutionPolicy unrestricted -file {SSH_ASKPASS_FILE}"'
        )
        self.ssh_askpass_require = '$Env:SSH_ASKPASS_REQUIRE="force"'

    def run(self):
        """Setting up local client connetion and do setup for host"""
        self.sshkey_check()
        self.host_ssh_port = self.ssh_avaible_check()
        if (
            self.host_ssh_port
            == self.settings.sshd_config["port_before_setup"]
        ):
            if not self.ssh_connection_with_key_try():
                self.ssh_key_copy_to_host()
            self.os_update_upgrade()
            self.ssh_connection_make_secure()
        self.host_ssh_port = self.settings.sshd_config["Port"]
        self.firewall_setup()
        self.apps_install()

    def sshkey_check(self):
        """Check if client have sshkey pair for secure connection else
        we create the sshkey pair
        """
        if not os.path.isfile(
            f"{Path.home()}{os.path.sep}.ssh{os.path.sep}id_rsa.pub"
        ):
            self.logger.debug("Create ssh connection: Create ssh key")
            cmd = [
                f"ssh-keygen -b 4096 -t rsa "
                f"-f {Path.home()}\\.ssh\\id_rsa -N '\"\"'"
            ]
            self.powershell(cmd)

    def ssh_avaible_check(self) -> int:
        """Return the first avaible port of
        Port before setup or Port efter setup

        Returns:
            int: Avaible port
        """
        if self.port_check(
            (

                self.settings.host["ip_address"],
                self.settings.sshd_config["port_before_setup"]

            )
        ):
            return self.settings.sshd_config["port_before_setup"]
        if self.port_check(
            (
                self.settings.host["ip_address"],
                self.settings.sshd_config["Port"]
            )
        ):
            return self.settings.sshd_config["Port"]
        self.logger.fatal("Can't connect host")
        raise ConnectionError()

    @staticmethod
    def port_check(ip_port: tuple) -> bool:
        """Check if port is avaible

        Args:
            ip_port (tuple): _description_

        Returns:
            bool: True if port is avaible
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        return s.connect_ex(ip_port) == 0

    def ssh_connection_with_key_try(self):

        with open(SSH_ASKPASS_FILE, "w", encoding="utf-8") as f:
            f.write(f'Write-Output "{self.settings.host["admin_password"]}"')

        # Can we login with public key

        test = self.powershell(
            [
                "ssh "
                # "-o PubkeyAuthentication=yes "
                "-o BatchMode=yes "
                "-o StrictHostKeyChecking=no "
                "-o ConnectTimeout=5 "
                f"{self.settings.host['admin_user']}@"
                f"{self.settings.host['ip_address']} "
                f"-p {self.host_ssh_port} "
                "exit"
            ],
            check=False,
        )
        if test.returncode:
            self.logger.info("Can't use ssh key for login")
            return False
        else:
            return True

    def ssh_key_copy_to_host(self):
        self.logger.info("Create ssh connection: Copy ssh key to host")
        # params = "-o BatchMode=yes"
        cmds = [
            f"{self.ssh_askpass_require}",
            f"{self.ssh_askpass}",
            f"cat {Path.home()}\\.ssh\\id_rsa.pub | "
            f"ssh {self.settings.host['admin_user']}@"
            f"{self.settings.host['ip_address']} "
            f"-p {self.settings.sshd_config['port_before_setup']} "
            f"'cat >> ~/.ssh/authorized_keys'",
        ]
        self.powershell(cmds)

    def ssh_connection_make_secure(self):
        self.logger.info("Host : Securing ssh connection")
        for key, value in self.settings.sshd_config.items():
            if not key == "port_before_setup":
                # cmd = r"pwsh -Command ssh root@161.97.108.95 -p 22
                # 'sed -i '\"'s/#\?\(UsePAM\s*\).*$/\1 no/'\"'
                # /etc/ssh/sshd_config'"
                cmd = (
                    r"pwsh -Command ssh "
                    # "ssh "
                    + self.settings.host["admin_user"]
                    + r"@"
                    + self.settings.host["ip_address"]
                    + r" -p "
                    + str(self.host_ssh_port)
                    + r" 'sed -i '\"'s/#\?\("
                    + key
                    + r"\s*\).*$/\1 "
                    + str(value)
                    + r"/'\"' /etc/ssh/sshd_config'"
                )
                # self.powershell([cmd]) # changing the script to not be valid!
                subprocess.run(cmd, check=False)
        cmd = ["systemctl restart ssh"]
        self.ssh_commands(cmd)

    def firewall_setup(self):
        self.logger.info("Host : Firewall setup")
        # create nftable file
        with open(NFTABLE_FILE, "r", encoding="utf-8") as f:
            data = f.read()
            data = data.replace(
                "%SSH_PORT%", str(self.settings.sshd_config["Port"])
            )
            with open(
                INSTANCE_NFTABLE_FILE, "w", newline="\n", encoding="utf-8"
            ) as file:
                file.write(data)

        self.scp(INSTANCE_NFTABLE_FILE, "/etc/")

        self.ssh_commands(["/usr/sbin/nft -f /etc/nftables.conf"])
        self.ssh_commands(["systemctl enable nftables"])
        self.ssh_commands(["systemctl start nftables"])

    def os_update_upgrade(self):
        self.logger.info("Host : Update and upgrade software")
        self.ssh_commands(["apt-get -qq update && apt-get -qq upgrade"])

    def apps_install(self):
        for app_install in self.settings.app_host:
            self.logger.info("Host : App install %s", app_install["name"])
            r = self.ssh_commands(
                                [f"apt-get install -qq {app_install["name"]}"],
                                check=False)
            if r.returncode:
                print(f"app not installed {app_install["name"]} - {r.stderr}")
            if hasattr(self, f"{app_install['name']}_setup"):
                print(f"{app_install['name']}_setup")
            if hasattr(self, f"{app_install['name']}_setup"):
                func = getattr(self, f"{app_install['name']}_setup")
                func()

    def nginx_setup(self):
        self.logger.info("HOST: Nginx : Setup")
        cmds = [
            "systemctl start nginx",
            "systemctl enable nginx",
        ]
        for cmd in cmds:
            self.ssh_commands([cmd])

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
                        "tcp dport 443 accept comment" '"accept https"'
                    )
                else:
                    new_file_contents += line
            f.seek(0)
            f.truncate()
            f.write(new_file_contents)
        self.scp(INSTANCE_NFTABLE_FILE, "/etc/")

        self.ssh_commands(["/usr/sbin/nft -f /etc/nftables.conf"])

    @staticmethod
    def powershell(cmds: list, check=True) -> subprocess.CompletedProcess:
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
        print(f"{' '.join(cmds_reformatted)}")
        result = subprocess.run(
            cmds_reformatted,
            encoding="utf-8",
            capture_output=True,
            text=True,
            check=check,
        )
        return result

    def ssh_commands(
            self, cmds: list, check=True) -> subprocess.CompletedProcess:
        cmds_reformatted = [cmd + ";" for cmd in cmds if not cmd.endswith(";")]
        ssh_cmd_list = [
            f"ssh {self.settings.host['admin_user']}@"
            f"{self.settings.host['ip_address']} -p {self.host_ssh_port} "
            + r'"DEBIAN_FRONTEND=noninteractive;'
            + " ".join(cmds_reformatted)
            + r'"'
        ]

        return self.powershell(ssh_cmd_list, check=check)

    def scp(self, src: str, dst: str):
        self.powershell([
            f"scp -P {str(self.settings.sshd_config['Port'])} "
            f"{src} {self.settings.host['admin_user']}"
            f"@{self.settings.host['ip_address']}:{dst}"
        ])


if __name__ == "__main__":
    app = Setup()
    app.run()
