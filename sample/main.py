from pyxplora_api import pyxplora_api as PXA


def main():
    countryCode = "+49"
    phoneNummer = "123456789"
    password = "ACCOUNT_PASSWORT"
    local = "de-DE"
    timeZone = "Europe/Berlin"
    childPhoneNumber = []

    xplora = PXA.PyXploraApi(
        countrycode=countryCode,
        phoneNumber=phoneNummer,
        password=password,
        userLang=local,
        timeZone=timeZone,
        childPhoneNumber=childPhoneNumber,
    )
    xplora.init()
    print(xplora.getUserName())


if __name__ == "__main__":
    main()
