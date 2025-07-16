# relish-notifier

A Python app that uses Selenium to tell you when your Relish order has arrived.

## Usage

```
usage: notifier.py [-h] [--headless] [--no-headless] [--extensions]
                   [--no-extensions] [--page-timeout PAGE_TIMEOUT]
                   [--check-interval INTERVAL] [--once] [--verbose]
                   [--command COMMAND]

options:
  -h, --help            show this help message and exit
  --headless            Run Chrome in headless mode (default)
  --no-headless         Do not run Chrome in headless mode (show browser
                        window)
  --extensions          Enable browser extensions
  --no-extensions       Disable browser extensions
  --page-timeout, -t PAGE_TIMEOUT
                        Set page timeout in seconds
  --check-interval, -i INTERVAL
                        How often to check for delivery
  --once                Check once and exit
  --verbose, -v
  --command, -c COMMAND
                        Run this command when your order has arrived
```

## Relish credentials

Credentials are stored in the system keyring and can be set via the following:

```bash
$ python
Python 3.12.10 (main, Apr 22 2025, 00:00:00) [GCC 14.2.1 20240912 (Red Hat 14.2.1-3)] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import keyring
>>> keyring.set_password("relish-notifier", "EMAIL", "<your email>")
>>> keyring.set_password("relish-notifier", "PASSWORD", "<your password>")
>>> exit()
```
