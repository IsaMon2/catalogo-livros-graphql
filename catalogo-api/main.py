
from datetime import datetime
from enum import Enum
from typing import Optional

import strawberry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

# --------------------------------------------------
# Enum de status
# --------------------------------------------------

@strawberry.enum
class ReadingStatus(Enum):
    WANT_TO_READ = "WANT_TO_READ"
    READING = "READING"
    FINISHED = "FINISHED"

# --------------------------------------------------
# Banco de dados em memória
# --------------------------------------------------

AUTHORS = {
    1: {"id": 1, "name": "Machado de Assis", "country": "Brasil"},
    2: {"id": 2, "name": "George Orwell", "country": "Reino Unido"},
    3: {"id": 3, "name": "Clarice Lispector", "country": "Brasil"},
}

BOOKS = {
    1: {
        "id": 1,
        "title": "Dom Casmurro",
        "year": 1899,
        "pages": 256,
        "status": ReadingStatus.FINISHED,
        "rating": 5,
        "author_id": 1,
    },
    2: {
        "id": 2,
        "title": "Memórias Póstumas de Brás Cubas",
        "year": 1881,
        "pages": 208,
        "status": ReadingStatus.FINISHED,
        "rating": 4,
        "author_id": 1,
    },
    3: {
        "id": 3,
        "title": "1984",
        "year": 1949,
        "pages": 328,
        "status": ReadingStatus.READING,
        "rating": None,
        "author_id": 2,
    },
    4: {
        "id": 4,
        "title": "A Revolução dos Bichos",
        "year": 1945,
        "pages": 152,
        "status": ReadingStatus.WANT_TO_READ,
        "rating": None,
        "author_id": 2,
    },
    5: {
        "id": 5,
        "title": "A Hora da Estrela",
        "year": 1977,
        "pages": 88,
        "status": ReadingStatus.FINISHED,
        "rating": 5,
        "author_id": 3,
    },
    6: {
        "id": 6,
        "title": "Perto do Coração Selvagem",
        "year": 1943,
        "pages": 202,
        "status": ReadingStatus.WANT_TO_READ,
        "rating": None,
        "author_id": 3,
    },
}

# --------------------------------------------------
# Tipos GraphQL
# --------------------------------------------------

@strawberry.type
class Author:
    id: int
    name: str
    country: Optional[str]

    @strawberry.field
    def books(self) -> list["Book"]:
        return [
            create_book(book)
            for book in BOOKS.values()
            if book["author_id"] == self.id
        ]

    @strawberry.field
    def book_count(self) -> int:
        return sum(
            1 for book in BOOKS.values()
            if book["author_id"] == self.id
        )

@strawberry.type
class Book:
    id: int
    title: str
    year: int
    pages: int
    status: ReadingStatus
    rating: Optional[int]
    author_id: strawberry.Private[int]

    @strawberry.field
    def author(self) -> Author:
        return create_author(AUTHORS[self.author_id])

@strawberry.type
class Stats:
    total_books: int
    finished_books: int
    average_rating: Optional[float]
    total_pages_read: int

# --------------------------------------------------
# Inputs
# --------------------------------------------------

@strawberry.input
class AuthorInput:
    name: str
    country: Optional[str] = None

@strawberry.input
class BookInput:
    title: str
    year: int
    pages: int
    author_id: int

# --------------------------------------------------
# Funções auxiliares
# --------------------------------------------------

def create_author(data):
    return Author(
        id=data["id"],
        name=data["name"],
        country=data["country"],
    )

def create_book(data):
    return Book(
        id=data["id"],
        title=data["title"],
        year=data["year"],
        pages=data["pages"],
        status=data["status"],
        rating=data["rating"],
        author_id=data["author_id"],
    )

def validate_book(data: BookInput):
    if not data.title.strip():
        raise ValueError("O título não pode ser vazio.")

    if data.year > datetime.now().year:
        raise ValueError("O ano não pode ser maior que o ano atual.")

    if data.pages < 1:
        raise ValueError("O número de páginas deve ser maior que zero.")

    if data.author_id not in AUTHORS:
        raise ValueError("Autor não encontrado.")

# --------------------------------------------------
# Queries
# --------------------------------------------------

@strawberry.type
class Query:

    @strawberry.field
    def books(
        self,
        status: Optional[ReadingStatus] = None,
        search: Optional[str] = None,
    ) -> list[Book]:

        results = list(BOOKS.values())

        if status is not None:
            results = [
                book for book in results
                if book["status"] == status
            ]

        if search:
            results = [
                book for book in results
                if search.casefold() in book["title"].casefold()
            ]

        return [create_book(book) for book in results]

    @strawberry.field
    def book(self, id: int) -> Optional[Book]:
        data = BOOKS.get(id)
        return create_book(data) if data else None

    @strawberry.field
    def authors(self) -> list[Author]:
        return [
            create_author(author)
            for author in AUTHORS.values()
        ]

    @strawberry.field
    def stats(self) -> Stats:

        finished = [
            book for book in BOOKS.values()
            if book["status"] == ReadingStatus.FINISHED
        ]

        ratings = [
            book["rating"]
            for book in BOOKS.values()
            if book["rating"] is not None
        ]

        average = (
            sum(ratings) / len(ratings)
            if ratings else None
        )

        pages_read = sum(
            book["pages"] for book in finished
        )

        return Stats(
            total_books=len(BOOKS),
            finished_books=len(finished),
            average_rating=average,
            total_pages_read=pages_read,
        )

# --------------------------------------------------
# Mutations
# --------------------------------------------------

@strawberry.type
class Mutation:

    @strawberry.mutation
    def add_author(self, input: AuthorInput) -> Author:

        if not input.name.strip():
            raise ValueError("O nome do autor não pode ser vazio.")

        new_id = max(AUTHORS.keys(), default=0) + 1

        author = {
            "id": new_id,
            "name": input.name.strip(),
            "country": input.country,
        }

        AUTHORS[new_id] = author
        return create_author(author)

    @strawberry.mutation
    def add_book(self, input: BookInput) -> Book:

        validate_book(input)

        new_id = max(BOOKS.keys(), default=0) + 1

        book = {
            "id": new_id,
            "title": input.title.strip(),
            "year": input.year,
            "pages": input.pages,
            "status": ReadingStatus.WANT_TO_READ,
            "rating": None,
            "author_id": input.author_id,
        }

        BOOKS[new_id] = book
        return create_book(book)

    @strawberry.mutation
    def update_book_status(
        self,
        id: int,
        status: ReadingStatus,
    ) -> Book:

        if id not in BOOKS:
            raise ValueError("Livro não encontrado.")

        BOOKS[id]["status"] = status

        if status != ReadingStatus.FINISHED:
            BOOKS[id]["rating"] = None

        return create_book(BOOKS[id])

    @strawberry.mutation
    def rate_book(self, id: int, rating: int) -> Book:

        if id not in BOOKS:
            raise ValueError("Livro não encontrado.")

        if rating < 1 or rating > 5:
            raise ValueError("A nota deve estar entre 1 e 5.")

        if BOOKS[id]["status"] != ReadingStatus.FINISHED:
            raise ValueError(
                "Só é possível avaliar livros finalizados."
            )

        BOOKS[id]["rating"] = rating

        return create_book(BOOKS[id])

    @strawberry.mutation
    def delete_book(self, id: int) -> bool:

        if id not in BOOKS:
            raise ValueError("Livro não encontrado.")

        del BOOKS[id]
        return True

# --------------------------------------------------
# Aplicação FastAPI
# --------------------------------------------------

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
)

app = FastAPI(title="Meu Catálogo de Livros")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    GraphQLRouter(schema),
    prefix="/graphql",
)