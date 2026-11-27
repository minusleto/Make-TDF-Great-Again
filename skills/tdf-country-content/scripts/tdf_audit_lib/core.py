"""Базовые типы, токенайзер и парсер HOI-скриптов, обход файлов, общие константы.

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import re
from pathlib import Path
from typing import Iterator, List, Optional, Sequence, Tuple, Union



BANNED = [
    "strengthen ties", "mutual benefit", "significant", "foothold", "valuable",
    "comprehensive", "ensuring", "foster", "paving the way",
]


BANNED_WORD = re.compile(r"\bkey\b", re.I)


GENERIC_LABELS = {
    "good", "great", "nice", "excellent", "interesting", "damn", "yes", "no",
    "ok", "okay", "fantastic", "wonderful", "sad", "sure", "decline the proposal",
    "decline", "thanks",
}


TAG_RE = re.compile(r"^[A-Z]{3}$")


LOC_LINE_RE = re.compile(r'^\s*([^\s:#]+):\d*\s+"((?:\\.|[^"\\])*)"\s*(?:#.*)?$')


class AuditInputError(Exception):
    """Ошибка структуры репозитория или чтения входных файлов."""


class Token:
    __slots__ = ("kind", "value", "line", "column", "offset")

    def __init__(self, kind: str, value: str, line: int, column: int, offset: int):
        self.kind = kind
        self.value = value
        self.line = line
        self.column = column
        self.offset = offset


class Entry:
    __slots__ = ("key", "value")

    def __init__(self, key: Token, value: Union[Token, "Block"]):
        self.key = key
        self.value = value

    @property
    def line(self) -> int:
        return self.key.line


class Block:
    __slots__ = ("items", "line")

    def __init__(self, items: Optional[List[Union[Entry, Token]]] = None, line: int = 1):
        self.items = items if items is not None else []
        self.line = line

    @property
    def entries(self) -> List[Entry]:
        return [item for item in self.items if isinstance(item, Entry)]


class ParseIssue:
    __slots__ = ("line", "column", "message")

    def __init__(self, line: int, column: int, message: str):
        self.line = line
        self.column = column
        self.message = message

    def __str__(self) -> str:
        return "line {}:{}: {}".format(self.line, self.column, self.message)


class ParseResult:
    __slots__ = ("root", "issues", "brace_balance")

    def __init__(self, root: Block, issues: List[ParseIssue], brace_balance: int):
        self.root = root
        self.issues = issues
        self.brace_balance = brace_balance


class LocEntry:
    __slots__ = ("key", "value", "path", "line")

    def __init__(self, key: str, value: str, path: str, line: int):
        self.key = key
        self.value = value
        self.path = path
        self.line = line


def read(path: Union[str, Path]) -> str:
    """Read UTF-8 (with optional BOM) without silently replacing bad bytes."""
    p = Path(path)
    try:
        return p.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AuditInputError("{}: невалидный UTF-8 около байта {}".format(p, exc.start)) from exc
    except OSError as exc:
        raise AuditInputError("{}: {}".format(p, exc)) from exc


def tokenize(text: str) -> Tuple[List[Token], List[ParseIssue]]:
    """Tokenize HOI4 script while respecting comments, escaped quotes and strings."""
    tokens: List[Token] = []
    issues: List[ParseIssue] = []
    i, line, column, n = 0, 1, 1, len(text)

    def advance(chunk: str) -> None:
        nonlocal line, column
        newlines = chunk.count("\n")
        if newlines:
            line += newlines
            column = len(chunk.rsplit("\n", 1)[-1]) + 1
        else:
            column += len(chunk)

    while i < n:
        ch = text[i]
        if ch.isspace():
            advance(ch)
            i += 1
            continue
        if ch == "#":
            end = text.find("\n", i)
            if end < 0:
                advance(text[i:])
                break
            advance(text[i:end])
            i = end
            continue

        start, start_line, start_col = i, line, column
        if ch in "{}=":
            kind = {"{": "LBRACE", "}": "RBRACE", "=": "EQUAL"}[ch]
            tokens.append(Token(kind, ch, start_line, start_col, start))
            advance(ch)
            i += 1
            continue

        if ch == '"':
            i += 1
            advance('"')
            value: List[str] = []
            closed = False
            while i < n:
                cur = text[i]
                if cur == "\\" and i + 1 < n:
                    nxt = text[i + 1]
                    if nxt in ('"', "\\"):
                        value.append(nxt)
                    else:
                        value.append("\\")
                        value.append(nxt)
                    chunk = text[i:i + 2]
                    advance(chunk)
                    i += 2
                    continue
                if cur == '"':
                    advance(cur)
                    i += 1
                    closed = True
                    break
                value.append(cur)
                advance(cur)
                i += 1
            tokens.append(Token("STRING", "".join(value), start_line, start_col, start))
            if not closed:
                issues.append(ParseIssue(start_line, start_col, "незакрытая строка"))
            continue

        while i < n and not text[i].isspace() and text[i] not in '#{}="':
            i += 1
        if i == start:
            issues.append(ParseIssue(line, column, "неожиданный символ {!r}".format(ch)))
            advance(ch)
            i += 1
            continue
        value = text[start:i]
        tokens.append(Token("ATOM", value, start_line, start_col, start))
        advance(value)

    tokens.append(Token("EOF", "", line, column, n))
    return tokens, issues


class HOIParser:
    """Small structural parser for HOI4 key/value files; preserves duplicate keys."""

    def __init__(self, tokens: Sequence[Token], issues: Optional[List[ParseIssue]] = None):
        self.tokens = tokens
        self.pos = 0
        self.issues = issues if issues is not None else []
        self.open_braces = 0
        self.close_braces = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def consume(self) -> Token:
        token = self.current()
        if token.kind != "EOF":
            self.pos += 1
        return token

    def parse(self) -> Block:
        return self.parse_items(expect_close=False, opening_line=1)

    def parse_items(self, expect_close: bool, opening_line: int) -> Block:
        block = Block(line=opening_line)
        while self.current().kind != "EOF":
            token = self.current()
            if token.kind == "RBRACE":
                self.close_braces += 1
                self.consume()
                if expect_close:
                    return block
                self.issues.append(ParseIssue(token.line, token.column, "лишняя закрывающая скобка '}'"))
                continue
            if token.kind == "LBRACE":
                self.open_braces += 1
                self.consume()
                child = self.parse_items(expect_close=True, opening_line=token.line)
                block.items.append(Entry(Token("ATOM", "<anonymous>", token.line, token.column, token.offset), child))
                continue
            if token.kind not in ("ATOM", "STRING"):
                self.issues.append(ParseIssue(token.line, token.column, "ожидалось имя параметра, получено {}".format(token.kind)))
                self.consume()
                continue

            key = self.consume()
            if self.current().kind != "EQUAL":
                # Bare values are valid in lists such as search_filters = { FOCUS_FILTER_ECONOMY }.
                block.items.append(key)
                continue
            self.consume()  # '='
            value_token = self.current()
            if value_token.kind == "LBRACE":
                self.consume()
                self.open_braces += 1
                value: Union[Token, Block] = self.parse_items(expect_close=True, opening_line=value_token.line)
            elif value_token.kind in ("ATOM", "STRING"):
                value = self.consume()
            else:
                self.issues.append(ParseIssue(value_token.line, value_token.column, "у параметра {!r} отсутствует значение".format(key.value)))
                continue
            block.items.append(Entry(key, value))

        if expect_close:
            self.issues.append(ParseIssue(opening_line, 1, "блок '{' не закрыт"))
        return block


def parse_hoi(text: str) -> ParseResult:
    tokens, issues = tokenize(text)
    parser = HOIParser(tokens, issues)
    root = parser.parse()
    return ParseResult(root, parser.issues, parser.open_braces - parser.close_braces)


def _structural_signature(value):
    """Return a location-independent signature for a parsed HOI block/value."""
    if isinstance(value, Token):
        return ("token", value.kind, value.value)
    if isinstance(value, Block):
        items = []
        for item in value.items:
            if isinstance(item, Token):
                items.append(("token", item.kind, item.value))
            elif isinstance(item, Entry):
                items.append(("entry", item.key.value, _structural_signature(item.value)))
        return ("block", tuple(items))
    return ("unknown", type(value).__name__)


def walk_entries(block: Block) -> Iterator[Entry]:
    for item in block.items:
        if isinstance(item, Entry):
            yield item
            if isinstance(item.value, Block):
                yield from walk_entries(item.value)


def direct_entries(block: Block, key: str) -> List[Entry]:
    return [item for item in block.items if isinstance(item, Entry) and item.key.value == key]


def nested_entries(block: Block, key: str) -> List[Entry]:
    return [entry for entry in walk_entries(block) if entry.key.value == key]


def scalar(entry: Optional[Entry]) -> Optional[str]:
    if entry is not None and isinstance(entry.value, Token):
        return entry.value.value
    return None


def get_scalar(block: Block, key: str) -> Optional[str]:
    for entry in direct_entries(block, key):
        value = scalar(entry)
        if value is not None:
            return value
    return None


def get_block(block: Block, key: str) -> Optional[Block]:
    for entry in direct_entries(block, key):
        if isinstance(entry.value, Block):
            return entry.value
    return None


def find_named_blocks(block: Block, key: str) -> List[Block]:
    return [entry.value for entry in walk_entries(block) if entry.key.value == key and isinstance(entry.value, Block)]


def iter_files(root: Path, suffix: str) -> List[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == suffix.lower())


EVENT_CALL_KEYS = frozenset(("country_event", "news_event"))


def iter_event_calls(block: Block):
    """Yield real event calls in both scalar and block syntax; skip display-only tooltips."""
    def visit(current: Block):
        for item in current.items:
            if not isinstance(item, Entry):
                continue
            if item.key.value in EVENT_CALL_KEYS:
                event_id = item.value.value if isinstance(item.value, Token) else get_scalar(item.value, "id")
                if event_id:
                    yield item.key.value, event_id, item.line
            if isinstance(item.value, Block) and item.key.value != "effect_tooltip":
                yield from visit(item.value)

    yield from visit(block)


PARSE_ERROR_FIELDS = (
    "parse_errors", "source_parse_errors", "mio_parse_errors",
    "equipment_parse_errors", "module_parse_errors", "technology_parse_errors",
    "script_parse_errors",
)


def reports_have_parse_errors(*reports) -> bool:
    """Return True if any report contains a parser failure from any audit subsystem."""
    return any(bool(report.get(field)) for report in reports for field in PARSE_ERROR_FIELDS)


def _state_flow_script_files(directory: Path) -> List[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.rglob("*")
        if path.is_file() and (path.suffix.lower() == ".txt" or not path.suffix)
    )
