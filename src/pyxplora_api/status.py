from __future__ import annotations

from enum import Enum


class NormalStatus(Enum):
    ENABLE = "ENABLE"
    DISABLE = "DISABLE"
    UNKNOWN__ = "UNKNOWN__"


class WatchOnlineStatus(Enum):
    UNKNOWN = "UNKNOWN"
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    UNKNOWN__ = "UNKNOWN__"


class YesOrNo(Enum):
    YES = "YES"
    NO = "NO"
    UNKNOWN__ = "UNKNOWN__"


class VerificationType(Enum):
    REGIST = "REGIST"
    RESET = "RESET"
    UNKNOWN__ = "UNKNOWN__"


class Gender(Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    UNKNOWN = "UNKNOWN"
    NO_COMMENT = "NO_COMMENT"
    UNKNOWN__ = "UNKNOWN__"


class CoinHistoryType(Enum):
    CONV_STEP_TO_COIN = "CONV_STEP_TO_COIN"
    EXEC_CAMPAIGN = "EXEC_CAMPAIGN"
    USE_COIN_IN_CAMPAIGN = "USE_COIN_IN_CAMPAIGN"
    ORDER_PRODUCT = "ORDER_PRODUCT"
    COIN_SEND = "COIN_SEND"
    COIN_RECV = "COIN_RECV"
    USED_VOUCHER_REDEEM = "USED_VOUCHER_REDEEM"
    UNKNOWN__ = "UNKNOWN__"


class ChatEmoticonType(Enum):
    M1001 = "M1001"
    M1002 = "M1002"
    M1003 = "M1003"
    M1004 = "M1004"
    M1005 = "M1005"
    M1006 = "M1006"
    M1007 = "M1007"
    M1008 = "M1008"
    M1009 = "M1009"
    M1010 = "M1010"
    M1011 = "M1011"
    M1012 = "M1012"
    M1013 = "M1013"
    M1014 = "M1014"
    M1015 = "M1015"
    M1016 = "M1016"
    M1017 = "M1017"
    M1018 = "M1018"
    M1019 = "M1019"
    M1020 = "M1020"
    M1021 = "M1021"
    M1022 = "M1022"
    M1023 = "M1023"
    M1024 = "M1024"
    UNKNOWN__ = "UNKNOWN__"


class Emoticon(Enum):
    M1001 = "1001"
    M1002 = "1002"
    M1003 = "1003"
    M1004 = "1004"
    M1005 = "1005"
    M1006 = "1006"
    M1007 = "1007"
    M1008 = "1008"
    M1009 = "1009"
    M1010 = "1010"
    M1011 = "1011"
    M1012 = "1012"
    M1013 = "1013"
    M1014 = "1014"
    M1015 = "1015"
    M1016 = "1016"
    M1017 = "1017"
    M1018 = "1018"
    M1019 = "1019"
    M1020 = "1020"
    M1021 = "1021"
    M1022 = "1022"
    M1023 = "1023"
    M1024 = "1024"
    UNKNOWN__ = "UNKNOWN__"


class ClientType(Enum):
    WEB = "WEB"
    APP = "APP"
    UNKNOWN__ = "UNKNOWN__"


class EmailAndPhoneVerificationType(Enum):
    REGIST = "REGIST"
    RESET = "RESET"
    RESEND = "RESEND"
    SSO = "SSO"
    UNKNOWN__ = "UNKNOWN__"


class LocationType(Enum):
    WIFI = "WIFI"
    CELL = "CELL"
    GPS = "GPS"
    UNKNOWN = "UNKNOWN"
    UNKNOWN__ = "UNKNOWN__"


class UserContactType(Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    UNKNOWN__ = "UNKNOWN__"


class EmailAndPhoneVerificationTypeV2(Enum):
    REGIST = "REGIST"
    RESET = "RESET"
    RESEND = "RESEND"
    UPDATE = "UPDATE"
    UNKNOWN__ = "UNKNOWN__"


class ChatType(Enum):
    UNDEFINED = "UNDEFINED"
    EMOTICON = "EMOTICON"
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VOICE = "VOICE"
    MP3 = "MP3"
    SHORT_VIDEO = "SHORT_VIDEO"
    CALL_LOG = "CALL_LOG"
    SOS = "SOS"
    LEAVE_SAFE_ZONE = "LEAVE_SAFE_ZONE"
    ARRIVE_SAFE_ZONE = "ARRIVE_SAFE_ZONE"
    LOW_POWER = "LOW_POWER"
    POWER_ON = "POWER_ON"
    POWER_OFF = "POWER_OFF"
    UNKNOWN__ = "UNKNOWN__"
