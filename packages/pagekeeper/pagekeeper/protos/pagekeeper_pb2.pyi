from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class User(_message.Message):
    __slots__ = ("id", "email", "is_admin", "last_name", "first_name")
    ID_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    IS_ADMIN_FIELD_NUMBER: _ClassVar[int]
    LAST_NAME_FIELD_NUMBER: _ClassVar[int]
    FIRST_NAME_FIELD_NUMBER: _ClassVar[int]
    id: str
    email: str
    is_admin: bool
    last_name: str
    first_name: str
    def __init__(self, id: _Optional[str] = ..., email: _Optional[str] = ..., is_admin: bool = ..., last_name: _Optional[str] = ..., first_name: _Optional[str] = ...) -> None: ...

class RegisterRequest(_message.Message):
    __slots__ = ("email", "password", "first_name", "last_name", "is_admin")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    FIRST_NAME_FIELD_NUMBER: _ClassVar[int]
    LAST_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ADMIN_FIELD_NUMBER: _ClassVar[int]
    email: str
    password: str
    first_name: str
    last_name: str
    is_admin: bool
    def __init__(self, email: _Optional[str] = ..., password: _Optional[str] = ..., first_name: _Optional[str] = ..., last_name: _Optional[str] = ..., is_admin: bool = ...) -> None: ...

class RegisterResponse(_message.Message):
    __slots__ = ("message", "id")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    message: str
    id: str
    def __init__(self, message: _Optional[str] = ..., id: _Optional[str] = ...) -> None: ...

class AuthenticateRequest(_message.Message):
    __slots__ = ("email", "password")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    email: str
    password: str
    def __init__(self, email: _Optional[str] = ..., password: _Optional[str] = ...) -> None: ...

class AuthenticateResponse(_message.Message):
    __slots__ = ("message", "access_token", "user")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    message: str
    access_token: str
    user: User
    def __init__(self, message: _Optional[str] = ..., access_token: _Optional[str] = ..., user: _Optional[_Union[User, _Mapping]] = ...) -> None: ...

class VerifyRequest(_message.Message):
    __slots__ = ("access_token",)
    ACCESS_TOKEN_FIELD_NUMBER: _ClassVar[int]
    access_token: str
    def __init__(self, access_token: _Optional[str] = ...) -> None: ...

class VerifyResponse(_message.Message):
    __slots__ = ("message", "user")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    message: str
    user: User
    def __init__(self, message: _Optional[str] = ..., user: _Optional[_Union[User, _Mapping]] = ...) -> None: ...

class FetchUsersRequest(_message.Message):
    __slots__ = ("page", "page_size", "ids")
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    IDS_FIELD_NUMBER: _ClassVar[int]
    page: int
    page_size: int
    ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, page: _Optional[int] = ..., page_size: _Optional[int] = ..., ids: _Optional[_Iterable[str]] = ...) -> None: ...

class FetchUsersResponse(_message.Message):
    __slots__ = ("message", "total_users", "current_page", "users")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    TOTAL_USERS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PAGE_FIELD_NUMBER: _ClassVar[int]
    USERS_FIELD_NUMBER: _ClassVar[int]
    message: str
    total_users: int
    current_page: int
    users: _containers.RepeatedCompositeFieldContainer[User]
    def __init__(self, message: _Optional[str] = ..., total_users: _Optional[int] = ..., current_page: _Optional[int] = ..., users: _Optional[_Iterable[_Union[User, _Mapping]]] = ...) -> None: ...
