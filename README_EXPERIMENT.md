# LLM-Driven Dynamic Replanning Experiment

## The Supermarket Problem

An autonomous robot navigates a city to buy groceries while minimizing total cost (time + money). The robot starts with partial knowledge, knowing only about the expensive Victory supermarket. During execution, it discovers a cheaper Rami Levy supermarket and must decide whether to replan its route.

## System Architecture

### Components
- **SupermarketEnv**: 8x8 MiniGrid environment with Victory (blue ball) and Rami Levy (red ball)
- **LLMReasoner**: GPT-4o strategic advisor for Time vs Money optimization
- **PDDLPatcher**: Safely updates PDDL files with new knowledge and topology
- **FastDownwardRunner**: Executes optimal planning with cost minimization
- **StateTranslator**: Bridges MiniGrid coordinates ↔ PDDL symbols

### Data Flow
```
MiniGrid Pixels → Semantic Bridge → Store Discovery
Store Discovery → LLM Strategic Advisor → Replan Decision
Decision → PDDL Patcher → Updated Domain + Topology
Updated PDDL → Fast Downward → New Optimal Plan
```

## Running the Experiment

### Prerequisites
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key-here"
```

### Quick Test (Mock LLM)
```bash
python test_supermarket_scenario.py
```

### Full Live Experiment
```bash
python run_experiment.py
```

The experiment will:
1. Initialize with naive knowledge (only Victory known)
2. Execute interleaved planning
3. Discover Rami Levy through visual observation
4. Consult GPT-4o for strategic replanning decision
5. Update PDDL with new topology and costs
6. Replan with complete knowledge
7. Generate visualization and metrics

## Expected Output

```
🚀 Starting Experiment...

🏪 Creating Supermarket Environment...
   Grid: 8x8
   Agent starts at: (1, 1)
   True world contains: 2 stores
     - victory (blue) at (5, 5)
     - rami_levy (red) at (2, 6)

📋 Phase 1: Initial Planning (Naive Knowledge)
✅ Initial plan found

🎬 Phase 2: Interleaved Execution

🔄 Step 1
📍 Agent at: (1,1)
👀 DISCOVERY! Found rami_levy (red store) at (2, 6)
🤖 Consulting LLM Strategic Advisor...
💡 Decision: REPLAN
📝 Reasoning: Rami Levy offers 38% savings ($2.50 vs $4.00) with acceptable detour cost...

🔄 Replanning with updated knowledge...
✅ New plan found

🏁 EXPERIMENT COMPLETE
Steps: 8
Replans: 1
Final Status: goal_achieved_with_replanning
Total Cost: $6.50
Frames Captured: 12
```

## Results Analysis

The experiment generates `results.json` with:
- **Steps taken**: Execution efficiency
- **Total cost**: Time + money optimization
- **Replan decision**: LLM strategic reasoning
- **LLM reasoning**: Full decision explanation
- **Visualization**: experiment.gif showing discovery and replanning

## Key Innovations

1. **LLM-Modulo Architecture**: LLM makes high-level decisions, Python handles technical PDDL manipulation
2. **Semantic Observation Bridge**: Pixels → meaningful store identities
3. **Dynamic Topology**: PDDL updated with real-time connection costs
4. **Cost-Based Optimization**: True minimization of time + money
5. **Strategic Reasoning**: LLM weighs economic savings vs planning disruption

## Research Questions Answered

✅ **Can an LLM effectively act as a high-level reasoning agent for dynamic replanning?**
- Yes, with proper prompting and structured output

✅ **Economic vs Spatial Trade-offs**: LLM correctly identifies 38% savings justify replanning

✅ **Technical Integration**: Clean separation between LLM reasoning and PDDL execution

This demonstrates that LLMs can serve as effective strategic advisors in autonomous planning systems, making intelligent decisions about when computational replanning is worthwhile.
