"""
LLM Reasoner - Weighted reasoning agent for dynamic replanning decisions
Uses Google Gemini with configurable personality weights (Price vs. Distance vs. Other).
Includes simulated "soft" data for comprehensive decision making.
"""

import os
import json
import logging
import random
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("Experiment")

# Init Gemini
HAS_GEMINI = False
api_key = os.environ.get("GOOGLE_API_KEY")
if api_key:
    try:
        genai.configure(api_key=api_key)
        HAS_GEMINI = True
    except Exception as e:
        logger.error(f"Gemini Config Error: {e}")
        print("[LLM] Google Generative AI library not found - using Mock mode")
    except Exception as e:
        HAS_GEMINI = False
        print(f"[LLM] Gemini initialization failed: {e} - using Mock mode")
else:
    print("[LLM] No GOOGLE_API_KEY found - using Mock mode")

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ReplanningDecision(BaseModel):
    """Response schema for replanning decisions with detailed reasoning and PDDL predicates."""
    replan_needed: bool = Field(description="Whether to replan the route")
    reasoning: str = Field(description="Detailed explanation of the decision-making process")
    economic_analysis: str = Field(description="Breakdown of cost-benefit analysis")
    distance_assessment: str = Field(description="Evaluation of distance vs. savings trade-off")
    recommendation_strength: str = Field(description="Confidence level in the decision (Strong/Moderate/Weak)")
    pddl_predicates: list[str] = Field(description="List of PDDL predicates to add for the new object")


class LLMReasoner:
    """
    Semantic reasoning agent that uses world knowledge to estimate prices.
    No explicit price data - relies on brand recognition and common sense.
    """

    def __init__(self, price_weight=0.6, dist_weight=0.4):
        """
        Initialize with decision weights.
        - price_weight: Importance of saving money.
        - dist_weight: Importance of minimizing walking effort.
        """
        self.model_name = "gemini-2.0-flash-exp"
        self.weights = {
            "price": price_weight,
            "distance": dist_weight
        }
        self.llm_call_count = 0  # Counter for LLM API calls

    def analyze_observation(self, discovery_name):
        """
        PHASE 1: Pure Perception/Knowledge
        Analyze what the discovered object is and estimate its properties.

        Args:
            discovery_name: Name/label of the discovered object

        Returns:
            dict: {'type': str, 'sells_milk': bool, 'estimated_price': float}
        """
        prompt = f"""
        ROLE: You are an AI Agent operating in Israel. You possess common sense regarding local retail chains.

        OBSERVATION: You pass by a building labeled: "{discovery_name}"

        YOUR TASK: IDENTIFY AND ANALYZE
        1. What is "{discovery_name}"? (Supermarket? Coffee shop? Shoe store? Pharmacy?).
        2. Does it sell milk? (true/false)
        3. If it sells milk, estimate the price compared to 'Victory' (which costs 4.00 NIS).

        HINTS:
        - Supermarkets that sell milk: Rami Levy (cheap ~2.5), Victory (standard 4.0), AM:PM (expensive ~6.0)
        - Other stores: Starbucks (coffee), Nike (sportswear), American Eagle (clothing), McDonald's (fast food), Super-Pharm (pharmacy/cosmetics), Louis Vuitton (luxury)

        JSON RESPONSE FORMAT:
        {{
            "type": "Brief description of place",
            "sells_milk": true/false,
            "estimated_price": 0.0
        }}
        """

        # Log LLM communication
        if HAS_GEMINI:
            logger.info("LLM", f"🤖 ANALYZING: '{discovery_name}'")
            try:
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                self.llm_call_count += 1  # Count LLM API call
                result = json.loads(response.text)
                logger.info("LLM", f"✅ RESULT: {result.get('type', 'unknown')} | Sells milk: {result.get('sells_milk', False)} | Price: ${result.get('estimated_price', 0):.1f}")
                return result
            except Exception as e:
                logger.warning(f"❌ Gemini API error for {discovery_name}, falling back to mock reasoning: {str(e)[:100]}")

        # Fallback Mock Analysis
        return self._mock_perception_analysis(discovery_name)

    def decide_replan(self, context, analysis_result):
        """
        PHASE 2: Strategic Decision Making
        Given perception analysis and context, decide whether to replan.

        Args:
            context: Dict with agent location, current plan, etc.
            analysis_result: Output from analyze_observation()

        Returns:
            dict: {'replan_needed': bool, 'reasoning': str}
        """
        if not analysis_result.get('sells_milk', False):
            return {
                'replan_needed': False,
                'reasoning': f"{analysis_result['type']} does not sell milk - no need to replan."
            }

        estimated_price = analysis_result.get('estimated_price', 4.0)
        walking_distance = context.get('walking_distance_to_new_store', 0)

        prompt = f"""
        ROLE: You are a strategic decision-making agent.

        CURRENT SITUATION:
        - Current destination: Victory Supermarket (milk costs 4.00 NIS)
        - New option: {analysis_result['type']} (estimated milk price: {estimated_price} NIS)
        - Detour distance: {walking_distance} steps

        DECISION WEIGHTS:
        - Price Importance: {self.weights['price']*100}%
        - Distance Importance: {self.weights['distance']*100}%

        TASK: Should you switch plans to this new store?

        JSON RESPONSE FORMAT:
        {{
            "replan_needed": true/false,
            "reasoning": "Explain your strategic decision based on cost-benefit analysis."
        }}
        """

        # Log strategic LLM decisions
        if HAS_GEMINI:
            logger.info("LLM", f"🧠 DECIDING: Replan to '{analysis_result.get('type', 'unknown')}' at distance {context.get('walking_distance_to_new_store', 0)}?")
            try:
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                self.llm_call_count += 1  # Count LLM API call
                result = json.loads(response.text)
                logger.info("LLM", f"✅ DECISION: {'REPLAN' if result.get('replan_needed', False) else 'CONTINUE'} | Reason: {result.get('reasoning', 'N/A')[:80]}...")
                return result
            except Exception as e:
                logger.warning(f"❌ Gemini API error in strategic decision, falling back to mock reasoning: {str(e)[:100]}")

        # Fallback Mock Decision
        return self._mock_strategic_decision(context, analysis_result)

    # DEPRECATED: Keep for backward compatibility during transition
    def should_replan(self, context, new_discovery):
        """
        LEGACY METHOD: Combined perception + decision making
        Kept for backward compatibility during refactoring
        """
        # Phase 1: Analyze observation
        analysis = self.analyze_observation(new_discovery['name'])

        # Phase 2: Make decision
        decision = self.decide_replan(context, analysis)

        # Combine results for backward compatibility
        combined_result = {
            **analysis,
            **decision
        }

        # Inject price for system compatibility (legacy behavior)
        if decision.get('replan_needed'):
            new_discovery['price'] = float(analysis.get('estimated_price', 4.0))

        return combined_result

    def _mock_semantic_inference(self, context, new_discovery):
        name = new_discovery['name'].lower()

        # Mock knowledge about Israeli retail chains and global brands
        if "rami" in name or "levy" in name or "osher" in name:
            est_price = 2.5
            identified_type = "Discount supermarket chain"
            sells_milk = True
            reason = "[MOCK] Recognized Rami Levy as discount chain - should be cheaper than Victory."
            replan = True
        elif "am:pm" in name or "yellow" in name:
            est_price = 6.0
            identified_type = "Convenience store"
            sells_milk = True
            reason = "[MOCK] Recognized AM:PM as expensive convenience store - probably more expensive."
            replan = False
        elif "victory" in name:
            est_price = 4.0
            identified_type = "Standard supermarket"
            sells_milk = True
            reason = "[MOCK] This is Victory - same as current destination."
            replan = False
        elif "american" in name.lower() or "eagle" in name.lower():
            est_price = 0  # Not applicable
            identified_type = "Clothing store"
            sells_milk = False
            reason = "[MOCK] American Eagle is a clothing store - doesn't sell milk. No need to replan."
            replan = False
        elif "mcdonald" in name.lower() or "mc donald" in name.lower():
            est_price = 0  # Not applicable
            identified_type = "Fast food restaurant"
            sells_milk = False
            reason = "[MOCK] McDonald's is a fast food restaurant - doesn't sell milk for home use. No need to replan."
            replan = False
        elif "starbuck" in name.lower():
            est_price = 0  # Not applicable
            identified_type = "Coffee shop"
            sells_milk = False
            reason = "[MOCK] Starbucks is a coffee shop - sells coffee and drinks, not milk for home use. No need to replan."
            replan = False
        elif "nike" in name.lower():
            est_price = 0  # Not applicable
            identified_type = "Sportswear store"
            sells_milk = False
            reason = "[MOCK] Nike is a sportswear store - sells shoes and clothing, not groceries. No need to replan."
            replan = False
        elif "super" in name.lower() and "pharm" in name.lower():
            est_price = 0  # Not applicable
            identified_type = "Pharmacy and cosmetics store"
            sells_milk = False
            reason = "[MOCK] Super-Pharm is a pharmacy and cosmetics store - sells medicine and beauty products, not milk. No need to replan."
            replan = False
        elif "butcher" in name.lower() or "moshe" in name.lower():
            est_price = 0.0
            identified_type = "Butcher Shop"
            sells_milk = False
            reason = "[MOCK] Recognized as a butcher shop - sells meat, not milk. No need to replan."
            replan = False
        else:
            est_price = 0  # Not applicable
            identified_type = "Unknown retail establishment"
            sells_milk = False  # Conservative assumption
            reason = "[MOCK] Unknown brand - doesn't appear to be a supermarket."
            replan = False

        # Inject estimated price for system compatibility
        if replan:
            new_discovery['price'] = est_price

        return {
            "identified_type": identified_type,
            "sells_milk": sells_milk,
            "estimated_price": est_price,
            "replan_needed": replan,
            "reasoning": reason
        }

    def _mock_perception_analysis(self, discovery_name):
        """
        Mock perception analysis - identifies object type and properties
        """
        name = discovery_name.lower()

        # Mock knowledge about stores and objects
        if "rami" in name or "levy" in name or "osher" in name:
            return {
                "type": "Discount supermarket chain",
                "sells_milk": True,
                "estimated_price": 2.5
            }
        elif "victory" in name:
            return {
                "type": "Standard supermarket",
                "sells_milk": True,
                "estimated_price": 4.0
            }
        elif "am:pm" in name or "am_pm" in name or "yellow" in name:
            return {
                "type": "Convenience store",
                "sells_milk": True,
                "estimated_price": 12.0
            }
        elif "american" in name.lower() or "eagle" in name.lower():
            return {
                "type": "Clothing store",
                "sells_milk": False,
                "estimated_price": 0.0
            }
        elif "mcdonald" in name.lower() or "mc donald" in name.lower():
            return {
                "type": "Fast food restaurant",
                "sells_milk": False,
                "estimated_price": 0.0
            }
        elif "starbuck" in name.lower():
            return {
                "type": "Coffee shop",
                "sells_milk": False,
                "estimated_price": 0.0
            }
        elif "nike" in name.lower():
            return {
                "type": "Sportswear store",
                "sells_milk": False,
                "estimated_price": 0.0
            }
        elif "super" in name.lower() and "pharm" in name.lower():
            return {
                "type": "Pharmacy and cosmetics store",
                "sells_milk": False,
                "estimated_price": 0.0
            }
        elif "louis" in name.lower() and "vuitton" in name.lower():
            return {
                "type": "Luxury fashion store",
                "sells_milk": False,
                "estimated_price": 0.0
            }
        elif "mega" in name.lower() and "bulldog" in name.lower():
            return {
                "type": "Supermarket",
                "sells_milk": True,
                "estimated_price": 3.0
            }
        elif "old" in name.lower() and "tree" in name.lower():
            return {
                "type": "Tree (natural object)",
                "sells_milk": False,
                "estimated_price": 0.0
            }
        else:
            return {
                "type": "Unknown establishment",
                "sells_milk": False,
                "estimated_price": 0.0
            }

    def _mock_strategic_decision(self, context, analysis_result):
        """
        Mock strategic decision making based on weights and context
        """
        if not analysis_result.get('sells_milk', False):
            return {
                'replan_needed': False,
                'reasoning': f"{analysis_result['type']} does not sell milk."
            }

        estimated_price = analysis_result.get('estimated_price', 4.0)
        walking_distance = context.get('walking_distance_to_new_store', 0)

        # Simple weighted decision
        price_savings = 4.0 - estimated_price
        distance_penalty = walking_distance * 0.1  # Each step costs 0.1 utility

        net_benefit = (price_savings * self.weights['price']) - (distance_penalty * self.weights['distance'])

        replan_needed = net_benefit > 0.5  # Threshold for replanning

        reasoning = f"Price savings: ${price_savings:.1f}, Distance cost: ${distance_penalty:.1f}, Net benefit: {net_benefit:.1f}"

        return {
            'replan_needed': replan_needed,
            'reasoning': reasoning
        }

    def get_llm_call_count(self):
        """
        Get the total number of LLM API calls made during the experiment.
        
        Returns:
            int: Number of LLM API calls
        """
        return self.llm_call_count

    def reset_llm_call_count(self):
        """
        Reset the LLM call counter (useful for testing or multiple experiments).
        """
        self.llm_call_count = 0
