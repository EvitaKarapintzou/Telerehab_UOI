For windows PC with Windows Subsystem for Linux (WSL)<br />

On VSCode you can connect to WSL using `Remote-Host`.<br />

Download and install [usbipd-win](https://github.com/dorssel/usbipd-win/releases) <br />

Description:<br />
  Shares locally connected USB devices to other machines, including Hyper-V guests and WSL 2.<br />

Usage:<br />
  usbipd [command] [options]<br />

Commands:<br />
  List USB devices <br />
  `usbipd list` <br />

  Bind device <br />
  `usbipd bind --busid <busid>` <br />

  Attach a USB device to a client <br />
  `usbipd attach --wsl --busid <busid>` <br />

  Detach a USB device from a client <br />
  `usbipd detach --busid <busid>` <br />

  Unbind device<br />
  `usbipd unbind --busid <busid>` <br />

Application entry point is `main.py` <br />

Sensor values vary from 0 to 4095.