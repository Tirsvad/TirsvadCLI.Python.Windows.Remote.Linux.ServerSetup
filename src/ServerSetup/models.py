"""
All models is defined here
"""

from dataclasses import dataclass
from dataclass_wizard import JSONWizard


@dataclass
class SettingsHost:
    """Host connection settings"""

    ip_address: str | None = None
    admin_user: str | None = None
    admin_password: str | None = None


@dataclass
class SettingsSshdConfig:
    """SSHD config settings"""

    port_before_setup: int = 22
    # pylint: disable=invalid-name
    Port: int = 10322  # noqa: C0103
    PermitRootLogin: str = "yes"
    PasswordAuthentication: str = "no"
    UsePAM: str = "no"
    # pylint: enable=invalid-name


@dataclass
class Settings(JSONWizard):
    """Server configure settings"""

    host: SettingsHost
    sshd_config: SettingsSshdConfig
