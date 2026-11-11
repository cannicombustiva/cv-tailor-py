# Learning log

Concepts I could not explain without an agent. One entry per concept, in my own words.
Format: what I thought, what it is, TypeScript equivalent, source.

## 2026-11-08 · models.py

### Pydantic field name vs alias
- Thought: an alias was an object created from the model.
- Is: the external name of a field. Python uses `start_date`, JSON uses `startDate`.
  `alias_generator=to_camel` generates the alias for every field.
- TS: mapping snake_case to camelCase in a Zod transform.
- Source: https://docs.pydantic.dev/latest/concepts/alias/

### validate_by_name and validate_by_alias
- Thought: `alias_generator` is what lets me write `Role(start_date=...)`.
- Is: `alias_generator` decides how a field is named outside. `validate_by_alias` and
  `validate_by_name` decide which names are accepted as input. Both on = both accepted.
- Gotcha: `model_dump()` outputs field names. Use `model_dump(by_alias=True)` for camelCase.
- Source: https://docs.pydantic.dev/latest/api/config/

### extra="forbid"
- Is: unknown keys raise `ValidationError` (`extra_forbidden`). Default is "ignore", silently.
- Why here: a typo in the profile fails loudly instead of losing a fact.
- TS: `z.object({...}).strict()`

### frozen=True
- Is: instances are immutable after creation. Assignment raises `ValidationError`
  (`frozen_instance`). To change a value: `model.model_copy(update={...})`.
- Why here: no pipeline step can mutate the profile.
- TS: `Readonly<T>`, but enforced at runtime.

### Type hints are not enforced by Python
- Is: like TS types, hints are ignored at runtime. mypy checks code statically,
  Pydantic reads hints at runtime to validate data.
- TS: `tsc` + Zod.

## 2026-11-08 · cli.py

### Keyword arguments
- Thought: `prog` and `description` were aliases.
- Is: arguments passed by name, `ArgumentParser(prog="...", description="...")`.
- TS: an options object, `new ArgumentParser({ prog, description })`.

### main(argv: list[str] | None = None)
- Is: optional argument. With `None`, argparse reads `sys.argv[1:]`. Passing a list
  lets tests call `main(["profile.json", "job.txt"])` without a real terminal.

### Exit codes
- Thought: `return 1` terminates the program.
- Is: `main` returns an exit code, the caller passes it to `sys.exit()`.
  0 = success, non-zero = failure. CI relies on it. Errors go to `sys.stderr`.
- Source: https://docs.python.org/3/library/argparse.html

### pyproject.toml and [project.scripts]
- Is: TOML is a config format. `pyproject.toml` is Python's `package.json`.
  `cv-tailor-py = "cv_tailor_py.cli:main"` maps the command to a function.
- TS: the `bin` field in `package.json`.
- Source: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/

### if __name__ == "__main__":
- Is: `__name__` is `"__main__"` when the file is run directly, the module name when
  imported. Runs code only in the first case. Not needed here thanks to `[project.scripts]`.
- TS: `import.meta.main` (Deno), `require.main === module` (Node).
- Source: https://docs.python.org/3/library/__main__.html

### @traced (Braintrust)
- Thought: a Braintrust log named after the function.
- Is: a decorator that records a span for every call (input, output, duration, errors),
  nested under the parent span, so the trace shows the pipeline step by step.
  The span name defaults to the function name.
- TS: wrapTraced(fn).

### Decorators
- Is: `@something` above a function wraps it in another function that adds behaviour
  without changing its code.
- Source: https://docs.python.org/3/glossary.html#term-decorator

### Mocking OpenAI in tests
- Thought: a fake client created inside a fake_openai function.
- Is: a real OpenAI client wrapped by wrap_openai, with a test API key and an httpx
  MockTransport. The transport intercepts every HTTP request and returns a canned JSON
  response, so no network call leaves the machine. monkeypatch swaps the client used by
  the code for this fake one during the test only; pytest restores it afterwards.
- Why: the test covers the real path (request building, Braintrust wrapper, parsing into
  JobSpec), not just a stubbed function.
- Sources: https://www.python-httpx.org/advanced/transports/
  https://docs.pytest.org/en/stable/how-to/monkeypatch.html

  ### list vs dict
- Thought: I did not know the difference.
- Is: list = ordered sequence accessed by position. dict = key-value map accessed by key.
- Why here: strict structured output needs fixed field names, so the LLM returns a
  list of {id, text} objects and I convert it to a dict afterwards.
- TS: list = array, dict = object used as a map (or Map).
- Source: https://docs.python.org/3/tutorial/datastructures.html

## 2026-11-10 · rewrite_bullets

### Two classes for one result (RewriteOutput and Rewritten)
- Thought: they do the same thing, the split is about an OpenAI requirement.
- Is: same data in two shapes. RewriteOutput is what the LLM returns (bullets as a
  list of {id, text}). Rewritten is what the pipeline uses (bullets as dict id -> text).
  `to_rewritten()` converts one into the other.
- TS: a wire type and a domain type, with a mapper between them.
- Source: https://platform.openai.com/docs/guides/structured-outputs

### list vs dict
- Thought: I did not know the difference.
- Is: list = ordered sequence accessed by position. dict = key-value map accessed by key.
- Why here: strict structured output needs fixed field names. A dict keyed by
  achievement id has unknown keys, so the LLM returns a list of objects instead.
- TS: array vs object used as a map.
- Source: https://docs.python.org/3/tutorial/datastructures.html

### parse(response_format=SomeModel)
- Thought: I read `schema` as a JSON schema.
- Is: it is the Pydantic class itself. The SDK turns it into a JSON schema, sends it,
  validates the answer and returns an instance. `message.parsed` is None on refusal.
- TS: Zod schema passed to a structured output helper.
- Source: https://platform.openai.com/docs/guides/structured-outputs

### @cache on get_client()
- Is: builds the client on first call and reuses it. Importing the module needs no
  OPENAI_API_KEY, so CI works without one.
- Gotcha: the cached client survives between tests. Reset with `get_client.cache_clear()`
  or replace `get_client` with monkeypatch.
- Source: https://docs.python.org/3/library/functools.html#functools.cache

### monkeypatch and @cache
- Thought: (write what you assumed about the cached client in tests)
- Is: `monkeypatch.setattr(llm, "get_client", ...)` replaces the cached function itself
  on the module. `structured_call` looks it up at call time, so it gets the fake and
  the real client is never built.
- Guard: an autouse fixture makes `get_client` raise, so a test without `fake_openai`
  fails loudly instead of reaching the network.
- TS: `vi.spyOn(module, "getClient")` in Vitest.
- Source: https://docs.pytest.org/en/stable/how-to/monkeypatch.html

### Golden fixtures for port parity
- Thought: (write what you assumed before checking where golden.json came from)
- Is: expected outputs generated by running the TS code once and stored as a fixture.
  Python tests compare against them, so parity is checked against the original, not
  against itself.
- Gotcha: it is a snapshot. Regenerate it when the TS behavior changes.
- TS: snapshot testing, with the reference implementation as the source.