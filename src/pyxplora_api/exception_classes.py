from __future__ import annotations


class Error(Exception):
    pass


class NoAdminError(Error):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "no Admin"


class ChildNoError(Error):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "Child phonenumber or Watch ID not found!"


class FunctionError(Error):
    def __init__(self, fnc: str) -> None:
        self.fnc = fnc
        super().__init__(self.fnc)

    def __str__(self) -> str:
        return "Xplora API call finally failed with response: {0}".format(self.fnc)


class LoginError(Error):
    def __init__(self, message: str, res: int = 1) -> None:
        self.message = message
        self.res = res
        super().__init__(self.message, self.res)

    def __str__(self) -> str:
        return f"{self.message} - {self.res}"
