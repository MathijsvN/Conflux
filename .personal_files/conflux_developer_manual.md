# 🎛 **Conflux Developer Manual**

*A practical guide for maintaining, extending, and contributing to the Conflux translation toolkit.*

This guide gives you **simple workflows** for the things you will do most often:

*   Adding a new translator (e.g., DatalogMTL → LARS)
*   Adding tests
*   Adding a new SR framework
*   Updating the IR
*   Running tests, linting, CI
*   Working with the CLI
*   Documenting new features
*   Keeping the codebase clean

Each workflow is designed to tell you **exactly which files to open**, **what to edit**, and **what to run**.

***

# 📁 1. Understanding the Repo Structure (Quick Mental Model)

You don’t need to remember every folder. You only need to know this mental model:

### 🔸 *Parsing layer*

`conflux/io/*.py`  
➡ Turns framework syntax → IR, and IR → framework syntax.

### 🔸 *Core IR layer*

`conflux/core/*.py`  
➡ Shared intermediate representation & plugin registry.

### 🔸 *Translators layer*

`conflux/translators/<A>_<B>`  
➡ Contains the **logic of mapping semantics** A → B.

### 🔸 *CLI layer*

`conflux/cli/conflux_cli.py`  
➡ User interface for commands like `conflux translate`.

### 🔸 *Tests*

`tests/...`  
➡ Ensures features work.

### 🔸 *Docs*

➡ Where you explain design and mappings.

This is all you really need.

***

# 🛠️ 2. Common Workflows

Below are the **most important workflows** you’ll use when developing Conflux.

***

## ⭐ Workflow A — *Start working on a new translation (A → B)*

Use this when you begin implementing a new translator direction.

### **Checklist**

1.  Create a directory:

<!---->

    conflux/translators/<a>_<b>/

Example:

    conflux/translators/datalogmtl_lars/

2.  Create these files (if not present):

<!---->

    __init__.py
    a_to_b.py
    b_to_a.py
    mapping_tables.py
    constraints.py

3.  Register both translators in `__init__.py`:

```python
from conflux.core.registry import register
from .a_to_b import AtoB
from .b_to_a import BtoA

register(AtoB())
register(BtoA())
```

4.  Implement the translator logic skeleton in `a_to_b.py`:

```python
class AtoB(Translator):
    src = "A"
    dst = "B"
    name = "A_to_B"

    def translate(self, ir, options=None):
        # TODO: implement mapping
        return ir

    def check_support(self, ir):
        # TODO: inspect unsupported operators
        return SimpleReport(ok=True)
```

5.  Write minimal tests in:

<!---->

    tests/translators/<a>_<b>/test_a_to_b.py

6.  Run tests:

```bash
pytest
```

### **Done!**

You now have a new translation direction.

***

## ⭐ Workflow B — *After adding a test*

Tests are your safety net. Whenever you add a test:

### **Checklist**

1.  Add your test under:

<!---->

    tests/translators/.../
    tests/io/.../
    tests/e2e/.../

2.  Confirm imports work:

```bash
pytest tests/<your-file>.py -q
```

3.  If the test fails:

*   Check if the translator is registered
*   Check if parser or IR fields exist
*   Check file names (`snake_case.py` is important)

4.  If everything passes, commit:

```bash
git add .
git commit -m "Add test for <feature>"
```

5.  Push and let CI run automatically (GitHub workflow).

***

## ⭐ Workflow C — *Add support for a new SR framework (e.g., RTEC)*

This is a bigger task, but straightforward.

### **Checklist**

1.  Add grammar (if parsing needed):

<!---->

    grammars/rtec.g4

2.  Add IO files:

<!---->

    conflux/io/parse_rtec.py
    conflux/io/emit_rtec.py

3.  Add translator directory:

<!---->

    conflux/translators/rtec_lars/
    conflux/translators/rtec_datalogmtl/

4.  Add entries to registry in each translator folder:

```python
register(RtecToLars())
register(LarsToRtec())
```

5.  Add tests:

<!---->

    tests/translators/rtec_lars/...

6.  Document the new language here:

<!---->

    docs/specs/rtec.md

7.  Test everything:

```bash
pytest
```

***

## ⭐ Workflow D — *Modify or extend the IR*

**Only do this when absolutely needed**, because IR changes affect everything downstream.

### **Checklist**

1.  Modify the dataclasses in:

<!---->

    conflux/core/ast.py

2.  Add or update validators:

<!---->

    conflux/core/ir_validators.py

3.  Update translators to handle new IR fields.

4.  Update parsers/emitters:

<!---->

    conflux/io/parse_*.py
    conflux/io/emit_*.py

5.  Add/adjust tests for the IR change.

6.  Document the IR update:

<!---->

    docs/design/architecture.md

***

## ⭐ Workflow E — *Run and test the CLI*

To test the CLI manually:

### **Checklist**

1.  Install project locally:

```bash
pip install -e .
```

2.  Run CLI:

```bash
conflux translate --from DatalogMTL --to LARS --in input.rules --out output.lars
```

3.  Test translator discovery:

```bash
conflux list
```

4.  Debug or log:

*   Add prints temporarily
*   Or add `logging.info(...)` inside translators

***

## ⭐ Workflow F — *Adding documentation for a new feature*

Follow this simple rule:

*   **If it affects users** → Add to `docs/index.md`
*   **If it affects architecture** → Add to `docs/design/...`
*   **If it affects a language** → Add to `docs/specs/...`

### **Checklist**

1.  Write/update `.md` files.
2.  Include examples in `docs/examples/`.
3.  If relevant, create diagrams or pseudocode.
4.  Keep docs brief but precise.

***

## ⭐ Workflow G — *Keeping the repo clean*

These housekeeping tasks prevent future chaos.

### **Checklist**

*   Remove unused imports:
    ```python
    from something import unused → delete
    ```

*   Follow naming conventions:
    *   `mtl_to_lars.py`
    *   `test_mtl_to_lars.py`
    *   `mapping_tables.py`

*   Run tests after every major change:
    ```bash
    pytest
    ```

*   Run optional formatters:
        black .
        isort .

*   Push often so CI catches issues early.

***

# 🧪 3. Testing Strategy Reference

*   Unit tests for each translator module
*   Round-trip tests:
    *   A → B → A should approximate original
*   Parser/emitter tests
*   Core IR tests
*   E2E tests for real datasets

***

# 🧰 4. Quick Reference Commands

### Run all tests

```bash
pytest
```

### Run specific test

```bash
pytest tests/translators/datalogmtl_lars/test_mtl_to_lars.py
```

### Install locally

```bash
pip install -e .
```

### CLI help

```bash
conflux --help
```

***

# 🎯 5. Mental Rules of Thumb

*   **Don’t change IR unless truly needed.**
*   **Always add tests for a new translator before coding the translator.**
*   **Keep parsing and translating separate.**
*   **Registry is your friend** — if something "doesn’t work", check registration.
*   **Document each decision** so future you remembers why.

***

# 📌 Want a printable PDF version of this guide?

I can generate a PDF with layout, headings, and icons. Just ask!
