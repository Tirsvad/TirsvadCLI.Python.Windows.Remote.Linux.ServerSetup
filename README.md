[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]
<!-- REPLACE -->
<!-- Linux Server Setup -->
<!-- ServerSetup -->
<!-- TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup -->

<!-- PROJECT LOGO -->
<br />
<div align="center">
    <a href="https://github.com/https://github.com/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup">
        <img src="images/logo.png" alt="Logo" width="80" height="80">
    </a>
    <h3 align="center">Linux Server Setup</h3>
    <p align="center">
    <!-- PROJECT DESCRIPTION -->
    <br />
    <br />
    <!-- PROJECT SCREENSHOTS -->
    <!--
    <a href="https://github.com/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup/blob/main/images/screenshot01.png">
        <img src="images/screenshot01.png" alt="screenshot" width="120" height="120">
    </a>
    -->
    <br />
    <a href="https://github.com/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    ·
    <a href="https://github.com/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>

  </p>
</div>

# Linux Server Setup

This script can remte setup a linux server from Windows using powershell.

What it can do now

* Make SSH not to use password only keys.
* Setup firewall (nftables).

# Getting Started

## Prerequisites

You have python3 installed for windows.

## Download

To download source code from git hub we can oen a terminal.

```powershell
Invoke-WebRequest https://github.com/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup/archive/refs/heads/main.zip -OutFile ServerSetup.zip
Expand-Archive -Path ServerSetup.zip -DestinationPath .\
Get-Item "*ServerSetup-*" | Rename-Item -NewName "ServerSetup"
Set-Location .\ServerSetup\srv\ServerSetup
```

## Configure your server
In the folder custom_files you may find setting.json whre you configure your server

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any
contributions you make are greatly appreciated.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also
simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

Fork the Project

<ol>
    <li>Fork the Project</li>
    <li>Create your Feature Branch</li>
    <li>Commit your Changes</li>
    <li>Push to the Branch</li>
    <li>Open a Pull Request</li>
</ol>

Example

```bash
git checkout -b feature
git commit -m 'Add my feature enhance to project'
git push origin feature
```

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup?style=for-the-badge

[contributors-url]: https://github.com/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup/graphs/contributors

[forks-shield]: https://img.shields.io/github/forks/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup?style=for-the-badge

[forks-url]: https://github.com/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup/network/members

[stars-shield]: https://img.shields.io/github/stars/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup?style=for-the-badge

[stars-url]: https://github.com/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup/stargazers

[issues-shield]: https://img.shields.io/github/issues/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup?style=for-the-badge

[issues-url]: https://github.com/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup/issues

[license-shield]: https://img.shields.io/github/license/TirsvadCLI/Python.Windows.Remote.Linux.ServerSetup?style=for-the-badge

[license-url]: https://github.comTirsvadCLI/Python.Windows.Remote.Linux.ServerSetup/blob/master/LICENSE

[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555

[linkedin-url]: https://www.linkedin.com/in/jens-tirsvad-nielsen-13b795b9/
