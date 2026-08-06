# THE FORGE v3.0 + Garcar

**Cognitive Economic Control System**  
Protocol: `FORGE-COGNITIVE-CONTROL-v3`

> State → Perception → Prediction → Decision → Action → Outcome → Learning

**Repo:** https://github.com/Garrettc123/THE-FORGE

---

## Quick Start

```bash
git clone https://github.com/Garrettc123/THE-FORGE.git
cd THE-FORGE

# Optional secrets
cp garcar.env.template .env
# edit .env

python forge_all.py                  # interactive menu
python forge_all.py status           # all agents + env
python forge_all.py cycle            # cognitive cycle (dry-run)
python forge_all.py cycle --live     # live capital movement
python forge_all.py bridge           # Garcar → Forge
python forge_all.py demo --live      # full closed-loop demo
python forge_all.py tower            # Control Tower
```

Zero external dependencies. Pure Python 3.9+.

---

## Architecture

8 agents: SENTINEL · DELTA · TREASURY · ALPHA · BETA · GAMMA · KNOWLEDGE · EXECUTIVE

Multi-horizon utility (H1–H4) · Experiment ledger · Causal memory · Replication gate

## Files

| File | Purpose |
|------|---------|
| `forge_all.py` | Unified launcher |
| `forge_cognitive_core.py` | Full cognitive control system |
| `forge_garcar_bridge.py` | Garcar sensors → Forge cycle |
| `garcar_master.py` | Enterprise orchestration |
| `forge_master_workflow.yml` | GitHub Actions |
| `FORGE_v3_PROTOCOL.md` | Canonical operating protocol |
| `garcar.env.template` | Secrets template |

## GitHub Actions

Drop `forge_master_workflow.yml` into `.github/workflows/` (already present).

Schedule: every 15 min (status) · 07:00 UTC (tower) · midnight (bridge).

## Sibling systems

- [`systems/forge_agents/`](systems/forge_agents/) — dependency-light multi-agent
  orchestrator (planner → researcher → coder → critic) with CLI and optional REST API.
  Independent of the FORGE v3 modules above; can be extracted to its own repo.

## Value Function

```
Enterprise Value = Recurring Cash Flow × Durability × Growth × Optionality × Strategic Advantage
```

The most valuable asset THE FORGE creates is the accumulated decision infrastructure.
