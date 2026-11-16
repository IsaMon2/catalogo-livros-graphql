# Exercício - Catálogo de Livros com GraphQL

## Parte 1 - Reflexão

### 1. Por que status é melhor como enum do que como String?

Porque o enum permite apenas valores definidos, como
WANT_TO_READ, READING e FINISHED. Isso evita erros
de digitação e impede status inválidos.

### 2. Por que rating é opcional e title não?

O título é obrigatório porque identifica o livro.
Já a nota é opcional porque um livro pode ainda
não ter sido lido ou avaliado.

### 3. bookCount deve ser armazenado ou calculado?

É melhor calcular por um resolver, pois a quantidade
de livros pode mudar. Assim, o valor será atualizado
quando um livro for adicionado ou excluído.

## Parte 4 - Análise

### 9. Quantas requisições REST e GraphQL?

Em uma API REST com endpoints separados, seriam
normalmente três requisições: livros, autores e
estatísticas. Com GraphQL, fiz uma única requisição
para buscar todos esses dados.

### 10. O que acontece quando uma mutation lança erro?

Quando ocorre um erro de execução, a resposta GraphQL
geralmente tem código HTTP 200 e um campo "errors"
no JSON. O frontend verifica esse campo e mostra
a mensagem ao usuário.

### 11. O que é o problema N+1?

O problema N+1 ocorre quando uma consulta busca
100 autores e depois faz outra consulta para cada
autor, totalizando 101 consultas. O DataLoader ajuda
agrupando essas buscas e reduzindo acessos ao banco.

### 12. Vantagem e desvantagem de um único endpoint?

Uma vantagem é conseguir consultar diferentes dados
em uma única requisição. Uma desvantagem é que o
cache e o monitoramento podem ser mais complexos.
