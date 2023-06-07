from pyxplora_api.pyxplora_api import PyXploraApi


def main():
    countryCode: str = "+49"
    phoneNummer: str = "123456789"
    password: str = "ACCOUNT_PASSWORT"
    local: str = "de-DE"
    timeZone: str = "Europe/Berlin"
    childPhoneNumber: list[str] = []
    wuid: list[str] = []
    email: str = "your@mail.local"

    xplora = PyXploraApi(
        countrycode=countryCode,
        phoneNumber=phoneNummer,
        password=password,
        userLang=local,
        timeZone=timeZone,
        childPhoneNumber=childPhoneNumber,
        wuid=wuid,
        email=email,
    )
    xplora.init()
    print(xplora.getUserName())


if __name__ == "__main__":
    main()
