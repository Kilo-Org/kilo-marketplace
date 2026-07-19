# Skill Benchmark

Generated: 2026-05-22T10:36:23.032Z

Skill: redis-core

Suite: core

Input: `eval-workspaces/redis-core/core/iteration-1`

## Overall

- Models: 3
- Mean pass-rate delta: +2 points
- Mean token delta: -309
- Mean time delta: +4.6s
- Total eval cost: $8.0206
- Mean cost delta: +$0.0361
- Verdict counts: 0 improves, 3 neutral, 0 degrades

## Against Baseline

Baseline: `skills/redis-core/evals/core/baselines/aggregate-benchmark.json`

Baseline generated: 2026-05-20T07:02:10.439Z

| Metric | Baseline | Current | Change |
|--------|----------|---------|--------|
| Mean pass delta | +2 points | +2 points | +0 points |
| Mean token delta | -222 | -309 | -87 |
| Mean time delta | +8.2s | +4.6s | -3.6s |
| Mean cost delta | +$0.0583 | +$0.0361 | -$0.0222 |

### By Model Against Baseline

| Model | Pass Delta Change | Token Delta Change | Time Delta Change | Cost Delta Change | Verdict |
|-------|-------------------|--------------------|-------------------|-------------------|---------|
| claude-haiku-4-5-20251001 | -3 points | -12 | -2.7s | -$0.0043 | neutral -> neutral |
| claude-opus-4-7 | +3 points | -127 | -6.0s | -$0.0465 | neutral -> neutral |
| claude-sonnet-4-6 | +0 points | -121 | -2.1s | -$0.0158 | neutral -> neutral |

## By Model

| Model | Without Skill | With Skill | Pass Delta | Token Delta | Time Delta | Total Cost | Cost Delta | Verdict |
|-------|---------------|------------|------------|-------------|------------|------------|------------|---------|
| claude-haiku-4-5-20251001 | 95% | 95% | +0 points | -75 | +9.2s | $2.1215 | +$0.0416 | neutral |
| claude-opus-4-7 | 98% | 100% | +3 points | -714 | -1.5s | $3.3557 | +$0.0285 | neutral |
| claude-sonnet-4-6 | 95% | 98% | +3 points | -137 | +6.1s | $2.5435 | +$0.0383 | neutral |

## By Eval

| Eval | Without Skill | With Skill | Pass Delta | Token Delta | Time Delta | Model Pass Deltas |
|------|---------------|------------|------------|-------------|------------|-------------------|
| object-profile-cache | 87% | 90% | +3 points | -247 | +6.6s | claude-haiku-4-5-20251001: +0 points<br>claude-opus-4-7: +0 points<br>claude-sonnet-4-6: +10 points |
| unique-membership | 97% | 100% | +3 points | -294 | +3.2s | claude-haiku-4-5-20251001: +0 points<br>claude-opus-4-7: +10 points<br>claude-sonnet-4-6: +0 points |
| leaderboard-ranking | 100% | 100% | +0 points | -296 | +5.4s | claude-haiku-4-5-20251001: +0 points<br>claude-opus-4-7: +0 points<br>claude-sonnet-4-6: +0 points |
| key-naming-cleanup | 100% | 100% | +0 points | -397 | +3.2s | claude-haiku-4-5-20251001: +0 points<br>claude-opus-4-7: +0 points<br>claude-sonnet-4-6: +0 points |
