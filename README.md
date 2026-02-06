# az-reporter

A small DevOps-friendly Python CLI that queries **Azure Resource Graph** and exports a report.

## Prereqs

- Python 3.13+
- Azure login (for local dev):

```bash
az login
```

## Install (uv / pip)

```bash
pip install -e .
```

## Usage

Export an inventory report:

```bash
azr inventory --subs <subId1>,<subId2> --out report.csv
```

## Notes

- Auth uses `DefaultAzureCredential` (Azure SDK): local `az login`, CI env vars, or Managed Identity.
- Created time is **not** included in the MVP inventory because it is not consistently available across resource types.
  (We can add an optional `--with-created-time` later using `resourcechanges`.)
