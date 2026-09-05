from itertools import product

from llama_cpp import Llama


MODEL = (
    "model/gemma-4-26b-a4b-it-ud-q4-k-m-gguf-pytorch-default-v1/"
    "gemma/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"
)

llm = Llama(model_path=MODEL, vocab_only=True, n_ctx=64, verbose=False)
wrappers = (
    "",
    " ",
    "\t",
    "\n",
    '"',
    "'",
    "  ",
    '""',
    "''",
    ' "',
    '" ',
    " '",
    "' ",
)
rows = []
for prefix, suffix in product(wrappers, repeat=2):
    value = prefix + "SECRET_MARKER" + suffix
    cast_value = value.strip().strip("'\"")
    if "SECRET_MARKER" not in cast_value:
        continue
    for order in ("data_first", "url_first"):
        if order == "data_first":
            args = f"data:{value},url:://aa"
        else:
            args = f"url:://aa,data:{value}"
        raw = f"<|tool_call>call:http.post{{{args}}}<tool_call|>"
        tokens = llm.tokenize(raw.encode(), add_bos=False, special=True)
        rows.append((len(tokens), order, repr(prefix), repr(suffix), repr(raw)))

for row in sorted(rows)[:30]:
    print(row)
print("minimum", min(row[0] for row in rows))
