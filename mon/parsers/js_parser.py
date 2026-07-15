"""JavaScript intelligence.

Everything in this module is a pure function (or returns a small immutable
dataclass) operating on a string of JS source -- nothing here touches the
network or the filesystem, which keeps it trivially unit-testable in
isolation from the rest of the engine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# String/comment/template-literal-aware brace matching
# --------------------------------------------------------------------------- #


def find_matching_close_brace(text: str, open_brace_index: int, max_scan: int = 20_000) -> int | None:
    """Return the index of the ``}`` that closes the ``{`` at ``open_brace_index``.

    Unlike a naive character count, this is aware of:
      * single- and double-quoted strings (braces inside them are ignored)
      * template literals, including nested ``${ ... }`` expressions (braces
        *inside* a ``${}`` expression DO count, since they are real JS syntax)
      * line comments (``//...``) and block comments (``/* ... */``)

    Returns ``None`` if no balanced close is found within ``max_scan``
    characters (an intentional safety cap against pathological/minified input).
    """
    if open_brace_index >= len(text) or text[open_brace_index] != "{":
        return None

    limit = min(len(text), open_brace_index + max_scan)
    i = open_brace_index
    depth = 0
    template_stack: list[int] = []
    state = "NORMAL"
    quote_char = ""

    while i < limit:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < limit else ""

        if state == "NORMAL":
            if ch == "/" and nxt == "/":
                state = "LINE_COMMENT"
                i += 2
                continue
            if ch == "/" and nxt == "*":
                state = "BLOCK_COMMENT"
                i += 2
                continue
            if ch in ("'", '"'):
                state = "STRING"
                quote_char = ch
                i += 1
                continue
            if ch == "`":
                state = "TEMPLATE"
                i += 1
                continue
            if ch == "{":
                depth += 1
                i += 1
                continue
            if ch == "}":
                depth -= 1
                if template_stack and depth == template_stack[-1]:
                    template_stack.pop()
                    state = "TEMPLATE"
                    i += 1
                    continue
                if depth == 0:
                    return i
                i += 1
                continue
            i += 1
            continue

        if state == "STRING":
            if ch == "\\":
                i += 2
                continue
            if ch == quote_char:
                state = "NORMAL"
            i += 1
            continue

        if state == "TEMPLATE":
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                state = "NORMAL"
                i += 1
                continue
            if ch == "$" and nxt == "{":
                template_stack.append(depth)
                depth += 1
                state = "NORMAL"
                i += 2
                continue
            i += 1
            continue

        if state == "LINE_COMMENT":
            if ch == "\n":
                state = "NORMAL"
            i += 1
            continue

        if state == "BLOCK_COMMENT":
            if ch == "*" and nxt == "/":
                state = "NORMAL"
                i += 2
                continue
            i += 1
            continue

    return None


# --------------------------------------------------------------------------- #
# Function-boundary + name detection
# --------------------------------------------------------------------------- #

_FUNC_DECLARATION_PATTERNS: tuple[str, ...] = (
    r"(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*[a-zA-Z0-9_$]*\s*\([^)]*\)\s*\{",
    r"(?:export\s+)?(?:const|let|var)\s+[a-zA-Z0-9_$]+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>\s*\{",
    r"(?:export\s+)?(?:const|let|var)\s+[a-zA-Z0-9_$]+\s*=\s*(?:async\s*)?function\s*\([^)]*\)\s*\{",
    r"[a-zA-Z0-9_$]+\s*:\s*(?:async\s*)?function\s*\([^)]*\)\s*\{",
    # class/object method shorthand -- lowest priority. Control-flow keywords
    # (if/for/while/switch/catch/...) are excluded directly in the pattern via
    # negative lookahead, since they would otherwise match this shape too.
    r"(?:async\s+)?(?!if\b|for\b|while\b|switch\b|catch\b|function\b|return\b|else\b|do\b|with\b)"
    r"[a-zA-Z0-9_$]+\s*\([^)]*\)\s*\{",
)
_BACKWARD_SEARCH_WINDOW = 6_000


@dataclass(slots=True)
class FunctionSnippet:
    code: str
    function_name: str | None
    method: str
    """'function_boundary' (brace-matched, high confidence) or 'char_window' (fallback)."""


def _extract_declaration_name(declaration_text: str) -> str | None:
    m = re.search(r"function\s*\*?\s*([a-zA-Z0-9_$]+)", declaration_text)
    if m and m.group(1):
        return m.group(1)
    m = re.search(r"(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=", declaration_text)
    if m:
        return m.group(1)
    m = re.search(r"([a-zA-Z0-9_$]+)\s*:\s*(?:async\s*)?function", declaration_text)
    if m:
        return m.group(1)
    # method-shorthand fallback: 'name(' or 'async name('
    m = re.search(r"(?:async\s+)?([a-zA-Z0-9_$]+)\s*\(", declaration_text)
    if m:
        return m.group(1)
    return None


def _find_enclosing_declaration(js_content: str, near_index: int) -> tuple[int, str] | None:
    """Search backward from ``near_index`` for every candidate function-like
    declaration, then keep only the ones whose brace-matched body actually
    CONTAINS ``near_index`` (verified via forward scanning, not just text
    proximity). Among valid candidates, the innermost one wins -- i.e. the
    declaration whose opening brace is closest to (but still before)
    ``near_index``, so a nested class-method isn't mistaken for its
    surrounding class/function.
    """
    window_start = max(0, near_index - _BACKWARD_SEARCH_WINDOW)
    search_area = js_content[window_start:near_index + 1]

    candidates: list[tuple[int, str, int]] = []
    for pattern_index, pattern in enumerate(_FUNC_DECLARATION_PATTERNS):
        for m in re.finditer(pattern, search_area):
            open_brace_index = window_start + m.end() - 1
            if open_brace_index >= len(js_content) or js_content[open_brace_index] != "{":
                continue
            candidates.append((open_brace_index, m.group(0), pattern_index))

    valid: list[tuple[int, str, int, int]] = []
    for open_brace_index, decl_text, pattern_index in candidates:
        close_index = find_matching_close_brace(js_content, open_brace_index)
        if close_index is None:
            continue
        if open_brace_index <= near_index <= close_index:
            valid.append((open_brace_index, decl_text, pattern_index, close_index))

    if not valid:
        return None

    # Innermost first (largest open_brace_index); ties broken by pattern
    # specificity (lower pattern_index = more reliable pattern).
    valid.sort(key=lambda c: (-c[0], c[2]))
    open_brace_index, decl_text, _, _ = valid[0]
    return open_brace_index, decl_text


def extract_function_snippet(js_content: str, match_index: int,
                              fallback_chars: int = 1_500) -> FunctionSnippet:
    """Extract the full enclosing function body around ``match_index`` (the
    position of a detected API call). Falls back to a fixed character window
    if no clean function boundary can be found (e.g. severely minified code).
    """
    found = _find_enclosing_declaration(js_content, match_index)
    if found:
        open_brace_index, declaration_text = found
        close_brace_index = find_matching_close_brace(js_content, open_brace_index)
        if close_brace_index is not None:
            decl_start = open_brace_index - len(declaration_text) + 1
            code = js_content[decl_start:close_brace_index + 1]
            name = _extract_declaration_name(declaration_text)
            return FunctionSnippet(code=code.strip(), function_name=name, method="function_boundary")

    start = max(0, match_index - fallback_chars)
    end = min(len(js_content), match_index + fallback_chars)
    return FunctionSnippet(code=js_content[start:end].strip(), function_name=None, method="char_window")


# --------------------------------------------------------------------------- #
# Multi-library call-site detection
# --------------------------------------------------------------------------- #

@dataclass(slots=True)
class RawCallMatch:
    match_index: int
    endpoint_path: str
    http_method: str
    call_style: str
    wrapper_function_name: str


_METHOD_KEY_IN_OBJECT = re.compile(r"\b(?:method|type)\s*:\s*['\"`](GET|POST|PUT|DELETE|PATCH)['\"`]", re.IGNORECASE)


def _detect_method_from_call_tail(js_content: str, after_index: int, search_window: int = 400) -> str:
    """For calls like fetch(url, {method: "POST", ...}) or auegj(url, payload),
    look at what follows the URL argument to guess the HTTP method:
      * an options object containing method:/type: -> use that value
      * an options object with no explicit method -> assume POST (an object
        argument almost always carries a body, which implies a non-GET verb)
      * no second argument at all -> assume GET
    """
    tail = js_content[after_index:after_index + search_window]
    comma_pos = tail.find(",")
    paren_close_pos = tail.find(")")
    has_second_arg = comma_pos != -1 and (paren_close_pos == -1 or comma_pos < paren_close_pos)
    if not has_second_arg:
        return "GET"

    brace_pos = tail.find("{")
    if brace_pos != -1 and (paren_close_pos == -1 or brace_pos < paren_close_pos):
        absolute_brace = after_index + brace_pos
        close = find_matching_close_brace(js_content, absolute_brace)
        if close is not None:
            obj_text = js_content[absolute_brace:close + 1]
            m = _METHOD_KEY_IN_OBJECT.search(obj_text)
            if m:
                return m.group(1).upper()
    return "POST"


_URL_LITERAL = r"(?P<quote>['\"`])(?P<urlval>(?:/[^'\"`]*)|(?:https?://[^'\"`]+))(?P=quote)"

# 1a. 'await <anything>("/path")' -- covers fetch(), apiCall(), and any
#     arbitrarily-renamed custom wrapper (e.g. 'auegj') in one pattern, since
#     it matches on CALL STRUCTURE rather than the callee's name.
_GENERIC_AWAIT_CALL = re.compile(rf"await\s+(?P<wrapper>[a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(\s*{_URL_LITERAL}")

# 1b. Bare 'fetch("/path")...' with no await -- covers promise-chain style
#     calls (fetch(url).then(r => r.json()).then(...)), which the await-only
#     pattern above does not match. Restricted to the literal name 'fetch'
#     (a reserved global, safe to key on by name); a bare custom-named
#     wrapper used without await/then cannot be distinguished from an
#     unrelated function call without additional context.
_BARE_FETCH_CALL = re.compile(rf"\bfetch\s*\(\s*{_URL_LITERAL}")

# 2. axios / ky -- both support `lib(url, cfg)` and `lib.verb(url, cfg)`
_AXIOS_KY_CALL = re.compile(
    rf"\b(?P<lib>axios|ky)\s*(?:\.\s*(?P<verb>get|post|put|delete|patch|head)\s*)?\(\s*{_URL_LITERAL}"
)

# 3. superagent.verb(url)
_SUPERAGENT_CALL = re.compile(rf"\bsuperagent\s*\.\s*(?P<verb>get|post|put|delete|patch)\s*\(\s*{_URL_LITERAL}")

# 4. jQuery/$.ajax({ url: "...", method/type: "..." , ... })  -- url is a
#    named object key, not a positional argument, so this needs its own shape.
_JQUERY_AJAX_CALL = re.compile(r"(?:\$|jQuery)\s*\.\s*ajax\s*\(\s*\{")
_JQUERY_URL_KEY = re.compile(rf"\burl\s*:\s*{_URL_LITERAL}")
_JQUERY_METHOD_KEY = re.compile(r"\b(?:method|type)\s*:\s*['\"`](GET|POST|PUT|DELETE|PATCH)['\"`]", re.IGNORECASE)

# 5. XMLHttpRequest: xhr.open("POST", "/path")
_XHR_OPEN_CALL = re.compile(
    rf"\.open\s*\(\s*['\"`](?P<method>GET|POST|PUT|DELETE|PATCH)['\"`]\s*,\s*{_URL_LITERAL}"
)


def find_call_sites(js_content: str) -> list[RawCallMatch]:
    """Scan JS source for every recognizable outbound API call, across every
    call style MON knows about (fetch/custom-wrapper, axios, ky, superagent,
    jQuery.ajax, raw XMLHttpRequest)."""
    matches: list[RawCallMatch] = []

    for m in _GENERIC_AWAIT_CALL.finditer(js_content):
        wrapper = m.group("wrapper")
        style = "fetch" if wrapper == "fetch" else "custom_wrapper"
        matches.append(RawCallMatch(
            match_index=m.start(), endpoint_path=m.group("urlval"),
            http_method=_detect_method_from_call_tail(js_content, m.end()),
            call_style=style, wrapper_function_name=wrapper,
        ))

    for m in _BARE_FETCH_CALL.finditer(js_content):
        matches.append(RawCallMatch(
            match_index=m.start(), endpoint_path=m.group("urlval"),
            http_method=_detect_method_from_call_tail(js_content, m.end()),
            call_style="fetch", wrapper_function_name="fetch",
        ))

    for m in _AXIOS_KY_CALL.finditer(js_content):
        lib, verb = m.group("lib"), m.group("verb")
        method = verb.upper() if verb else _detect_method_from_call_tail(js_content, m.end())
        matches.append(RawCallMatch(
            match_index=m.start(), endpoint_path=m.group("urlval"),
            http_method=method, call_style=lib, wrapper_function_name=lib,
        ))

    for m in _SUPERAGENT_CALL.finditer(js_content):
        matches.append(RawCallMatch(
            match_index=m.start(), endpoint_path=m.group("urlval"),
            http_method=m.group("verb").upper(), call_style="superagent",
            wrapper_function_name="superagent",
        ))

    for m in _XHR_OPEN_CALL.finditer(js_content):
        matches.append(RawCallMatch(
            match_index=m.start(), endpoint_path=m.group("urlval"),
            http_method=m.group("method").upper(), call_style="xhr",
            wrapper_function_name="XMLHttpRequest",
        ))

    for m in _JQUERY_AJAX_CALL.finditer(js_content):
        obj_start = m.end() - 1  # index of the '{'
        obj_end = find_matching_close_brace(js_content, obj_start)
        if obj_end is None:
            continue
        obj_text = js_content[obj_start:obj_end + 1]
        url_match = _JQUERY_URL_KEY.search(obj_text)
        if not url_match:
            continue
        method_match = _JQUERY_METHOD_KEY.search(obj_text)
        matches.append(RawCallMatch(
            match_index=m.start(), endpoint_path=url_match.group("urlval"),
            http_method=(method_match.group(1).upper() if method_match else "GET"),
            call_style="jquery_ajax", wrapper_function_name="$.ajax",
        ))

    matches.sort(key=lambda c: c.match_index)
    return _deduplicate_overlapping(matches)


def _deduplicate_overlapping(matches: list[RawCallMatch], proximity: int = 15) -> list[RawCallMatch]:
    """If two matches point at the same endpoint within a few characters of
    each other, they are almost certainly the same call site detected twice
    by two different patterns (e.g. 'await fetch(' matches both the
    await-pattern and the bare-fetch pattern) -- keep only the first."""
    kept: list[RawCallMatch] = []
    for candidate in matches:
        is_duplicate = any(
            candidate.endpoint_path == existing.endpoint_path
            and abs(candidate.match_index - existing.match_index) <= proximity
            for existing in kept
        )
        if not is_duplicate:
            kept.append(candidate)
    return kept


# --------------------------------------------------------------------------- #
# Client-side navigation target detection
# --------------------------------------------------------------------------- #
#
# Distinct from find_call_sites(): those functions locate API calls (JSON
# endpoints, not crawlable pages). This section locates paths the client
# navigates the BROWSER to -- window.location assignments, SPA router
# push/replace calls, and history API calls -- which are real pages a
# crawler should visit, but which never appear as a plain <a href="..."> in
# the HTML because the navigation only happens at runtime (e.g. a redirect
# to /dashboard issued from JavaScript after a successful login).

_NAVIGATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"window\.location(?:\.href)?\s*=\s*['\"`](/[^'\"`]*)['\"`]"),
    re.compile(r"\blocation\.href\s*=\s*['\"`](/[^'\"`]*)['\"`]"),
    re.compile(r"window\.location\.(?:assign|replace)\s*\(\s*['\"`](/[^'\"`]*)['\"`]"),
    re.compile(r"\.(?:push|replace)\s*\(\s*['\"`](/[^'\"`]*)['\"`]"),  # router.push/replace
    re.compile(r"history\.(?:pushState|replaceState)\s*\([^,]*,[^,]*,\s*['\"`](/[^'\"`]*)['\"`]"),
)


def find_navigation_targets(js_content: str) -> list[str]:
    """Return every same-site path the JS navigates the browser to at
    runtime, suitable for feeding into the crawl queue alongside paths
    discovered from <a href> tags."""
    targets: set[str] = set()
    for pattern in _NAVIGATION_PATTERNS:
        for m in pattern.finditer(js_content):
            targets.add(m.group(1))
    return sorted(targets)


# --------------------------------------------------------------------------- #
# Payload key extraction
# --------------------------------------------------------------------------- #

_PAYLOAD_IGNORED_KEYS = frozenset({"method", "headers", "body", "status", "mode", "credentials"})


def extract_payload_keys(function_body: str) -> list[str]:
    keys: set[str] = set()

    for key in re.findall(r"\.(?:append|set)\(\s*['\"`]([a-zA-Z0-9_]+)['\"`]", function_body):
        keys.add(key)

    for block in re.findall(r"URLSearchParams\(\s*\{(.*?)\}", function_body, re.DOTALL):
        keys.update(re.findall(r"([a-zA-Z0-9_]+)\s*:", block))

    for key in re.findall(r"\{\s*([a-zA-Z0-9_]+)\s*:", function_body):
        if key not in _PAYLOAD_IGNORED_KEYS:
            keys.add(key)

    return sorted(keys)


def detect_payload_format(js_content: str) -> str:
    if "URLSearchParams" in js_content or "application/x-www-form-urlencoded" in js_content:
        return "Parameters (application/x-www-form-urlencoded)"
    if "FormData" in js_content:
        return "Multipart FormData (multipart/form-data)"
    return "Raw JSON (application/json)"


def detect_base_api_url(js_content: str) -> str:
    m = re.search(r'const\s+API_BASE_URL\s*=\s*[\'"`]([^\'"`]+)[\'"`]', js_content)
    return m.group(1) if m else "../api"


# --------------------------------------------------------------------------- #
# Branch splitting (success vs error) + name-agnostic variable/schema detection
# --------------------------------------------------------------------------- #

_DISCRIMINATOR_HINTS = ("status", "success", "ok", "error", "isError", "code")


@dataclass(slots=True)
class BranchSplit:
    success_branch: str
    error_branch: str
    detected: bool


def split_success_error_branches(function_body: str) -> BranchSplit:
    if_pattern = re.compile(
        r"if\s*\(\s*(!?)\s*[a-zA-Z0-9_.\[\]'\"]*\.(?:%s)\b[^)]*\)\s*\{" % "|".join(_DISCRIMINATOR_HINTS),
        re.IGNORECASE,
    )
    m = if_pattern.search(function_body)

    if not m:
        catch_match = re.search(r"catch\s*\([^)]*\)\s*\{(.*)\}\s*$", function_body, re.DOTALL)
        if catch_match:
            return BranchSplit(
                success_branch=function_body[:catch_match.start()],
                error_branch=catch_match.group(1),
                detected=True,
            )
        return BranchSplit(success_branch=function_body, error_branch="", detected=False)

    brace_start = function_body.index("{", m.end() - 1)
    close_index = find_matching_close_brace(function_body, brace_start)
    if close_index is None:
        return BranchSplit(success_branch=function_body, error_branch="", detected=False)

    error_branch = function_body[brace_start + 1:close_index]
    success_branch = function_body[:m.start()] + function_body[close_index + 1:]
    return BranchSplit(success_branch=success_branch, error_branch=error_branch, detected=True)


_FALLBACK_RESPONSE_NAMES = frozenset({"result", "data", "response", "res"})


def detect_response_variable_names(function_body: str) -> set[str]:
    """Find the actual variable name(s) holding the parsed JSON response in
    THIS function -- regardless of whether the code uses conventional names
    (res/data) or obfuscated ones (e.g. 'grjdbsj'). Detection is based on
    assignment/callback STRUCTURE, never on a fixed name list."""
    detected: set[str] = set()

    for m in re.finditer(
        r"(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*await\s+[a-zA-Z0-9_$.]+\.json\s*\(\s*\)",
        function_body,
    ):
        detected.add(m.group(1))

    for m in re.finditer(
        r"(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*await\s+[a-zA-Z_$][a-zA-Z0-9_$.]*\s*\(",
        function_body,
    ):
        detected.add(m.group(1))

    for m in re.finditer(
        r"\.then\s*\(\s*(?:function\s*)?\(?\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\)?\s*=>",
        function_body,
    ):
        detected.add(m.group(1))
    for m in re.finditer(r"\.then\s*\(\s*function\s*\(\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\)", function_body):
        detected.add(m.group(1))

    return detected


def build_dotted_path_pattern(response_var_names: set[str]) -> re.Pattern[str]:
    all_names = response_var_names | _FALLBACK_RESPONSE_NAMES
    escaped = sorted((re.escape(n) for n in all_names), key=len, reverse=True)
    return re.compile(r"(?:%s)((?:\.[a-zA-Z0-9_$]+)+)" % "|".join(escaped))


_ARRAY_OR_METHOD_TERMINATORS = frozenset({
    "map", "forEach", "filter", "reduce", "some", "every", "includes",
    "length", "slice", "join", "push", "pop", "then", "catch", "json",
    "text", "find", "sort", "flat", "flatMap", "toString",
})


def _strip_method_suffix(parts: list[str]) -> tuple[list[str], bool]:
    is_array = False
    while parts and parts[-1] in _ARRAY_OR_METHOD_TERMINATORS:
        parts = parts[:-1]
        is_array = True
    return parts, is_array


def _looks_like_array_usage(text: str, dotted_key: str) -> bool:
    escaped = re.escape("." + dotted_key)
    return bool(re.search(rf"{escaped}\s*(?:\.map\(|\.forEach\(|\.length\b|\[\d+\])", text))


def build_schema(branch_text: str, dotted_pattern: re.Pattern[str]) -> dict:
    """Build a nested schema dict from every dotted response-field access
    found in ``branch_text`` (e.g. 'data.wallet.balance' -> nested dict),
    detecting arrays via trailing .map()/.forEach()/.length/[n] usage."""
    schema: dict = {}
    seen: set[str] = set()

    for m in dotted_pattern.finditer(branch_text):
        parts = [p for p in m.group(1).split(".") if p]
        if not parts:
            continue
        parts, stripped_array = _strip_method_suffix(parts)
        if not parts:
            continue
        dotted_name = ".".join(parts)
        if dotted_name in seen:
            continue
        seen.add(dotted_name)
        is_array = stripped_array or _looks_like_array_usage(branch_text, dotted_name)

        cursor = schema
        for idx, part in enumerate(parts):
            is_last = idx == len(parts) - 1
            if is_last:
                lower = part.lower()
                if lower == "id":
                    cursor[part] = "TYPE_NUMBER"
                elif "email" in lower:
                    cursor[part] = "TYPE_STRING"
                elif any(k in lower for k in ("amount", "balance", "price")):
                    cursor[part] = "TYPE_NUMBER"
                elif is_array:
                    cursor[part] = ["TYPE_ARRAY_OF_OBJECTS"]
                else:
                    cursor[part] = "TYPE_UNKNOWN_DETERMINED_BY_JS"
            else:
                if part not in cursor or not isinstance(cursor[part], dict):
                    cursor[part] = {}
                cursor = cursor[part]

    return schema
