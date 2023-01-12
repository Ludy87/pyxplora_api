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
        return "You are not an Administrator!"


class ChildNoError(Error):
    def __init__(self, error_message=["Child phonenumber", "Watch ID"]) -> None:
        self.error_message = error_message
        super().__init__()

    def __str__(self) -> str:
        error_message = " & ".join(self.error_message)
        return f"{error_message} not found!"


class XTypeError(Error):
    def __init__(self, allow, deny) -> None:
        self.allow = allow
        self.deny = deny
        super().__init__()

    def __str__(self) -> str:
        return (
            f"Transfer value has the wrong type! The following are permitted: {self.allow}. The specified type is: {self.deny}"
        )


class FunctionError(Error):
    # FunctionError(sys._getframe().f_code.co_name)
    def __init__(self, fnc: str) -> None:
        self.fnc = fnc
        super().__init__(self.fnc)

    def __str__(self) -> str:
        return f"Xplora API call finally failed with response: {self.fnc}"


class LoginError(Error):
    def __init__(self, error_message: str | ErrorMSG = "") -> None:
        self.error_message = error_message if isinstance(error_message, str) else error_message.value
        super().__init__()

    def __str__(self) -> str:
        return f"{self.error_message}"


class PhoneOrEmailFail(Error):
    def __init__(self, error_message: str | ErrorMSG = ErrorMSG.PHONE_MAIL_ERR) -> None:
        self.error_message = error_message if isinstance(error_message, str) else error_message.value
        super().__init__()

    def __str__(self) -> str:
        return f"{self.error_message}"
