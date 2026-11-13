# MiniL — Linguagens Formais e Autômatos Finitos

Reconhecedor léxico de uma mini-linguagem, modelado com um autômato finito determinístico completo e implementado em Python.

**Versão 1.1.0 — revisão de 13 de novembro de 2026.**

## Documentos

| Material | PDF | Fonte LaTeX |
|---|---|---|
| Relatório técnico | [Abrir](relatorios/tecnico/relatorio_tecnico.pdf) | [article](relatorios/tecnico/relatorio_tecnico.tex) |
| Relatório explicativo para o cliente | [Abrir](relatorios/cliente/relatorio_cliente.pdf) | [article](relatorios/cliente/relatorio_cliente.tex) |
| Apresentação | [Abrir](slides/apresentacao.pdf) | [beamer](slides/apresentacao.tex) |

O relatório técnico formaliza a tupla, a tabela de transições, os diagramas TikZ, as expressões regulares e a minimização de nove para oito estados. O relatório do cliente apresenta o problema, o uso, exemplos de resultados e erros, critérios de aceite e limites em linguagem acessível.

## Organização

- `codigo/`: scanner e interface de linha de comando.
- `testes/`: testes de comportamento, propriedades formais e interface.
- `exemplos/`: arquivos positivo e negativo.
- `relatorios/tecnico/` e `relatorios/cliente/`: os dois relatórios em PDF e LaTeX.
- `slides/`: apresentação em PDF e Beamer.
- `documentacao/latex/`: estilo e diagramas compartilhados.
- `evidencias/`: resultados registrados de execução e verificação.
- `scripts/`: comandos para validar e recompilar os documentos.

## Executar

Requer **Python 3.12 ou superior**. O scanner usa somente a biblioteca padrão; não é necessário instalar pacotes.

Na raiz do repositório:

```sh
python codigo/scanner.py exemplos/exemplo.min --minimizar
python codigo/scanner.py exemplos/exemplo.min --json
python codigo/scanner.py exemplos/invalido.min
python scripts/validar.py
```

O exemplo inválido deve informar erro no ponto em **1:15** e terminar com código **1**. Isso é o comportamento esperado. Os testes devem terminar com `OK` e código **0**.

Sem um caminho explícito, o scanner usa o exemplo positivo incluído no projeto. Esse caminho é calculado em relação ao arquivo do código e funciona mesmo quando o comando é executado de outra pasta.

Para consultar a versão:

```sh
python codigo/scanner.py --version
```

O argumento `-` lê a entrada padrão. Exemplo em Bash:

```sh
printf 'let total = 12.50;' | python codigo/scanner.py - --json
```

Em PowerShell:

```powershell
'let total = 12.50;' | python codigo/scanner.py - --json
```

## Exemplo de resultado

Entrada: `let total = 12.50;`

| Categoria | Lexema | Linha | Coluna |
|---|---|---:|---:|
| KW_LET | let | 1 | 1 |
| ID | total | 1 | 5 |
| OP | = | 1 | 11 |
| FLOAT | 12.50 | 1 | 13 |
| SEP | ; | 1 | 18 |

Com `--json`, o objeto de saída contém `tokens`, uma lista com `kind`, `lexeme`, `line` e `column`. Com `--minimizar --json`, contém também `minimization`. Em caso de erro, o objeto `error` é escrito em stderr, stdout fica vazio e o processo termina com código 1. Uso incorreto dos argumentos termina com código 2.

## Regras e limites

- Palavras reservadas: `let`, `if`, `else`, `print`.
- ID: `[A-Za-z_][A-Za-z_0-9]*`; INT: `[0-9]+`; FLOAT: `[0-9]+\.[0-9]+`.
- Operadores de um caractere: `+ - * / =`; separadores: `( ) ;`.
- Espaço, tabulação, CR e LF são reconhecidos e descartados. LF inicia outra linha; tabulação conta como uma coluna.
- As palavras-chave são consultadas após consumir o maior identificador: `ifx` é ID.
- `12abc` produz INT e ID; `-3` produz OP e INT; `==` produz dois OP.
- A entrada de arquivo é UTF-8. Letras acentuadas não integram identificadores.
- Não há strings, comentários ou notação científica. `//` continua sendo dois operadores, não início de comentário.
- O programa separa tokens; não verifica a sintaxe, o balanceamento de parênteses, os tipos nem o significado do programa.

## Verificação

```sh
python -m unittest discover -s testes -v
```

São **18 testes**, incluindo um confronto com uma regex independente em **2.801 palavras**, a totalidade e a alcançabilidade do AFD, e a equivalência exata do original com seu quociente por exploração do produto. Os testes de exemplos não provam sozinhos a correção do scanner para todas as entradas; a argumentação formal está no relatório técnico.

A minimização demonstrada é do **reconhecedor booleano de lexemas**. OP e SEP se fundem porque aceitam e têm os mesmos destinos. O scanner mantém os nove estados originais para classificar diretamente; no quociente, OP/SEP precisariam ser recuperados do lexema.

## Compilar os documentos

Os PDFs já estão prontos. Para recompilar, instale uma distribuição LaTeX com `pdflatex` (TeX Live ou MiKTeX) ou Tectonic e execute:

```sh
python scripts/compilar.py
```

O script compila cada documento no próprio diretório e usa os arquivos compartilhados de `documentacao/latex/`. Com pdfLaTeX, executa duas passagens para atualizar referências e sumário. Não há dependências Python externas para esse script.

## Revisão de 2026

Esta versão acrescenta tipos explícitos e aliases da sintaxe Python 3.12, JSON, entrada padrão, erro de codificação tratado, preservação de CR/LF e execução independente do diretório corrente. A versão do interpretador realmente testada e os resultados estão em `evidencias/validacao.txt`.

A documentação oficial do Python 3.14 foi consultada em 13/11/2026: [Python 3.14 Documentation](https://docs.python.org/3.14/).

## Integrantes

Gabriel Holanda · Gabriel Torres · Victor Milito · Paulo Júnior · Vinicius Kaua · Pablo Café.
