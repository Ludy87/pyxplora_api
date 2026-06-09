from __future__ import annotations

from pyxplora_api.exception_classes import (
    ChildNoError,
    Error,
    ErrorMSG,
    FunctionError,
    HandlerException,
    LoginError,
    NoAdminError,
    PhoneOrEmailFail,
    XTypeError,
)


def test_exception_messages_are_human_readable() -> None:
    assert str(Error("base")) == "base"
    assert str(HandlerException("bad handler")) == "HandlerException: bad handler"
    assert str(NoAdminError()) == "You are not an Administrator!"
    assert str(ChildNoError()) == "Child phonenumber & Watch ID not found!"
    assert str(ChildNoError(["Watch ID"])) == "Watch ID not found!"
    assert str(XTypeError("str", int)) == (
        "Transfer value has the wrong type! The following are permitted: str. "
        "The specified type is: <class 'int'>"
    )
    assert (
        str(FunctionError("call"))
        == "Xplora API call finally failed with response: call"
    )


def test_login_and_contact_errors_accept_error_enums() -> None:
    assert str(LoginError(ErrorMSG.AUTH_FAIL)) == "Authentication failed."
    assert str(PhoneOrEmailFail()) == "Phone Number or Email address not exist"
    assert (
        str(PhoneOrEmailFail(ErrorMSG.PHONE_MAIL_ERR))
        == "Phone Number or Email address not exist"
    )
