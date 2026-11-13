"""Verificacoes executaveis: python -m unittest -v."""
import unittest
import itertools
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from collections import deque
from codigo.scanner import (tokenize, recognize, minimize, DELTA, STATES, FINAL,
                            CLASSES, LexicalError, char_class)

class ScannerTests(unittest.TestCase):
    def test_classes_and_maximal_munch(self):
        actual = [(t.kind, t.lexeme) for t in tokenize('let if ifx _a2 007 0.5 +-*/=();')]
        self.assertEqual(actual, [('KW_LET','let'), ('KW_IF','if'), ('ID','ifx'),
            ('ID','_a2'), ('INT','007'), ('FLOAT','0.5')] +
            [('OP',c) for c in '+-*/='] + [('SEP',c) for c in '();'])

    def test_all_keywords(self):
        self.assertEqual([t.kind for t in tokenize('let if else print')],
                         ['KW_LET','KW_IF','KW_ELSE','KW_PRINT'])

    def test_single_lexemes(self):
        for word in ('a', '_a9', '0', '001', '12.50', '+', ';', '\r\n\t '):
            with self.subTest(word=word): self.assertTrue(recognize(word))
        for word in ('', '.5', '12.', '@', 'a+b', '12.3.4', 'ç'):
            with self.subTest(word=word): self.assertFalse(recognize(word))

    def test_positions(self):
        ts = tokenize('let x=1;\n  print(x);')
        self.assertEqual((ts[0].line, ts[0].column), (1,1))
        self.assertEqual((ts[5].kind, ts[5].line, ts[5].column), ('KW_PRINT',2,3))

    def test_errors_and_rollback(self):
        for source, position in [('12.', '1:3'), ('.5','1:1'),
                                 ('12.3.4','1:5'), ('a\n@','2:1')]:
            with self.subTest(source=source):
                with self.assertRaisesRegex(LexicalError, position): tokenize(source)

    def test_explicit_lexical_policy(self):
        self.assertEqual([(t.kind,t.lexeme) for t in tokenize('12abc -3 ==')],
            [('INT','12'),('ID','abc'),('OP','-'),('INT','3'),('OP','='),('OP','=')])
        self.assertEqual(tokenize(''), [])
        self.assertEqual(tokenize(' \t\r\n'), [])

    def test_total_transition_function_and_reachability(self):
        self.assertEqual(set(DELTA), set(STATES))
        for row in DELTA.values():
            self.assertEqual(set(row), set(CLASSES))
            self.assertLessEqual(set(row.values()), set(STATES))
        seen, queue = {'q0'}, deque(['q0'])
        while queue:
            for dest in DELTA[queue.popleft()].values():
                if dest not in seen: seen.add(dest); queue.append(dest)
        self.assertEqual(seen, set(STATES))

    def test_minimization_and_exact_equivalence(self):
        blocks, _ = minimize()
        self.assertEqual(len(blocks), 8)
        self.assertIn({'qOp','qSep'}, blocks)
        which = {q:i for i,b in enumerate(blocks) for q in b}
        table = {i:{c:which[DELTA[next(iter(b))][c]] for c in CLASSES}
                 for i,b in enumerate(blocks)}
        finals = {which[q] for q in FINAL}
        queue, seen = deque([('q0',which['q0'])]), set()
        while queue:
            q, b = queue.popleft()
            if (q,b) in seen: continue
            seen.add((q,b))
            self.assertEqual(q in FINAL, b in finals)
            for c in CLASSES: queue.append((DELTA[q][c],table[b][c]))
        # Produto alcancavel: equivalencia para TODAS as palavras, nao amostragem.
        self.assertEqual(len(seen), 9)

    def test_character_class_requires_one_character(self):
        for ch in ('', 'ab'):
            with self.subTest(ch=ch):
                with self.assertRaises(ValueError): char_class(ch)

    def test_recognizer_against_independent_regex(self):
        pattern = re.compile(r'(?:[A-Za-z_][A-Za-z_0-9]*|[0-9]+|[0-9]+\.[0-9]+|[+*/=\-]|[();]|[ \t\r\n]+)')
        # 2801 palavras: uma representante de cada uma das sete classes.
        for n in range(5):
            for chars in itertools.product('a0.+; @', repeat=n):
                word = ''.join(chars)
                self.assertEqual(recognize(word), pattern.fullmatch(word) is not None, word)


class CommandLineTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]
    scanner = root / 'codigo' / 'scanner.py'

    def run_cli(self, *args, input_text=None, cwd=None):
        return subprocess.run([sys.executable, str(self.scanner), *args],
                              input=input_text, capture_output=True, text=True,
                              encoding='utf-8', cwd=cwd or self.root, timeout=20)

    def test_default_input_from_another_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            p = self.run_cli(cwd=folder)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('KW_LET', p.stdout)

    def test_json_tokens_and_minimization(self):
        p = self.run_cli('--json', '--minimizar')
        self.assertEqual(p.returncode, 0, p.stderr)
        data = json.loads(p.stdout)
        self.assertEqual(data['tokens'][3]['lexeme'], '12.50')
        self.assertEqual(data['minimization']['minimal_states'], 8)

    def test_standard_input(self):
        p = self.run_cli('-', '--json', input_text='print(3);')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)['tokens'][0]['kind'], 'KW_PRINT')

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            p = self.run_cli(str(Path(folder) / 'nao_existe.min'), '--json')
        self.assertEqual(p.returncode, 1)
        self.assertEqual(json.loads(p.stderr)['error']['type'], 'FileNotFoundError')

    def test_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as folder:
            f = Path(folder) / 'invalid.min'
            f.write_bytes(b'\xff')
            p = self.run_cli(str(f), '--json')
        self.assertEqual(p.returncode, 1)
        self.assertEqual(json.loads(p.stderr)['error']['type'], 'UnicodeDecodeError')
        self.assertNotIn('Traceback', p.stderr)

    def test_lexical_error_has_position_and_no_partial_output(self):
        p = self.run_cli('-', '--json', input_text='let total = 12.;')
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stdout, '')
        error = json.loads(p.stderr)['error']
        self.assertEqual((error['character'], error['line'], error['column']), ('.', 1, 15))

    def test_crlf_file_matches_api(self):
        source = 'let a=1;\r\n\tprint(a);'
        with tempfile.TemporaryDirectory() as folder:
            f = Path(folder) / 'windows.min'
            f.write_bytes(source.encode('utf-8'))
            p = self.run_cli(str(f), '--json')
        self.assertEqual(p.returncode, 0, p.stderr)
        expected = [(t.kind, t.lexeme, t.line, t.column) for t in tokenize(source)]
        actual = [(t['kind'], t['lexeme'], t['line'], t['column'])
                  for t in json.loads(p.stdout)['tokens']]
        self.assertEqual(actual, expected)

    def test_version_identifies_revision(self):
        p = self.run_cli('--version')
        self.assertEqual(p.returncode, 0)
        self.assertIn('1.1.0 (2026-11-13)', p.stdout)


if __name__ == '__main__': unittest.main()
