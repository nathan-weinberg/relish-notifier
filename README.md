# relish-notifier

A Python app using Selenium that tells me when Relish is here without having to download another app or give them my phone number or whatever.

## Relish credentials

Credentials are stored in [keyring](https://github.com/jaraco/keyring) and can be set via the following:

```bash
$ python
Python 3.12.10 (main, Apr 22 2025, 00:00:00) [GCC 14.2.1 20240912 (Red Hat 14.2.1-3)] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import keyring
>>> keyring.set_password("relish-notifier", "EMAIL", "<your email>")
>>> keyring.set_password("relish-notifier", "PASSWORD", "<your password>")
>>> exit()
```
