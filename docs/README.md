# HEX — project documentation

- **[HEX-Technical-Overview.pdf](HEX-Technical-Overview.pdf)** — 20-page technical overview: what HEX does, how it works, the stack and the reasoning behind each choice.
- **[HEX-Deck.pptx](HEX-Deck.pptx)** — 20-slide presentation deck (dark HEX theme).

Both are generated from one content model:

```bash
pip install fpdf2 python-pptx     # docs tooling only — not app dependencies
python docs/generate_docs.py
```

Edit the `SECTIONS` list in `generate_docs.py` and re-run to update both files.
