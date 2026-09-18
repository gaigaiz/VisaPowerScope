"""Platform-independent static checks (stdlib only).

Run on the Windows authoring machine; does NOT import PyQt5/pyqtgraph/pyvisa.
1. Every tr("...") literal key in gui.py/cli.py must exist in ZH_CN_TEXTS/EN_US_TEXTS.
2. Dynamic f-string keys profile.<x> / task.<x> must cover every profile/task id.
3. Report self.<attr> referenced but never assigned and not a method/class attr.
"""

import ast
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from oscill.i18n import (  # noqa: E402
    EN_US_TEXTS,
    MEASUREMENT_PROFILES,
    POWER_TASK_WORKLOADS,
    ZH_CN_TEXTS,
)


def literal_tr_keys(path: str) -> tuple[set[str], set[str]]:
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    literal_keys: set[str] = set()
    dynamic_prefixes: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        key_arg = None
        if isinstance(node.func, ast.Attribute) and node.func.attr == "tr" and node.args:
            key_arg = node.args[0]
        elif isinstance(node.func, ast.Name) and node.func.id == "t" and node.args:
            key_arg = node.args[0]
        if key_arg is None:
            continue
        if isinstance(key_arg, ast.Constant) and isinstance(key_arg.value, str):
            literal_keys.add(key_arg.value)
        elif isinstance(key_arg, ast.JoinedStr):
            prefix = ""
            for part in key_arg.values:
                prefix += part.value if isinstance(part, ast.Constant) else "{}"
            dynamic_prefixes.add(prefix)
    return literal_keys, dynamic_prefixes


def check_file(path: str) -> list[str]:
    problems: list[str] = []
    literal_keys, dynamic_prefixes = literal_tr_keys(path)
    for key in sorted(literal_keys):
        if key not in ZH_CN_TEXTS:
            problems.append(f"  [MISSING ZH] {key}")
        if key not in EN_US_TEXTS:
            problems.append(f"  [MISSING EN] {key}")
    for prefix in sorted(dynamic_prefixes):
        if prefix.startswith("profile."):
            for pid in MEASUREMENT_PROFILES:
                full = f"profile.{pid}"
                if full not in ZH_CN_TEXTS or full not in EN_US_TEXTS:
                    problems.append(f"  [DYNAMIC] {full} missing")
        elif prefix.startswith("task."):
            for tid in POWER_TASK_WORKLOADS:
                full = f"task.{tid}"
                if full not in ZH_CN_TEXTS or full not in EN_US_TEXTS:
                    problems.append(f"  [DYNAMIC] {full} missing")
        else:
            problems.append(f"  [UNKNOWN DYNAMIC PREFIX] {prefix}")
    return problems


def check_self_attrs(path: str) -> list[str]:
    """self.<attr> loaded but never stored, not a method, not a class attr."""
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    stored: set[str] = set()
    loaded: set[str] = set()
    class_members: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    class_members.add(item.name)
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            class_members.add(target.id)
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    class_members.add(item.target.id)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            if isinstance(node.ctx, ast.Store):
                stored.add(node.attr)
            elif isinstance(node.ctx, ast.Load):
                loaded.add(node.attr)
    # QMainWindow members used directly.
    qt_inherited = {"statusBar", "setWindowTitle", "resize", "setMinimumSize",
                    "setCentralWidget", "closeEvent"}
    return sorted(
        a for a in loaded
        if a not in stored and a not in class_members and a not in qt_inherited
    )


print("== i18n literal/dynamic key coverage ==")
all_ok = True
for rel in ("oscill/gui.py", "oscill/cli.py"):
    p = os.path.join(ROOT, rel)
    probs = check_file(p)
    if probs:
        all_ok = False
        print(f"{rel}: {len(probs)} problem(s)")
        print("\n".join(probs))
    else:
        nk = len(literal_tr_keys(p)[0])
        print(f"{rel}: all {nk} tr() keys present in ZH + EN")

print("\n== structural cross-checks ==")
prof_ids = {f"profile.{k}" for k in MEASUREMENT_PROFILES}
prof_zh = {k for k in ZH_CN_TEXTS if k.startswith("profile.")}
print("profile keys == MEASUREMENT_PROFILES:", prof_zh == prof_ids)
task_ids = {f"task.{k}" for k in POWER_TASK_WORKLOADS}
task_zh = {k for k in ZH_CN_TEXTS if k.startswith("task.")}
print("task keys == POWER_TASK_WORKLOADS:", task_zh == task_ids)
print("profile tuples all length 3:",
      all(len(v) == 3 for v in MEASUREMENT_PROFILES.values()))
print("ZH/EN table key sets identical:", set(ZH_CN_TEXTS) == set(EN_US_TEXTS))
print("total i18n keys:", len(ZH_CN_TEXTS))

print("\n== gui.py self.<attr> loaded-but-never-assigned (should be empty) ==")
leftover = check_self_attrs(os.path.join(ROOT, "oscill/gui.py"))
print(leftover if leftover else "  (none)")

print("\nRESULT:", "OK" if all_ok and not leftover else "HAS_PROBLEMS")
sys.exit(0 if all_ok and not leftover else 1)
