"""Verify str.format placeholders match between ZH/EN tables and call sites."""

import ast
import os
import sys
import string

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from oscill.i18n import EN_US_TEXTS, ZH_CN_TEXTS  # noqa: E402


def fields(text: str) -> set[str]:
    try:
        return {fname for _, fname, _, _ in string.Formatter().parse(text) if fname}
    except ValueError:
        return set()


problems: list[str] = []

# 1) ZH vs EN placeholder parity.
for key in ZH_CN_TEXTS:
    zhf, enf = fields(ZH_CN_TEXTS[key]), fields(EN_US_TEXTS.get(key, ""))
    if zhf != enf:
        problems.append(f"[TABLE {key}] ZH fields {zhf} != EN fields {enf}")

# 2) Call-site kwargs vs table placeholders.
for rel in ("oscill/gui.py", "oscill/cli.py"):
    path = os.path.join(ROOT, rel)
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        is_tr = (
            (isinstance(node.func, ast.Attribute) and node.func.attr == "tr")
            or (isinstance(node.func, ast.Name) and node.func.id == "t")
        )
        if not is_tr or not node.args:
            continue
        first = node.args[0]
        # Only static keys can be checked here; f-string profile./task. keys
        # have no placeholders by construction.
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            continue
        key = first.value
        kwargs_given = {kw.arg for kw in node.keywords if kw.arg}
        expected = fields(ZH_CN_TEXTS.get(key, ""))
        if kwargs_given != expected:
            problems.append(
                f"[CALL {rel}:{node.lineno} {key}] table fields {expected} "
                f"but call passes {kwargs_given}"
            )

if problems:
    print("FORMAT PROBLEMS:")
    print("\n".join(problems))
    sys.exit(1)
print("FORMAT CHECK OK: all ZH/EN placeholders match and every call passes the correct kwargs")
