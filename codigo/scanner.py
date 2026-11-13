"""Scanner MiniL. Revisao 1.1.0, de 13/11/2026; Python 3.12+.

Simula diretamente o AFD, sem executar expressoes regulares.
Da raiz: python codigo/scanner.py exemplos/exemplo.min --minimizar
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

type State = Literal['q0', 'qI', 'qN', 'qDot', 'qF', 'qOp', 'qSep', 'qW', 'qErr']
type CharClass = Literal['L', 'D', '.', 'O', 'S', 'W', 'X']
type Partition = list[set[State]]

VERSION = '1.1.0'
REVISION_DATE = '2026-11-13'
DEFAULT_INPUT = Path(__file__).resolve().parents[1] / 'exemplos' / 'exemplo.min'

# TABELA_INICIO
CLASSES: tuple[CharClass, ...] = ('L', 'D', '.', 'O', 'S', 'W', 'X')
STATES: tuple[State, ...] = ('q0', 'qI', 'qN', 'qDot', 'qF', 'qOp', 'qSep', 'qW', 'qErr')
FINAL: frozenset[State] = frozenset(('qI', 'qN', 'qF', 'qOp', 'qSep', 'qW'))
DEAD: State = 'qErr'
DELTA: dict[State, dict[CharClass, State]] = {q: {c: DEAD for c in CLASSES} for q in STATES}
DELTA['q0'].update(L='qI', D='qN', O='qOp', S='qSep', W='qW')
DELTA['qI'].update(L='qI', D='qI')
DELTA['qN'].update(D='qN', **{'.': 'qDot'})
DELTA['qDot']['D'] = 'qF'
DELTA['qF']['D'] = 'qF'
DELTA['qW']['W'] = 'qW'
# TABELA_FIM
KEYWORDS = {'let': 'KW_LET', 'if': 'KW_IF', 'else': 'KW_ELSE', 'print': 'KW_PRINT'}
KINDS = {'qI': 'ID', 'qN': 'INT', 'qF': 'FLOAT', 'qOp': 'OP', 'qSep': 'SEP'}


def char_class(ch: str) -> CharClass:
    """Classifica exatamente um caractere; as letras e digitos sao ASCII."""
    if len(ch) != 1:
        raise ValueError('char_class exige exatamente um caractere')
    if ch in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_':
        return 'L'
    if ch in '0123456789':
        return 'D'
    if ch == '.':
        return '.'
    if ch in '+-*/=':
        return 'O'
    if ch in '();':
        return 'S'
    if ch in ' \t\r\n':
        return 'W'
    return 'X'


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    lexeme: str
    line: int
    column: int


class LexicalError(ValueError):
    """Erro com campos reutilizaveis por uma futura interface."""

    def __init__(self, character: str, line: int, column: int) -> None:
        self.character, self.line, self.column = character, line, column
        super().__init__(f'Caractere inesperado {character!r} em {line}:{column}')


def recognize(word: str) -> bool:
    """Reconhece um unico lexema, inclusive um bloco de espacos."""
    q: State = 'q0'
    for ch in word:
        q = DELTA[q][char_class(ch)]
    return q in FINAL


# SCANNER_INICIO
def tokenize(source: str) -> list[Token]:
    """Maior prefixo aceito; guarda a ultima posicao final para retroceder."""
    tokens: list[Token] = []
    i, line, column = 0, 1, 1
    while i < len(source):
        q: State = 'q0'
        j, last = i, None
        while j < len(source):
            q = DELTA[q][char_class(source[j])]
            if q == DEAD:
                break
            j += 1
            if q in FINAL:
                last = (j, q)
        if last is None:
            raise LexicalError(source[i], line, column)
        end, accepted = last
        lexeme = source[i:end]
        if accepted != 'qW':
            kind = KINDS[accepted]
            if kind == 'ID':
                kind = KEYWORDS.get(lexeme, 'ID')
            tokens.append(Token(kind, lexeme, line, column))
        for ch in lexeme:
            if ch == '\n':
                line, column = line + 1, 1
            else:
                column += 1
        i = end
    return tokens
# SCANNER_FIM


def minimize() -> tuple[Partition, list[Partition]]:
    """Refinamento de Moore para a linguagem booleana de um unico lexema."""
    partition: Partition = [set(FINAL), set(STATES) - FINAL]
    history = [[set(b) for b in partition]]
    while True:
        block_of = {q: i for i, block in enumerate(partition) for q in block}
        refined: Partition = []
        for block in partition:
            groups: dict[tuple[int, ...], set[State]] = {}
            for q in sorted(block):
                signature = tuple(block_of[DELTA[q][c]] for c in CLASSES)
                groups.setdefault(signature, set()).add(q)
            refined.extend(groups.values())
        history.append([set(b) for b in refined])
        if {frozenset(b) for b in refined} == {frozenset(b) for b in partition}:
            return refined, history
        partition = refined


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Scanner MiniL por AFD')
    parser.add_argument('arquivo', nargs='?', default=str(DEFAULT_INPUT),
                        help='arquivo UTF-8; use - para entrada padrao')
    parser.add_argument('--minimizar', action='store_true', help='mostrar particoes de Moore')
    parser.add_argument('--json', action='store_true', help='saida estruturada para integracao')
    parser.add_argument('--version', action='version', version=f'MiniL {VERSION} ({REVISION_DATE})')
    args = parser.parse_args(argv)
    try:
        if args.arquivo == '-':
            source = sys.stdin.read()
        else:
            # Preserva CR/LF para que a API e a CLI contem os mesmos caracteres.
            with Path(args.arquivo).open(encoding='utf-8', newline='') as stream:
                source = stream.read()
        tokens = tokenize(source)  # Sem saida parcial antes de validar toda a entrada.
    except (OSError, UnicodeError, LexicalError) as exc:
        if args.json:
            error = {'type': type(exc).__name__, 'message': str(exc)}
            if isinstance(exc, LexicalError):
                error.update(character=exc.character, line=exc.line, column=exc.column)
            print(json.dumps({'error': error}, ensure_ascii=True), file=sys.stderr)
        else:
            print(f'Erro: {exc}', file=sys.stderr)
        return 1
    result = {'tokens': [asdict(t) for t in tokens]}
    if args.minimizar:
        blocks, history = minimize()
        partitions = [[sorted(b) for b in p] for p in history]
        if args.json:
            result['minimization'] = {'original_states': len(STATES),
                                      'minimal_states': len(blocks), 'partitions': partitions}
        else:
            for i, partition in enumerate(partitions):
                print(f'P{i} = ' + ' | '.join('{' + ','.join(b) + '}' for b in partition))
            print(f'{len(STATES)} estados -> {len(blocks)} estados')
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        for token in tokens:
            print(f'{token.line}:{token.column:<3} {token.kind:<9} {token.lexeme}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
