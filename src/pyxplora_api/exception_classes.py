from __future__ import annotations

from enum import Enum


class ErrorMSG(Enum):
    SERVER_ERR = "Cannot connect to the server."
    LOGIN_ERR = "Login to Xplora® API failed. Check your input!\n{}"
    PHONE_MAIL_ERR = "Phone Number or Email address not exist"


class Error(Exception):
    pass


class NoAdminError(Error):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "no Admin"


class ChildNoError(Error):
    def __init__(self, msg=["Child phonenumber", "Watch ID"]) -> None:
        self.msg = msg
        super().__init__()

    def __str__(self) -> str:
        msg = " & ".join(self.msg)
        return "{} not found!".format(msg)


class XTypeError(Error):
    def __init__(self, allow, deny) -> None:
        self.allow = allow
        self.deny = deny
        super().__init__()

    def __str__(self) -> str:
        return "Transfer value has the wrong type! The following are permitted: {}. The specified type is: {}".format(
            self.allow, self.deny
        )


class FunctionError(Error):
    # FunctionError(sys._getframe().f_code.co_name)
    def __init__(self, fnc: str) -> None:
        self.fnc = fnc
        super().__init__(self.fnc)

    def __str__(self) -> str:
        return "Xplora API call finally failed with response: {0}".format(self.fnc)


class LoginError(Error):
    def __init__(self, message: str | ErrorMSG) -> None:
        self.message = message if isinstance(message, str) else message.value
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class PhoneOrEmailFail(LoginError):
    def __init__(self, message: str = ErrorMSG.PHONE_MAIL_ERR) -> None:
        super().__init__(message)
