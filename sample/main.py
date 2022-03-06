from pyxplora_api import pyxplora_api as PXA


def main():
    countryCode = "+49"
    phoneNummer = "123456789"
    password = "ACCOUNT_PASSWORT"
    local = "de-DE"
    timeZone = "Europe/Berlin"

    xplora = PXA.PyXploraApi(countryCode, phoneNummer, password, local, timeZone)
    print(xplora.getUserName())


if __name__ == '__main__':
    main()
