# Environment

## Conda env
- **`biomni_e1`** (`ml conda; conda activate biomni_e1`).

## Dependencies
George depends on the **patched Biomni fork**, editable-installed:

```bash
conda activate biomni_e1
pip install -e ../biomni-fork          # the patched Biomni package (own repo)
pip install duckdb pyarrow             # AlphaGenome DuckDB/Parquet backend
```

The editable install replaces the old `sys.path.append("./")` shadowing so
`import biomni` is unambiguous.

## Verification
```bash
cd /tmp && python -c "import biomni, os; print(os.path.dirname(biomni.__file__))"
# must print .../biomni-fork/biomni  (NOT the old repo, NOT site-packages/biomni 0.0.8)
python -c "from biomni.llm import _anthropic_rejects_sampling_params as f; print(f('claude-opus-4-8'))"  # -> True
python -c "import duckdb, biomni; print('ok')"
```

## Secrets
API keys live in `.env` only (copied from the old repo; never committed).
