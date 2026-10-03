# Implementation Plan: StockTrader Workstation Remake

## Overview
Replace the current screen-per-action UI with one persistent workstation shell, while tightening the existing money and market-data paths the new interface depends on.

## Architecture Decisions
- Keep CustomTkinter, SQLite, yfinance, and Matplotlib; add no dependencies.
- Keep views in `gui.py`; one application does not need a component framework.
- Isolate only portfolio insight math because it is reused, non-trivial, and independently testable.
- Use yfinance as the single market-data source and remove the embedded AlphaVantage key.

## Task List

### Phase 1: Trusted core
- [x] Harden authentication and trade invariants with focused tests.
- [x] Replace dual-provider quote lookup with the existing yfinance dependency.

### Checkpoint: Core
- [x] `python -m unittest -v` passes.
- [x] No credential remains in source.

### Phase 2: Workstation
- [x] Replace login and application shell with the new visual system.
- [x] Build Overview, Trade, Portfolio, Activity, and Research views.

### Checkpoint: Product
- [x] Core simulator flows work end to end.
- [x] Network work has loading and error states.

### Phase 3: Finish
- [x] Refresh README and repository hygiene.
- [x] Run tests, compile check, launch smoke check, and review the final diff.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Market APIs are slow or unavailable | Medium | Background requests and explicit retryable states |
| Existing plaintext passwords | High | Verify legacy values, then upgrade them on successful login |
| Existing portfolio rows use legacy cost data | Low | Preserve schema and calculate from available values |

## Open Questions
None.
