import pyxplora_api.pyxplora_api as PyXploraApi

def main():
    xplora = PyXploraApi("+49", "123456789", "ACCOUNT_PASSWORT", "de-DE", "Europe/Berlin")
    print(xplora.getUserName())

if __name__ == '__main__':
    main()