# Observability Schema

Schema for changes to the observability layer.

## When to use this schema

Use `observability` when the change affects:

- **Prometheus alerts**: `PrometheusRule`, `AlertRule`, thresholds, evaluation windows
- **Grafana dashboards**: creation, modification, or removal of dashboards
- **SLO definitions**: targets, windows, burn rates
- **Recording rules**: aggregations and derived metrics
- **Notification policies**: alert routing, receivers, silences

## Sequence

```text
proposal → impact-analysis → design → runbook → tasks
```

## Required context

Read [`context/slo-budget.md`](../../context/slo-budget.md) — especially the sections on burn rate calculation and freeze criteria.

## Templates

| Template | Description |
|----------|-------------|
| [proposal.md](templates/proposal.md) | Coverage gap or problem with an existing alert |
| [impact-analysis.md](templates/impact-analysis.md) | SLO impact, alert coverage, noise ratio |
| [design.md](templates/design.md) | Validated PromQL, justified thresholds, alert YAML |
| [runbook.md](templates/runbook.md) | Rule deploy, validation, rollback (restore previous rule) |
| [tasks.md](templates/tasks.md) | Tasks with staging validation before production |
