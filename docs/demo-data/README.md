# HEX demo dataset — "Aurora Foods"

A small, coherent, fictional business for testing HEX's **file-upload integration**.
Aurora Foods is a packaged-snacks maker in India that imports ingredients and
packaging from China, Vietnam and the Netherlands.

## Files (upload all 8 in one connection)

| File | Rows | What it exercises |
|---|---|---|
| `supplier.csv` | 6 | suppliers with lead times, one `AT_RISK` |
| `product.csv` | 8 | snack SKUs across two categories |
| `purchase_order.csv` | 5 | open + received POs in USD / EUR / INR |
| `purchase_order_line.csv` | 6 | PO lines linked by `po_number` + `product` name |
| `shipment.csv` | 4 | on real corridors (Shanghai→Mundra = Red Sea) — lights up Risk Center / World Watch |
| `inventory.csv` | 8 | 3 SKUs deliberately below reorder level |
| `transaction.csv` | 39 | 15 months of revenue with a 2-month contraction |
| `expense.csv` | 105 | 15 months across 7 categories incl. Marketing (for CAC) and fixed overhead |

Links are resolved **by name** (HEX matches `supplier` / `product` columns to the
names in `supplier.csv` / `product.csv`), so no ID columns are needed — just upload
all 8 and hit **Sync**.

## How to load

1. In HEX → **Integrations** → **New connection** → **File upload**.
2. Upload one file per entity (entity type = the file name without `.csv`).
3. **Sync.**
4. Check **Data Readiness** on the same page, then look at **Analytics**, **Finance**,
   **Supply Routes** and **Risk Center** — they now run on Aurora Foods' data.

Syncing the POs also triggers HEX's **shipment projection** (a derived shipment per
open PO), so Supply Routes shows more than the 4 uploaded shipments.

## Regenerate / tweak

```bash
python docs/demo-data/generate.py
```

Edit the lists at the top of `generate.py` and re-run. Ingestion is verified by
`backend/test_demo_data.py`.
