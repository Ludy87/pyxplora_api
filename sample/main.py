import pyxplora_api as PXA

def main():
    xplora = PXA.PyXploraApi("+49", "123456789", "ACCOUNT_PASSWORT", "de-DE", "Europe/Berlin")
    print(xplora.getUserName())

if __name__ == '__main__':
    main()