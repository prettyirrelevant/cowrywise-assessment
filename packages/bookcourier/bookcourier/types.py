from typing import Literal, TypedDict


class BookData(TypedDict):
    id: str
    isbn: str
    title: str
    author: str
    added_by: str
    category: str
    publisher: str
    created_at: str
    updated_at: str


class BorrowedBookData(TypedDict):
    id: str
    book_id: str
    user_id: str
    created_at: str
    updated_at: str
    proposed_return_date: str


class AddBookMessage(TypedDict):
    event: Literal['book_added']
    book: BookData


class BorrowBookMessage(TypedDict):
    event: Literal['book_borrowed']
    borrowed_book: BorrowedBookData


class ReturnBookMessage(TypedDict):
    event: Literal['book_returned']
    borrowed_book_id: str
    actual_return_date: str


class RemoveBookMessage(TypedDict):
    event: Literal['book_removed']
    book_id: str


LibraryMessage = AddBookMessage | BorrowBookMessage | RemoveBookMessage | ReturnBookMessage
