const API = "http://127.0.0.1:8000/graphql";

const $ = (id) => document.getElementById(id);

const labels = {
  WANT_TO_READ: "Quero ler",
  READING: "Lendo",
  FINISHED: "Lido",
};

// Função genérica GraphQL
async function gql(query, variables = {}) {
  const response = await fetch(API, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, variables }),
  });

  if (!response.ok) {
    throw new Error(`Erro HTTP ${response.status}`);
  }

  const result = await response.json();

  if (result.errors?.length) {
    throw new Error(result.errors.map((e) => e.message).join("; "));
  }

  return result.data;
}

// Query principal
const QUERY = `
  query($status: ReadingStatus, $search: String) {
    books(status: $status, search: $search) {
      id
      title
      year
      pages
      status
      rating
      author {
        name
      }
    }

    authors {
      id
      name
    }

    stats {
      totalBooks
      finishedBooks
      averageRating
      totalPagesRead
    }
  }
`;

function showError(error) {
  $("error").textContent = error.message;
  $("error").hidden = false;
}

function clearError() {
  $("error").hidden = true;
}

// Mostrar estatísticas
function renderStats(stats) {
  $("stats").replaceChildren();

  const dados = [
    ["Total de livros", stats.totalBooks],
    ["Livros lidos", stats.finishedBooks],
    [
      "Média das notas",
      stats.averageRating == null
        ? "Sem avaliações"
        : stats.averageRating.toFixed(1),
    ],
    ["Páginas lidas", stats.totalPagesRead],
  ];

  dados.forEach(([titulo, valor]) => {
    const card = document.createElement("div");
    card.className = "stat";

    const numero = document.createElement("strong");
    numero.textContent = valor;

    const texto = document.createElement("span");
    texto.textContent = titulo;

    card.append(numero, texto);
    $("stats").append(card);
  });
}

// Carregar autores no formulário
function renderAuthors(authors) {
  const select = $("author-select");
  const anterior = select.value;

  select.replaceChildren();

  authors.forEach((author) => {
    select.add(new Option(author.name, author.id));
  });

  if ([...select.options].some((o) => o.value === anterior)) {
    select.value = anterior;
  }
}

// Mostrar livros
function renderBooks(books) {
  $("books").replaceChildren();

  $("empty").hidden = books.length > 0;

  books.forEach((book) => {
    const card = document.createElement("article");
    card.className = "book";

    const title = document.createElement("h3");
    title.textContent = book.title;

    const info = document.createElement("p");
    info.textContent = `${book.author.name} • ${book.year} • ${book.pages} páginas`;

    const nota = document.createElement("p");
    nota.textContent = `Nota: ${book.rating ?? "Não avaliado"}`;

    // Selecionar status
    const label = document.createElement("label");
    label.textContent = "Status";

    const select = document.createElement("select");

    Object.entries(labels).forEach(([value, text]) => {
      select.add(new Option(text, value));
    });

    select.value = book.status;

    select.addEventListener("change", async () => {
      try {
        clearError();

        await gql(
          `
          mutation($id: Int!, $status: ReadingStatus!) {
            updateBookStatus(id: $id, status: $status) {
              id
            }
          }
        `,
          {
            id: book.id,
            status: select.value,
          },
        );

        await load();
      } catch (error) {
        showError(error);
        select.value = book.status;
      }
    });

    label.append(select);

    const actions = document.createElement("div");
    actions.className = "actions";

    // Avaliar somente livros finalizados
    if (book.status === "FINISHED") {
      const btnNota = document.createElement("button");
      btnNota.textContent = "Dar nota";

      btnNota.addEventListener("click", async () => {
        const valor = prompt(
          "Digite uma nota de 1 a 5:",
          String(book.rating ?? 5),
        );

        if (valor === null) return;

        const rating = Number(valor);

        if (!Number.isInteger(rating)) {
          showError(new Error("Digite um número inteiro."));
          return;
        }

        try {
          clearError();

          await gql(
            `
            mutation($id: Int!, $rating: Int!) {
              rateBook(id: $id, rating: $rating) {
                id
                rating
              }
            }
          `,
            {
              id: book.id,
              rating,
            },
          );

          await load();
        } catch (error) {
          showError(error);
        }
      });

      actions.append(btnNota);
    }

    // Excluir livro
    const btnExcluir = document.createElement("button");
    btnExcluir.className = "danger";
    btnExcluir.textContent = "Excluir";

    btnExcluir.addEventListener("click", async () => {
      if (!confirm(`Excluir o livro "${book.title}"?`)) {
        return;
      }

      try {
        clearError();

        await gql(
          `
          mutation($id: Int!) {
            deleteBook(id: $id)
          }
        `,
          { id: book.id },
        );

        await load();
      } catch (error) {
        showError(error);
      }
    });

    actions.append(btnExcluir);

    card.append(title, info, nota, label, actions);
    $("books").append(card);
  });
}

// Buscar dados da API
async function load() {
  $("loading").hidden = false;
  clearError();

  try {
    const data = await gql(QUERY, {
      status: $("filter-status").value || null,
      search: $("search").value.trim() || null,
    });

    renderStats(data.stats);
    renderAuthors(data.authors);
    renderBooks(data.books);
  } catch (error) {
    showError(error);
  } finally {
    $("loading").hidden = true;
  }
}

// Cadastrar livro
$("form-book").addEventListener("submit", async (event) => {
  event.preventDefault();

  const form = new FormData(event.currentTarget);

  try {
    clearError();

    await gql(
      `
      mutation($input: BookInput!) {
        addBook(input: $input) {
          id
          title
        }
      }
    `,
      {
        input: {
          title: form.get("title"),
          year: Number(form.get("year")),
          pages: Number(form.get("pages")),
          authorId: Number(form.get("authorId")),
        },
      },
    );

    document.getElementById("form-book").reset();

    await load();
  } catch (error) {
    showError(error);
  }
});

// Filtro por status
$("filter-status").addEventListener("change", load);

// Busca com debounce de 300 ms
let timer;

$("search").addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(load, 300);
});

// Carregamento inicial
load();
