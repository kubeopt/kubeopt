"""
Claude API Integration for Plan Generation

Handles communication with Claude API to generate structured implementation plans
for AKS cost optimization based on enhanced analysis input.
"""

import anthropic
import json
import asyncio
import os
from typing import Dict, Optional
from datetime import datetime
import logging
from .plan_schema import (
    KubeOptImplementationPlan, ImplementationPlanDocument, 
    KUBEOPT_IMPLEMENTATION_PLAN_SCHEMA, create_empty_plan
)
from .plan_validator import PlanValidator
from .context_builder import ContextBuilder
from .cost_tracker import get_cost_tracker
from .cost_limiter import check_cost_limit

# Import standards loader for YAML-based configuration
from shared.standards.standards_loader import get_standards_loader


class ClaudePlanGenerator:
    """Generates implementation plans using Claude API with intelligent context compacting"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_output_tokens: Optional[int] = None,
        max_context_tokens: int = 180000
    ):
        """
        Initialize the plan generator.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (defaults to env CLAUDE_MODEL or Sonnet 3.5)
            max_output_tokens: Max tokens for output (defaults to env or model-specific)
            max_context_tokens: Maximum tokens for input context
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided and not found in environment")
        
        # Get model from parameter, environment, or default
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
        
        # Get max output tokens
        if max_output_tokens:
            self.max_output_tokens = max_output_tokens
        else:
            env_max_tokens = os.getenv("CLAUDE_MAX_OUTPUT_TOKENS")
            if env_max_tokens:
                self.max_output_tokens = int(env_max_tokens)
            else:
                # Use model-specific default
                self.max_output_tokens = self._get_model_max_output_tokens(self.model)
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.validator = PlanValidator()
        self.context_builder = ContextBuilder(target_token_limit=max_context_tokens)
        self.logger = logging.getLogger(__name__)
        
        print(f"✓ Initialized ClaudePlanGenerator")
        print(f"  Model: {self.model}")
        print(f"  Max output tokens: {self.max_output_tokens} (cost-optimized)")
        print(f"  Max context tokens: {max_context_tokens}")
        print(f"✓ Token limit set to {self.max_output_tokens} (cost-optimized)")
    
    def _get_model_max_output_tokens(self, model: str) -> int:
        """
        Get the maximum output tokens for a given model.
        
        Returns model-specific safe defaults.
        """
        model_limits = {
            # Latest Claude 4.5 models (2025) - Cost-optimized
            "claude-sonnet-4-5-20250929": 3000,  # Reduced from 16000 for cost optimization
            "claude-haiku-4-5-20251001": 3000,   # Reduced from 16000 for cost optimization
            
            # Claude 4 models (2025) - Cost-optimized
            "claude-opus-4-1-20250805": 3000,    # Reduced from 16000 for cost optimization
            "claude-sonnet-4-20250514": 3000,    # Reduced from 16000 for cost optimization
            "claude-opus-4-20250514": 3000,      # Reduced from 16000 for cost optimization
            
            # Claude 3.7 models - Cost-optimized
            "claude-3-7-sonnet-20250219": 3000,  # Reduced from 8192 for cost optimization
            
            # Legacy Claude 3.5 models - Cost-optimized
            "claude-3-haiku-20240307": 4000,     # Increased to fix JSON truncation issue
            "claude-3-5-sonnet-20240620": 3000,  # Reduced from 8192 for cost optimization
            
            # Legacy Claude 3 models - Cost-optimized
            "claude-3-opus-20240229": 3000,      # Reduced from 4096 for cost optimization
            "claude-3-sonnet-20240229": 3000,    # Reduced from 4096 for cost optimization
            "claude-3-haiku-20240307": 4000,     # Increased to fix JSON truncation issue
        }
        
        max_tokens = model_limits.get(model, 3000)  # Conservative default - cost-optimized
        
        if model not in model_limits:
            print(f"⚠️ Unknown model {model}, using conservative {max_tokens} max output tokens")
        
        return max_tokens
        
    async def generate_plan(
        self, 
        enhanced_input: Dict,
        cluster_name: str,
        cluster_id: str,
        max_retries: int = None
    ) -> KubeOptImplementationPlan:
        """
        Generate implementation plan.
        
        Automatically uses split mode for Haiku (2 calls),
        single mode for other models.
        """
        
        # Determine mode
        use_split = "haiku" in self.model.lower() or os.getenv("CLAUDE_USE_SPLIT_MODE", "true").lower() == "true"
        
        if use_split:
            # Use split mode (2 API calls)
            return await self.generate_plan_split(enhanced_input, cluster_name, cluster_id)
        else:
            # Use single call mode (for Sonnet/Opus)
            return await self.generate_plan_single(enhanced_input, cluster_name, cluster_id, max_retries)
    
    async def generate_plan_single(
        self, 
        enhanced_input: Dict,
        cluster_name: str,
        cluster_id: str,
        max_retries: int = None
    ) -> KubeOptImplementationPlan:
        """
        Generate implementation plan from enhanced analysis input with intelligent context optimization.
        
        Args:
            enhanced_input: The enhanced analysis JSON from Phase 1
            cluster_name: Name of the AKS cluster
            cluster_id: Unique cluster identifier
            max_retries: Number of API retry attempts (uses env CLAUDE_MAX_RETRIES if None)
            
        Returns:
            KubeOptImplementationPlan object with structured recommendations
        """
        # Get max_retries from environment if not provided
        if max_retries is None:
            max_retries = int(os.getenv("CLAUDE_MAX_RETRIES", 1))  # Default to 1 for cost savings
        # Build optimized context based on data size
        optimized_context = self.context_builder.build_optimized_context(enhanced_input, cluster_name)
        
        # Log optimization details
        original_tokens = self.context_builder.count_tokens(json.dumps(enhanced_input, indent=2))
        optimized_tokens = self.context_builder.count_tokens(json.dumps(optimized_context, indent=2))
        optimization_report = self.context_builder.get_optimization_report(
            original_tokens, optimized_tokens, optimized_context.get('context_type', 'unknown')
        )
        
        self.logger.info(f"Context optimization: {optimization_report}")
        
        # Build prompts with optimized context
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(optimized_context, cluster_name)
        
        for attempt in range(max_retries):
            try:
                # BEFORE making API call: Check cost limit
                estimated_cost = (2284 * 0.25 + 3000 * 1.25) / 1_000_000  # ~$0.004
                
                if not check_cost_limit(estimated_cost):
                    raise Exception("Daily cost limit exceeded - blocking Claude API call")
                
                self.logger.info(f"Generating plan for cluster {cluster_name} (attempt {attempt + 1})")
                
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model,
                    max_tokens=self.max_output_tokens,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": user_prompt
                    }]
                )
                
                # Add response inspection before processing
                print(f"\n{'─'*70}")
                print(f"📥 RAW RESPONSE FROM CLAUDE")
                print(f"{'─'*70}")
                
                # Show response metadata
                print(f"Response type: {type(response)}")
                print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
                
                if hasattr(response, 'usage'):
                    print(f"\nToken usage:")
                    print(f"   Input: {response.usage.input_tokens}")
                    print(f"   Output: {response.usage.output_tokens}")
                
                if hasattr(response, 'content'):
                    content = response.content[0].text
                    print(f"\nContent length: {len(content)} characters")
                    print(f"\nFirst 1000 characters:")
                    print(content[:1000])
                    print(f"\n...")
                    print(f"\nLast 500 characters:")
                    print(content[-500:])
                
                print(f"{'─'*70}\n")
                
                # Extract token usage and calculate costs
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                
                # Calculate cost (Claude Haiku pricing)
                input_cost = (input_tokens * 0.25) / 1_000_000  # Haiku: $0.25 per 1M input tokens
                output_cost = (output_tokens * 1.25) / 1_000_000  # Haiku: $1.25 per 1M output tokens
                total_cost = input_cost + output_cost
                
                # Log detailed usage
                print(f"\n{'='*60}")
                print(f"💰 CLAUDE API COST BREAKDOWN")
                print(f"{'='*60}")
                print(f"Model: {self.model}")
                print(f"Input tokens:  {input_tokens:,} × $0.25/1M = ${input_cost:.6f}")
                print(f"Output tokens: {output_tokens:,} × $1.25/1M = ${output_cost:.6f}")
                print(f"{'─'*60}")
                print(f"Total cost: ${total_cost:.4f}")
                print(f"{'='*60}\n")
                
                # Warning if output is close to limit
                if output_tokens > self.max_output_tokens * 0.9:
                    print(f"⚠️  WARNING: Output tokens ({output_tokens}) near limit ({self.max_output_tokens})")
                    print(f"   Plan may be truncated. Consider increasing max_tokens if needed.")
                
                # Track costs in log file
                tracker = get_cost_tracker()
                tracker.log_cost(
                    cluster_id=cluster_id,
                    model=self.model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=total_cost,
                    success=True
                )
                
                # Extract JSON from response with detailed logging
                try:
                    plan_json = self._extract_json(response.content[0].text)
                    print(f"✅ JSON parsing succeeded")
                    print(f"   Keys in plan_json: {list(plan_json.keys())}")
                except Exception as parse_error:
                    print(f"❌ JSON PARSING FAILED!")
                    print(f"   Error: {parse_error}")
                    print(f"\n   Raw content that failed to parse:")
                    print(f"   {response.content[0].text}")
                    raise
                
                # Add required fields if missing
                if 'generated_at' not in plan_json:
                    plan_json['generated_at'] = datetime.utcnow().isoformat()
                if 'cluster_id' not in plan_json:
                    plan_json['cluster_id'] = cluster_id
                if 'version' not in plan_json:
                    plan_json['version'] = "1.0"
                if 'generated_by' not in plan_json:
                    plan_json['generated_by'] = f"claude-api-{self.model}"
                
                # Validate against schema with context optimization info
                try:
                    plan = self.validator.validate(plan_json, cluster_id, cluster_name, optimization_report)
                    print(f"✅ Validation succeeded")
                except Exception as validation_error:
                    print(f"❌ VALIDATION FAILED!")
                    print(f"   Error: {validation_error}")
                    print(f"\n   Plan dict that failed validation:")
                    print(json.dumps(plan_json, indent=2)[:2000])
                    raise
                
                # Add metadata including optimization info
                plan.generated_at = datetime.utcnow()
                plan.version = "1.0"
                plan.generated_by = f"claude-api-{self.model}"
                
                # Add context optimization metadata to plan
                plan.metadata.context_optimization = {
                    "original_tokens": original_tokens,
                    "optimized_tokens": optimized_tokens,
                    "optimization_strategy": optimized_context.get('context_type'),
                    "reduction_percentage": optimization_report.get('reduction_percentage', 0)
                }
                
                self.logger.info(f"Successfully generated plan with {plan.total_actions} actions")
                return plan
                
            except anthropic.NotFoundError as e:
                # 404 = Model doesn't exist - DON'T RETRY (wastes money!)
                print(f"❌ Model not found: {self.model}")
                print(f"   This is a configuration error, not a temporary issue.")
                print(f"   Retrying won't help and costs money!")
                raise e  # Fail immediately, don't retry
                
            except anthropic.RateLimitError as e:
                # Rate limit - retry with exponential backoff
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                print(f"⚠️ Rate limited, waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
                
            except anthropic.APIError as e:
                # Other API errors - retry
                if attempt == max_retries - 1:
                    print(f"❌ All {max_retries} attempts failed")
                    raise
                wait_time = 2 ** attempt
                print(f"⚠️ API error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"   This means Claude didn't return valid JSON")
                if attempt < max_retries - 1:
                    print(f"⚠️ This retry will cost additional money!")
                    wait_time = 2 ** attempt
                    print(f"   Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ All {max_retries} attempts failed - no more retries")
                    # Don't raise here - let it fall through to the final error
                    
            except Exception as e:
                print(f"\n{'='*70}")
                print(f"🔍 DETAILED ERROR ANALYSIS")
                print(f"{'='*70}")
                
                # Show error type and message
                print(f"\nError Type: {type(e).__name__}")
                print(f"Error Message: {str(e)}")
                
                # If it's from Claude API, show response details
                if hasattr(e, 'response'):
                    print(f"\nAPI Response:")
                    print(f"   Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
                    print(f"   Body: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
                
                # Show what we sent to Claude
                print(f"\nContext sent to Claude:")
                print(f"   Cluster: {cluster_name}")
                print(f"   Input keys: {list(optimized_context.keys())}")
                if 'optimization_metadata' in optimized_context:
                    print(f"   Optimization: {optimized_context['optimization_metadata']}")
                
                # Show response if we got one
                if 'response' in locals():
                    print(f"\nClaude Response:")
                    print(f"   Content length: {len(response.content[0].text) if hasattr(response, 'content') else 'N/A'}")
                    print(f"   First 500 chars: {response.content[0].text[:500] if hasattr(response, 'content') else 'N/A'}")
                
                # Show parsing attempt
                if 'plan_json' in locals():
                    print(f"\nParsed plan keys: {list(plan_json.keys())}")
                
                # Show validation errors
                if 'validation' in str(e).lower():
                    print(f"\n⚠️ This looks like a VALIDATION error")
                    print(f"   The API call succeeded, but the response didn't pass validation")
                
                # Show full traceback
                import traceback
                print(f"\nFull Traceback:")
                print(traceback.format_exc())
                
                print(f"{'='*70}\n")
                
                # Save the failing input for debugging
                debug_file = f"debug_failed_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                try:
                    with open(debug_file, 'w') as f:
                        json.dump({
                            'cluster_name': cluster_name,
                            'cluster_id': cluster_id,
                            'optimized_context': optimized_context,
                            'error': str(e),
                            'error_type': type(e).__name__,
                            'timestamp': datetime.now().isoformat(),
                            'attempt': attempt + 1,
                            'model': self.model
                        }, f, indent=2, default=str)
                    
                    print(f"💾 Failed input saved to: {debug_file}")
                    print(f"   Use this file to reproduce the error!")
                except Exception as save_error:
                    print(f"⚠️ Could not save debug file: {save_error}")
                
                if attempt < max_retries - 1:
                    print(f"⚠️ This retry will cost additional money!")
                    wait_time = 2 ** attempt
                    print(f"   Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ All {max_retries} attempts failed - no more retries")
                    # Don't raise here - let it fall through to the final error
                
        # PRODUCTION SYSTEM: NO FALLBACKS - Fail fast with clear error
        error_msg = (
            f"Claude API plan generation failed after {max_retries} attempts for cluster {cluster_name}. "
            f"Model: {self.model}. Check API key, network connectivity, and model availability. "
            f"This is a production system - no fallback plans will be generated."
        )
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    async def generate_plan_split(
        self,
        enhanced_input: dict,
        cluster_name: str,
        cluster_id: str
    ) -> dict:
        """
        Generate complete plan using two API calls (for Haiku).
        
        Call 1: Core implementation plan (~3,000 tokens)
        Call 2: Detailed analysis (~2,500 tokens)
        
        Returns: Combined complete plan dictionary
        """
        
        print(f"\n{'='*70}")
        print(f"🔀 SPLIT GENERATION MODE (2 API Calls)")
        print(f"{'='*70}")
        print(f"Cluster: {cluster_name}")
        print(f"Model: {self.model}")
        print(f"Expected cost: ~$0.008 (2 × $0.004)")
        print(f"{'='*70}\n")
        
        # Build optimized context
        context = self.context_builder.build_optimized_context(enhanced_input, cluster_name)
        
        # Track totals
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        
        # ═══════════════════════════════════════════════════════
        # CALL 1: CORE IMPLEMENTATION PLAN
        # ═══════════════════════════════════════════════════════
        
        print(f"{'─'*70}")
        print(f"📤 CALL 1/2: Generating core implementation plan...")
        print(f"{'─'*70}")
        
        core_system_prompt = self._build_core_plan_system_prompt()
        core_user_prompt = self._build_core_plan_user_prompt(context, cluster_name)
        
        try:
            core_response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=3500,  # Safe buffer under 4,096
                temperature=0.3,
                system=core_system_prompt,
                messages=[{"role": "user", "content": core_user_prompt}]
            )
            
            # Track usage
            call1_input = core_response.usage.input_tokens
            call1_output = core_response.usage.output_tokens
            call1_cost = self._calculate_cost(call1_input, call1_output)
            
            total_input_tokens += call1_input
            total_output_tokens += call1_output
            total_cost += call1_cost
            
            print(f"✅ Call 1 complete")
            print(f"   Input: {call1_input:,} tokens")
            print(f"   Output: {call1_output:,} tokens ({call1_output/3500*100:.1f}% of limit)")
            print(f"   Cost: ${call1_cost:.6f}")
            
            # Parse JSON
            response_text = core_response.content[0].text
            print(f"📥 Raw response preview: {response_text[:500]}...")
            
            try:
                core_plan = self._extract_json_from_response(response_text)
                if not core_plan:
                    raise ValueError("Failed to extract JSON from core plan response")
                print(f"✅ Core plan parsed: {list(core_plan.keys())}")
            except Exception as parse_error:
                print(f"❌ JSON parsing failed!")
                print(f"   Error: {parse_error}")
                print(f"   Full response:")
                print(f"   {response_text}")
                raise ValueError(f"Failed to parse JSON: {parse_error}")
            
        except Exception as e:
            print(f"❌ Call 1 failed: {e}")
            raise RuntimeError(f"Core plan generation failed: {e}")
        
        # ═══════════════════════════════════════════════════════
        # CALL 2: DETAILED ANALYSIS
        # ═══════════════════════════════════════════════════════
        
        print(f"\n{'─'*70}")
        print(f"📤 CALL 2/2: Generating detailed analysis...")
        print(f"{'─'*70}")
        
        analysis_system_prompt = self._build_analysis_system_prompt()
        analysis_user_prompt = self._build_analysis_user_prompt(context, cluster_name)
        
        try:
            analysis_response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=3000,  # Slightly smaller
                temperature=0.3,
                system=analysis_system_prompt,
                messages=[{"role": "user", "content": analysis_user_prompt}]
            )
            
            # Track usage
            call2_input = analysis_response.usage.input_tokens
            call2_output = analysis_response.usage.output_tokens
            call2_cost = self._calculate_cost(call2_input, call2_output)
            
            total_input_tokens += call2_input
            total_output_tokens += call2_output
            total_cost += call2_cost
            
            print(f"✅ Call 2 complete")
            print(f"   Input: {call2_input:,} tokens")
            print(f"   Output: {call2_output:,} tokens ({call2_output/3000*100:.1f}% of limit)")
            print(f"   Cost: ${call2_cost:.6f}")
            
            # Parse JSON
            analysis = self._extract_json_from_response(analysis_response.content[0].text)
            
            if not analysis:
                print(f"⚠️ Call 2 failed to parse - using minimal analysis")
                analysis = self._get_minimal_analysis()
            else:
                print(f"✅ Analysis parsed: {list(analysis.keys())}")
            
        except Exception as e:
            print(f"⚠️ Call 2 failed: {e}")
            print(f"   Proceeding with core plan only")
            analysis = self._get_minimal_analysis()
            # Don't raise - core plan is enough to proceed
        
        # ═══════════════════════════════════════════════════════
        # MERGE AND RETURN
        # ═══════════════════════════════════════════════════════
        
        print(f"\n{'─'*70}")
        print(f"🔗 Merging results...")
        print(f"{'─'*70}")
        
        # Combine into complete plan
        complete_plan = {
            'implementation_plan': {
                # From Call 1 (Core)
                'metadata': core_plan.get('metadata', {}),
                'implementation_summary': core_plan.get('implementation_summary', {}),
                'phases': core_plan.get('phases', []),
                'roi_summary': core_plan.get('roi_summary', {}),
                'monitoring': core_plan.get('monitoring', {}),
                'next_steps': core_plan.get('next_steps', []),
                
                # From Call 2 (Analysis)
                'cluster_dna_analysis': analysis.get('cluster_dna_analysis', {}),
                'build_quality_assessment': analysis.get('build_quality_assessment', {}),
                'naming_conventions_analysis': analysis.get('naming_conventions_analysis', {}),
                'roi_analysis': analysis.get('roi_analysis', {}),
                'review_schedule': analysis.get('review_schedule', []),
            }
        }
        
        # Add metadata
        complete_plan['generated_at'] = datetime.utcnow()
        complete_plan['cluster_id'] = cluster_id
        complete_plan['generation_method'] = 'split_dual_call'
        
        # ═══════════════════════════════════════════════════════
        # SUMMARY
        # ═══════════════════════════════════════════════════════
        
        print(f"\n{'='*70}")
        print(f"💰 SPLIT GENERATION COMPLETE")
        print(f"{'='*70}")
        print(f"Total input tokens:  {total_input_tokens:,}")
        print(f"Total output tokens: {total_output_tokens:,}")
        print(f"Total tokens:        {total_input_tokens + total_output_tokens:,}")
        print(f"Total cost:          ${total_cost:.6f}")
        print(f"")
        print(f"✅ Full rich plan generated with 2 API calls!")
        print(f"   47% cheaper than Sonnet 3.5 single call")
        print(f"{'='*70}\n")
        
        return complete_plan
    
    def _build_system_prompt(self) -> str:
        """
        Defines Claude's role and output format with YAML-based standards.
        Fixed f-string formatting issue by separating dynamic and static content.
        """
        # Load standards from YAML configuration
        loader = get_standards_loader()
        scoring_standards = loader.load_scoring_standards()
        impl_standards = loader.load_implementation_standards()
        
        cpu_standards = loader.get_cpu_utilization_target()
        memory_standards = loader.get_memory_utilization_target()
        hpa_standards = loader.get_hpa_standards()
        opt_thresholds = loader.get_optimization_thresholds()
        
        # Get JSON schema (already a string, no formatting issues)
        schema_json = json.dumps(KUBEOPT_IMPLEMENTATION_PLAN_SCHEMA, indent=2)
        
        # Build dynamic standards section with f-string
        standards_section = f"""These standards are based on: CNCF, FinOps Foundation, Azure Well-Architected Framework, Google SRE
Configuration Version: {scoring_standards.get('version', 'unknown')} / {impl_standards.get('version', 'unknown')}

CPU Utilization Standards:
- Target Range: {cpu_standards['target_min']:.0f}%-{cpu_standards['target_max']:.0f}%
- Optimal: {cpu_standards['optimal']:.0f}%
- Source: {cpu_standards['source']}

Memory Utilization Standards:
- Target Range: {memory_standards['target_min']:.0f}%-{memory_standards['target_max']:.0f}%
- Optimal: {memory_standards['optimal']:.0f}%
- Source: {memory_standards['source']}

HPA Standards:
- Target CPU Utilization: {hpa_standards['target_cpu_utilization']:.0f}%
- Target Memory Utilization: {hpa_standards['target_memory_utilization']:.0f}%
- Coverage Target: {hpa_standards['coverage_target']:.0f}% of eligible workloads
- Default Min Replicas: {hpa_standards['min_replicas_default']}
- Default Max Replicas: {hpa_standards['max_replicas_default']}
- Source: {hpa_standards['source']}

Optimization Decision Thresholds:
- Maximum Payback Period: {opt_thresholds['payback_threshold_months']} months
- Minimum Monthly Savings: ${opt_thresholds['minimum_monthly_savings']:.2f}
- Minimum Savings Percentage: {opt_thresholds['minimum_savings_percentage']*100:.1f}%
- High Priority Threshold: ${opt_thresholds['high_priority_savings']:.2f}/month"""
        
        # Build static schema and structure section WITHOUT f-string to avoid brace issues
        schema_section = f"""SCHEMA YOU MUST FOLLOW:
{schema_json}

OUTPUT FORMAT:
- Start your response with ```json
- End with ```
- No markdown except the code fence
- No explanatory text outside the JSON
- Structure must match the KubeOpt implementation_plan schema exactly"""
        
        # Static JSON structure example (no f-string, no formatting issues)
        structure_section = """REQUIRED STRUCTURE:
Your JSON must have this exact top-level structure:
{
  "implementation_plan": {
    "metadata": { ... },
    "cluster_dna_analysis": { ... },
    "build_quality_assessment": { ... },
    "naming_conventions_analysis": { ... },
    "roi_analysis": { ... },
    "implementation_summary": { ... },
    "phases": [ ... ],
    "monitoring": { ... },
    "review_schedule": [ ... ]
  }
}"""
        
        # Combine all sections
        return f"""You are a Kubernetes FinOps Expert specializing in AKS cost optimization.

Your task: Generate a detailed, actionable implementation plan for optimizing an AKS cluster based on cost analysis and cluster metrics.

═══════════════════════════════════════════════════════════════
OPTIMIZATION STANDARDS YOU MUST FOLLOW
═══════════════════════════════════════════════════════════════

{standards_section}

CRITICAL REQUIREMENTS:
1. Output MUST be valid JSON matching the ImplementationPlan schema
2. Be specific: include exact resource names, namespaces, kubectl commands
3. Prioritize by ROI: highest savings with lowest risk first
4. Include rollback plans for every action
5. Provide validation commands to verify success
6. Consider dependencies: some actions must happen before others
7. Be realistic about implementation times and risks
8. ALL RECOMMENDATIONS MUST ALIGN WITH THE YAML STANDARDS ABOVE

{schema_section}

{structure_section}

PLAN PHASES:
- Phase 1: Quick Wins (low-risk, immediate savings, orphaned resources)
- Phase 2: Right-sizing (resource optimization based on usage)
- Phase 3: HPA Implementation (dynamic scaling setup)
- Phase 4: Advanced Optimization (long-term improvements)

CRITICAL REQUIREMENTS:
- Include realistic cluster DNA analysis with scores 0-100
- Generate actionable kubectl commands for each step
- Provide specific resource names and namespaces from the analysis
- Calculate realistic cost savings based on actual data
- Include comprehensive rollback procedures
- Add monitoring commands and success criteria

═══════════════════════════════════════════════════════════════
⚠️ CRITICAL: TOKEN LIMIT
═══════════════════════════════════════════════════════════════

Your response MUST be under 3,000 tokens total.

To achieve this:
- Be concise and direct
- Focus on the most impactful actions (top 5-10)
- Combine related steps where possible
- Use brief descriptions (1-2 sentences)
- Prioritize quality over quantity
- Omit verbose explanations

Remember: Concise responses save money while maintaining quality."""
    
    def _build_user_prompt(self, optimized_context: Dict, cluster_name: str) -> str:
        """
        Builds user prompt from optimized context data.
        """
        context_type = optimized_context.get('context_type', 'complete')
        
        if context_type == 'complete':
            return self._build_complete_prompt(optimized_context, cluster_name)
        elif context_type == 'medium_optimization':
            return self._build_medium_prompt(optimized_context, cluster_name)
        else:  # aggressive_optimization
            return self._build_compact_prompt(optimized_context, cluster_name)
    
    def _build_complete_prompt(self, optimized_context: Dict, cluster_name: str) -> str:
        """Build prompt for complete data (small clusters)."""
        enhanced_input = optimized_context.get('data', {})
        cost_analysis = enhanced_input.get('cost_analysis', {})
        total_cost = cost_analysis.get('total_cost', 0)
        total_savings = cost_analysis.get('total_savings', 0)
        current_usage = cost_analysis.get('current_usage', {})
        savings_breakdown = cost_analysis.get('savings_breakdown', {})
        
        return f"""Generate an implementation plan for optimizing this AKS cluster.

CLUSTER: {cluster_name}
CONTEXT: Complete cluster analysis (small cluster)

ANALYSIS DATA:
```json
{json.dumps(enhanced_input, indent=2)}
```

FOCUS AREAS (based on the analysis):
- Current monthly cost: ${total_cost:.2f}
- Potential savings: ${total_savings:.2f}
- CPU utilization: {current_usage.get('cpu_utilization', 'N/A')}%
- Memory utilization: {current_usage.get('memory_utilization', 'N/A')}%
- HPA savings opportunity: ${savings_breakdown.get('hpa_savings', 0):.2f}
- Right-sizing savings opportunity: ${savings_breakdown.get('right_sizing_savings', 0):.2f}

REQUIREMENTS:
1. Generate a comprehensive, phased implementation plan
2. Include specific kubectl commands for each action
3. Provide accurate cost savings estimates
4. Include proper rollback procedures
5. Ensure all actions are executable and safe

Generate the complete implementation plan as valid JSON matching the schema."""

    def _build_medium_prompt(self, optimized_context: Dict, cluster_name: str) -> str:
        """Build prompt for medium optimization (medium clusters)."""
        cost_analysis = optimized_context.get('cost_analysis', {})
        executive_summary = optimized_context.get('executive_summary', {})
        workloads = optimized_context.get('workloads', [])
        
        cluster_summary = executive_summary.get('cluster_analysis_summary', {})
        opportunities = executive_summary.get('optimization_opportunities', [])
        
        return f"""Generate an implementation plan for optimizing this AKS cluster.

CLUSTER: {cluster_name}
CONTEXT: Medium cluster analysis - Top 30 resources with executive summary

EXECUTIVE SUMMARY:
- Total workloads: {cluster_summary.get('total_workloads', 0)}
- Monthly cost: ${cluster_summary.get('total_monthly_cost', 0):.2f}
- Optimization potential: ${cluster_summary.get('optimization_potential', 0):.2f}
- Cost reduction potential: {cluster_summary.get('cost_reduction_percentage', 0):.1f}%

KEY OPTIMIZATION OPPORTUNITIES:
{chr(10).join(f"- {opp}" for opp in opportunities)}

COST ANALYSIS:
```json
{json.dumps(cost_analysis, indent=2)}
```

TOP OPTIMIZATION TARGETS (30 highest impact workloads):
```json
{json.dumps(workloads, indent=2)}
```

CLUSTER PATTERNS:
```json
{json.dumps(executive_summary.get('workload_distribution', {}), indent=2)}
```

REQUIREMENTS:
1. Focus on the top 30 workloads provided for detailed recommendations
2. Generate phased implementation plan prioritizing highest ROI actions
3. Include specific kubectl commands for each action
4. Provide accurate cost savings estimates based on the data
5. Include proper rollback procedures for all changes
6. Consider cluster patterns in your recommendations

Generate the complete implementation plan as valid JSON matching the schema."""

    def _build_compact_prompt(self, optimized_context: Dict, cluster_name: str) -> str:
        """Build prompt for aggressive optimization (large clusters)."""
        cost_analysis = optimized_context.get('cost_analysis', {})
        executive_summary = optimized_context.get('executive_summary', {})
        aggregated_stats = optimized_context.get('aggregated_statistics', {})
        top_targets = optimized_context.get('top_optimization_targets', [])
        cluster_overview = optimized_context.get('cluster_overview', {})
        
        cluster_summary = executive_summary.get('cluster_analysis_summary', {})
        opportunities = executive_summary.get('optimization_opportunities', [])
        complexity = executive_summary.get('complexity_indicators', {})
        
        return f"""Generate an implementation plan for optimizing this large AKS cluster.

CLUSTER: {cluster_name}
CONTEXT: Large cluster analysis - Aggregated statistics with top 10 targets

CLUSTER OVERVIEW:
- Total workloads: {cluster_summary.get('total_workloads', 0)}
- Monthly cost: ${cluster_summary.get('total_monthly_cost', 0):.2f}
- Optimization potential: ${cluster_summary.get('optimization_potential', 0):.2f}
- Complexity score: {complexity.get('complexity_score', 0)}/100
- Namespaces: {complexity.get('namespace_count', 0)}

KEY OPTIMIZATION OPPORTUNITIES:
{chr(10).join(f"- {opp}" for opp in opportunities)}

ESSENTIAL COST DATA:
```json
{json.dumps(cost_analysis, indent=2)}
```

AGGREGATED CLUSTER STATISTICS:
```json
{json.dumps(aggregated_stats, indent=2)}
```

TOP 10 OPTIMIZATION TARGETS (highest impact):
```json
{json.dumps(top_targets, indent=2)}
```

CLUSTER METADATA:
```json
{json.dumps(cluster_overview, indent=2)}
```

REQUIREMENTS FOR LARGE CLUSTER:
1. Focus recommendations on the top 10 targets provided
2. Use aggregated statistics to inform cluster-wide recommendations
3. Prioritize namespace-level and resource-type-level optimizations
4. Generate scalable implementation phases suitable for large clusters
5. Include kubectl commands that can work with multiple resources
6. Provide cost savings estimates based on aggregated data
7. Consider cluster complexity in implementation timeline

Generate the complete implementation plan as valid JSON matching the schema."""

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from Claude's response with robust error handling."""
        text = text.strip()
        
        # Remove markdown code fences
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
            
        if text.endswith("```"):
            text = text[:-3]
            
        # Try to find JSON content
        text = text.strip()
        
        # Parse JSON with fallback cleaning
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"⚠️  Initial JSON parse failed: {e}")
            print(f"   Attempting to clean JSON...")
            
            # Try to find JSON within the text
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_text = text[start_idx:end_idx]
                
                # Clean common JSON issues
                cleaned_json = self._clean_json_text(json_text)
                
                try:
                    result = json.loads(cleaned_json)
                    print(f"✅ JSON cleaned and parsed successfully")
                    return result
                except json.JSONDecodeError as e2:
                    print(f"❌ Cleaning failed: {e2}")
                    raise e
            else:
                raise e
    
    def _clean_json_text(self, json_text: str) -> str:
        """Clean common JSON formatting issues from Claude responses"""
        import re
        
        # Fix percentage values (e.g., "120%" -> "120")
        json_text = re.sub(r':\s*(\d+(?:\.\d+)?)%', r': \1', json_text)
        
        # Fix currency values (e.g., "$342.85" -> "342.85")
        json_text = re.sub(r':\s*"\$(\d+(?:\.\d+)?)"', r': \1', json_text)
        json_text = re.sub(r':\s*\$(\d+(?:\.\d+)?)', r': \1', json_text)
        
        # Remove trailing commas before closing braces/brackets
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
        
        # Fix unquoted property names
        json_text = re.sub(r'(\w+):', r'"\1":', json_text)
        
        # Fix single quotes to double quotes
        json_text = re.sub(r"'([^']*)'", r'"\1"', json_text)
        
        # Remove comments (// or /* */)
        json_text = re.sub(r'//.*?$', '', json_text, flags=re.MULTILINE)
        json_text = re.sub(r'/\*.*?\*/', '', json_text, flags=re.DOTALL)
        
        return json_text
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on model"""
        if "haiku" in self.model.lower():
            return (input_tokens * 0.25 + output_tokens * 1.25) / 1_000_000
        elif "sonnet" in self.model.lower() and "3-5" in self.model:
            return (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000
        else:
            return (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000

    def _get_minimal_analysis(self) -> dict:
        """Return minimal analysis structure as fallback"""
        return {
            'cluster_dna_analysis': {
                'overall_score': 0,
                'description': 'Analysis unavailable'
            },
            'build_quality_assessment': {
                'quality_checks': []
            },
            'naming_conventions_analysis': {
                'overall_score': 0
            },
            'roi_analysis': {
                'summary_metrics': []
            },
            'review_schedule': []
        }
    
    def _extract_json_from_response(self, text: str) -> dict:
        """Extract JSON from response text"""
        return self._extract_json(text)
    
    def _build_core_plan_system_prompt(self) -> str:
        """System prompt for core implementation plan (Call 1)"""
        
        from shared.standards.standards_loader import get_standards_loader
        loader = get_standards_loader()
        
        # Get individual standards components
        cpu_standards = loader.get_cpu_utilization_target()
        memory_standards = loader.get_memory_utilization_target()
        hpa_standards = loader.get_hpa_standards()
        optimization_thresholds = loader.get_optimization_thresholds()
        
        standards_text = self._format_standards_brief({
            'resource_utilization': {
                'cpu': cpu_standards,
                'memory': memory_standards
            },
            'hpa_standards': hpa_standards,
            'optimization_thresholds': optimization_thresholds
        })
        
        return f"""You are a Kubernetes FinOps Expert creating actionable implementation plans.

CRITICAL: This is PART 1 of a 2-part response. Generate ONLY the core implementation plan.

Your response must be under 3,000 tokens and include ONLY:
✅ metadata (plan_id, cluster_name, generated_date)
✅ implementation_summary (costs, savings, duration, phases count)
✅ phases (2-4 phases with detailed actions containing steps, commands, rollback)
✅ roi_summary (monthly_savings, annual_savings, payback_months, roi_percentage)
✅ monitoring (key_commands array, success_metrics array)
✅ next_steps (array of 3-5 milestone strings)

DO NOT INCLUDE (these are in Part 2):
❌ cluster_dna_analysis
❌ build_quality_assessment
❌ naming_conventions_analysis
❌ roi_analysis (full breakdown)
❌ detailed review_schedule

STANDARDS TO FOLLOW:
{standards_text}

OUTPUT FORMAT:
Respond ONLY with valid JSON wrapped in ```json code fence.
No explanatory text before or after.

CRITICAL JSON RULES:
- ALL strings must be in double quotes
- Numbers must be pure numbers (no %, $, or other symbols)
- Use decimal numbers for percentages (e.g., 0.75 not 75%)
- Use numbers for currency (e.g., 342.85 not "$342.85")
- No trailing commas
- No comments inside JSON

Example structure:
```json
{{
  "metadata": {{ "plan_id": "...", "cluster_name": "...", "generated_date": "..." }},
  "implementation_summary": {{ "current_monthly_cost": 2111.71, "estimated_monthly_savings": 342.85 }},
  "phases": [{{ "phase_number": 1, "actions": [...] }}],
  "roi_summary": {{ "monthly_savings": 342.85, "roi_percentage": 1.2 }},
  "monitoring": {{ "key_commands": [...], "success_metrics": [...] }},
  "next_steps": ["Day 7: ...", "Day 21: ...", ...]
}}
```

Be concise and actionable. Focus on high-impact optimizations."""

    def _build_core_plan_user_prompt(self, context: dict, cluster_name: str) -> str:
        """User prompt for core implementation plan"""
        
        import json
        context_json = json.dumps(context, indent=2)
        
        return f"""Generate a core implementation plan for cluster: {cluster_name}

Cluster context:
{context_json}

Generate phases with actionable steps, kubectl commands, and rollback procedures.
Focus on the top 5-10 highest-impact optimizations.
Keep response under 3,000 tokens."""

    def _build_analysis_system_prompt(self) -> str:
        """System prompt for detailed analysis (Call 2)"""
        
        return """You are a Kubernetes FinOps Expert analyzing cluster quality and compliance.

CRITICAL: This is PART 2 of a 2-part response. Generate ONLY the detailed analysis.

Your response must be under 2,500 tokens and include ONLY:
✅ cluster_dna_analysis (overall_score, metrics, data_sources)
✅ build_quality_assessment (quality_checks, strengths, improvements, scorecard)
✅ naming_conventions_analysis (overall_score, resources, recommendations)
✅ roi_analysis (summary_metrics, calculation_breakdown, savings_by_phase)
✅ review_schedule (array of milestone objects with day and title)

DO NOT INCLUDE (already in Part 1):
❌ metadata
❌ implementation_summary
❌ phases
❌ roi_summary
❌ monitoring
❌ next_steps

OUTPUT FORMAT:
Respond ONLY with valid JSON wrapped in ```json code fence.

CRITICAL JSON RULES:
- ALL strings must be in double quotes
- Numbers must be pure numbers (no %, $, or other symbols)
- Use decimal numbers for percentages (e.g., 0.89 not 89%)
- Use numbers for currency (e.g., 342.85 not "$342.85")
- No trailing commas
- No comments inside JSON

Example structure:
```json
{
  "cluster_dna_analysis": { "overall_score": 0.89, "metrics": [...] },
  "build_quality_assessment": { "quality_checks": [...] },
  "naming_conventions_analysis": { "overall_score": 0.78 },
  "roi_analysis": { "summary_metrics": [...] },
  "review_schedule": [{"day": 7, "title": "..."}, ...]
}
```

Be thorough but concise. Stay under 2,500 tokens."""

    def _build_analysis_user_prompt(self, context: dict, cluster_name: str) -> str:
        """User prompt for detailed analysis"""
        
        import json
        context_json = json.dumps(context, indent=2)
        
        return f"""Generate detailed quality analysis for cluster: {cluster_name}

Cluster context:
{context_json}

Analyze cluster DNA, build quality, naming conventions, and provide detailed ROI breakdown.
Keep response under 2,500 tokens."""

    def _format_standards_brief(self, standards: dict) -> str:
        """Format standards briefly for prompt"""
        cpu = standards['resource_utilization']['cpu']
        mem = standards['resource_utilization']['memory']
        hpa = standards['hpa_standards']
        opt = standards.get('optimization_thresholds', {})
        
        standards_text = f"""CPU: {cpu['target_min']:.0f}-{cpu['target_max']:.0f}% target, {cpu['optimal']:.0f}% optimal
Memory: {mem['target_min']:.0f}-{mem['target_max']:.0f}% target, {mem['optimal']:.0f}% optimal
HPA: {hpa['target_cpu_utilization']}% CPU target, {hpa['coverage_target']:.0f}% coverage goal"""
        
        if opt:
            standards_text += f"""
Optimization Thresholds: Max {opt['payback_threshold_months']} months payback, min ${opt['minimum_monthly_savings']:.2f}/month"""
        
        return standards_text
    
