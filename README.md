# LLM-Driven Dynamic Replanning Research Platform

## Abstract
This repository presents a controlled simulation framework for comparing four cognitive architectures for dynamic replanning in a partially observed environment. The system integrates a MiniGrid world, a PDDL planner (Fast Downward), and an LLM-based reasoning module. We evaluate how different strategies respond to new discoveries, balancing path length, milk price, and planning overhead.

## Research Question
Can a language model serve as an effective strategic layer that decides when to trigger replanning under new perceptual evidence?

## Research Questions and Hypotheses
**RQ1:** Does LLM-guided replanning reduce unnecessary replans without sacrificing performance?  
**RQ2:** Does a rigid heuristic miss cases where a slightly longer detour yields a much cheaper price?  
**RQ3:** Does replanning on every discovery improve speed but waste planning resources?

**H1:** Algorithm C achieves near-optimal speed with fewer replans than Algorithm B.  
**H2:** Algorithm D fails in “cheap but slightly farther” scenarios.  
**H3:** Algorithm B is fastest but performs the most replans.

## Key Contributions
- A reproducible experimental framework for dynamic replanning under novel observations.
- Five targeted scenarios that isolate specific decision dilemmas.
- Quantitative evaluation across steps, total cost, replans, and LLM usage.

## Algorithms
| ID | Name | Core Behavior | LLM Usage |
|----|------|----------------|-----------|
| **A** | Blind | Ignores discoveries; follows initial plan | None |
| **B** | Always Replan | Replans on every new observation; uses classification only | Low (1 call/observation) |
| **C** | Smart (LLM-Guided) | Uses LLM to decide if replanning is worthwhile | Medium (2 calls/observation) |
| **D** | Heuristic | Mirrors B, but replans only when the distance from the current goal to the observation exceeds 10 | Low (1 call/observation) |

Note: LLM calls are counted even in mock mode. Algorithm A never calls the LLM.

## Scenarios (Scenario-Only)
Each scenario contains a small, fixed set of “surprise objects” and no random stores.

| Scenario | Surprise Object | Milk Price | Objects | Expected Outcome |
|----------|------------------|------------|---------|------------------|
| **SCENARIO_1** | `old_tree_jerusalem_forest` | N/A | 1 | B/D replan once; C ignores |
| **SCENARIO_2** | 3 butcher delis (incl. `moshe_butcher_rehovot`) | N/A | 3 | B replans repeatedly; D skips close delis; C replans once then ignores |
| **SCENARIO_3** | `rami_levy_jerusalem` | 3.0 | 1 | B/C take the same path; D skips because distance ≤ 10 |
| **SCENARIO_4** | `mega_bulldog_tlv` | 3.5 | 1 | B/C take same path; D skips because distance ≤ 10 |
| **SCENARIO_5** | `am_pm_express` | 12.0 | 1 | B buys expensive milk; C/D ignore |

### Per-Scenario Expectations
**SCENARIO_1 (Noise)**  
- B/D replan once on the observation (classification only).  
- C analyzes and rejects; A ignores entirely.

**SCENARIO_2 (Wrong Category, 3 delis)**  
- B: Replans on each deli, causing high overhead.  
- D: Skips close delis and stays on the far path.  
- C: Replans once early, then ignores remaining delis.

**SCENARIO_3 (Cheap but Detour, distance gap = 7)**  
- B/C: Take the same path (non-expensive store).  
- D: Skips because distance ≤ 10.

**SCENARIO_4 (Sweet Spot)**  
- B/C: Same path; C uses more reasoning overhead.  
- D: Skips because distance ≤ 10 and follows the far path.

**SCENARIO_5 (Expensive Trap)**  
- B: Replans and buys expensive milk.  
- C/D: Reject and keep Victory.

## System Architecture
```
MiniGrid Environment
  -> Discovery Detection
  -> LLM Analysis (optional)
  -> State Update
  -> PDDL Planner (Fast Downward)
  -> Action Execution
```

## Core Components
| File | Role |
|------|------|
| `run_live_dashboard.py` | Main simulation loop |
| `custom_env.py` | MiniGrid environment |
| `simulation_engine.py` | PDDL-to-action translation |
| `llm_reasoner.py` | LLM analysis and replan decision |
| `scenarios.py` | Scenario definitions |
| `pddl_patcher.py` | Dynamic PDDL updates |
| `results_logger.py` | CSV experiment logging |

## Methodology
**Design:** Controlled simulation with identical seeds per scenario.  
**Runs:** 5 runs per scenario per algorithm.  
**Controls:** Scenario-only mode (no random stores), fixed seeds.  
**LLM:** Mock LLM still counts as external LLM calls.

## Metrics
- **Steps:** total agent steps.
- **Milk Price:** final purchase price.
- **Total Cost:** `steps + milk_price`.
- **Replans:** number of replanning events.
- **LLM Calls:** total reasoning calls.
- **Time:** average runtime per run.

## Log Validation (Spot Checks)
We validated behavior via log markers (examples from `trace.log`/run output):
- **A:** “Ignoring discovery” on irrelevant objects.  
- **B:** “Always replan” with highest replan counts.  
- **C/D:** explicit accept/ignore decisions based on price-distance tradeoffs.  

## Results: Scenario-Only (5 Runs Each)
All values are averages over 5 runs.  

### SCENARIO_1 (Noise)
| Algo | Steps | Milk Price | Total Cost | Replans | LLM Calls | Avg Time (s) |
|------|-------|------------|------------|---------|-----------|--------------|
| A | 37 | 4.0 | 41.0 | 0.0 | 0 | 3.4 |
| B | 37 | 4.0 | 41.0 | 1.0 | 1 | 4.0 |
| C | 37 | 4.0 | 41.0 | 0.0 | 2 | 4.6 |
| D | 37 | 4.0 | 41.0 | 1.0 | 1 | 3.9 |

### SCENARIO_2 (Wrong Category, 3 delis)
| Algo | Steps | Milk Price | Total Cost | Replans | LLM Calls | Avg Time (s) |
|------|-------|------------|------------|---------|-----------|--------------|
| A | 37 | 4.0 | 41.0 | 0.0 | 0 | 3.5 |
| B | 41 | 4.0 | 45.0 | 3.0 | 3 | 4.9 |
| C | 41 | 4.0 | 45.0 | 1.0 | 6 | 5.6 |
| D | 48 | 4.0 | 52.0 | 0.0 | 3 | 4.6 |

### SCENARIO_3 (Cheap but Detour, price 3 vs 5)
| Algo | Steps | Milk Price | Total Cost | Replans | LLM Calls | Avg Time (s) |
|------|-------|------------|------------|---------|-----------|--------------|
| A | 37 | 5.0 | 42.0 | 0.0 | 0 | 4.6 |
| B | 18 | 3.0 | 21.0 | 1.0 | 1 | 3.2 |
| C | 18 | 3.0 | 21.0 | 1.0 | 2 | 3.8 |
| D | 26 | 5.0 | 31.0 | 0.0 | 1 | 3.5 |

### SCENARIO_4 (Sweet Spot)
| Algo | Steps | Milk Price | Total Cost | Replans | LLM Calls | Avg Time (s) |
|------|-------|------------|------------|---------|-----------|--------------|
| A | 37 | 4.0 | 41.0 | 0.0 | 0 | 4.7 |
| B | 10 | 3.5 | 13.5 | 2.0 | 1 | 3.6 |
| C | 10 | 3.5 | 13.5 | 2.0 | 2 | 4.1 |
| D | 18 | 4.0 | 22.0 | 0.0 | 1 | 3.9 |

### SCENARIO_5 (Expensive Trap)
| Algo | Steps | Milk Price | Total Cost | Replans | LLM Calls | Avg Time (s) |
|------|-------|------------|------------|---------|-----------|--------------|
| A | 21 | 4.0 | 25.0 | 0.0 | 0 | 3.9 |
| B | 16 | 12.0 | 28.0 | 1.0 | 1 | 3.4 |
| C | 21 | 4.0 | 25.0 | 0.0 | 2 | 3.9 |
| D | 21 | 4.0 | 25.0 | 0.0 | 1 | 3.8 |

## Aggregate Summary (All Scenarios)
| Algo | Steps | Milk Price | Total Cost | Replans | LLM Calls | Avg Time (s) |
|------|-------|------------|------------|---------|-----------|--------------|
| A | 33.8 | 4.2 | 38.0 | 0.0 | 0 | 4.0 |
| B | 24.4 | 5.3 | 29.7 | 1.6 | 1.4 | 3.8 |
| C | 25.4 | 3.7 | 29.1 | 0.8 | 2.8 | 4.4 |
| D | 30.0 | 4.2 | 34.2 | 0.2 | 1.4 | 3.9 |

**Key Findings**
- **Algorithm B is fastest** but incurs the most replans and fails in expensive-trap scenarios.  
- **Algorithm C is the best overall**: strong total cost with fewer replans.  
- **Algorithm D tracks B except when observations are close (distance ≤ 10).**  
- **Algorithm A is stable and fastest in pure-noise cases**, but worst overall.

## Additional Experiment: Random Store Competition (Default Settings)
Default `run_live_dashboard.py` settings with random stores enabled (5 runs per algorithm).

| Algo | Steps | Milk Price | Total Cost | Replans | LLM Calls | Avg Time (s) |
|------|-------|------------|------------|---------|-----------|--------------|
| A | 44 | 4.0 | 48.0 | 0.0 | 0 | 6.2 |
| B | 26 | 7.5 | 33.5 | 4.2 | 1 | 4.3 |
| C | 28 | 4.2 | 32.2 | 1.8 | 2 | 4.9 |
| D | 27 | 7.4 | 34.4 | 4.0 | 1 | 4.4 |

Interpretation: C remains the best trade-off under noise, avoiding expensive stores while replanning less than B.

## LLM Prompts (English)
**Prompt 1: Classification and PDDL Semantics**
```
You are given an observation from the environment.

Task:
Classify the observation against the existing PDDL files so the planner can
replan using the new information. Do NOT paste file contents. Only reference
the files by name.

Available files:
- {domain.pddl}
- {problem.pddl}

Return JSON in this exact format:
{
  "type": "...",
  "sells_milk": true/false,
  "estimated_price": 0.0,
  "pddl_predicates": ["..."]
}
```

**Prompt 2: Replanning Decision**
```
Goal: buy milk as cheaply as possible with minimal time.

Observation: {observation}
Current plan length: {current_plan_steps}
Distance to new store: {detour_steps}
Victory price: {victory_price}

Task: Should we replan?
Do a deep search on the observation relevant to the mission:
price, congestion, product availability, and customer reviews.
Also consider distance.

Explain both:
1) Why to replan (if yes)
2) Why not to replan (if no)

Return JSON:
{
  "replan_needed": true/false,
  "reasoning": "...",
  "economic_analysis": "...",
  "distance_assessment": "...",
  "recommendation_strength": "Strong/Moderate/Weak"
}
```

## Reproducibility
```bash
# Scenario-only batch (5 runs per combo)
RUNS_PER_COMBO=5 SCENARIO_ONLY=true ./run_batch_experiments.sh

# Default settings with random stores
python run_live_dashboard.py
```

## Notes
- All results are reported as averages over 5 runs per scenario.  
- LLM calls are counted even in mock mode.  
- Total cost is defined as `steps + milk_price`.

---

## Code Responsibilities (Key Files)
Below are core modules and what each one is responsible for, with a code excerpt from each file.

- `run_live_dashboard.py`: Main simulation entry point and experiment loop.
```
def run_live_dashboard():
    ALGORITHM_MODE = os.environ.get('ALGORITHM_MODE', 'C').upper()
    SCENARIO_ID = os.environ.get('SCENARIO_ID', 'SCENARIO_4')
    logger.info("EXPERIMENT", f"Algorithm: {ALGORITHM_MODE}, Scenario: {SCENARIO_ID}")
```

- `custom_env.py`: MiniGrid environment generation and scenario object placement.
```
surprise_ball = Ball(color)
surprise_ball.name = surprise_obj['name']
if price is not None and price > 0:
    surprise_ball.price = price
self.grid.set(*obj_pos, surprise_ball)
```

- `simulation_engine.py`: PDDL action translation and discovery detection.
```
if use_semantic and hasattr(env, 'get_semantic_observation'):
    for obj in env.get_semantic_observation():
        entity_name = obj.get('name')
        pos = obj.get('position')
        if entity_name and pos:
            return obj
```

- `llm_reasoner.py`: LLM-based observation analysis and replanning decisions.
```
prompt = f"""
ROLE: You are an AI Agent operating in Israel.
OBSERVATION: You pass by a building labeled: "{discovery_name}"
YOUR TASK: IDENTIFY AND ANALYZE
"""
```

- `pddl_patcher.py`: Safe injection of dynamic predicates into PDDL.
```
new_pred = f"(at_agent agent loc_{agent_pos[0]}_{agent_pos[1]})"
if self.inject_dynamic_state([new_pred]):
    return True
```

- `results_logger.py`: CSV logging for experiment outcomes and metrics.
```
writer.writerow([
    'timestamp', 'scenario_id', 'algorithm_mode',
    'total_steps', 'total_cost', 'compute_time_seconds',
    'replans_count', 'llm_calls_count', 'true_final_price',
    'victory_reached', 'termination_reason'
])
```
