
import os
import json
import time
import sympy
import random
import google.generativeai as genai
from sympy import symbols, Eq, solve, sympify

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model for reasoning
reasoning_config = {
    "temperature": 0.2,  # Lower temperature for more logical responses
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 4096,
}

reasoning_model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=reasoning_config,
)

reasoning_chat = reasoning_model.start_chat(history=[])

class SymbolicReasoning:
    def __init__(self):
        self.rules_file = "symbolic_rules.json"
        self.load_rules()
        self.last_reasoning_time = time.time()
        
    def load_rules(self):
        """Load symbolic reasoning rules"""
        try:
            with open(self.rules_file, 'r') as f:
                self.rules = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.rules = {
                "logical_rules": [
                    {"name": "modus_ponens", "description": "If A implies B, and A is true, then B is true"},
                    {"name": "modus_tollens", "description": "If A implies B, and B is false, then A is false"},
                    {"name": "disjunctive_syllogism", "description": "If (A or B) is true, and A is false, then B is true"}
                ],
                "domain_rules": {},
                "mathematical_rules": [
                    {"name": "transitivity", "description": "If A = B and B = C, then A = C"},
                    {"name": "distributivity", "description": "A * (B + C) = (A * B) + (A * C)"}
                ]
            }
            self.save_rules()
    
    def save_rules(self):
        """Save symbolic reasoning rules"""
        try:
            with open(self.rules_file, 'w') as f:
                json.dump(self.rules, f, indent=2)
        except Exception as e:
            print(f"Error saving symbolic rules: {e}")
    
    def add_domain_rule(self, domain, rule_name, rule_description, rule_formula=None):
        """Add a domain-specific rule"""
        if domain not in self.rules["domain_rules"]:
            self.rules["domain_rules"][domain] = []
            
        rule = {
            "name": rule_name,
            "description": rule_description
        }
        
        if rule_formula:
            rule["formula"] = rule_formula
            
        self.rules["domain_rules"][domain].append(rule)
        self.save_rules()
        
        return True
    
    def symbolic_solve(self, problem_statement):
        """Attempt to solve a problem using symbolic mathematics"""
        try:
            # Use LLM to translate problem to symbolic form
            translation_prompt = f"""
            Translate this problem into symbolic mathematics using SymPy syntax:
            
            PROBLEM: {problem_statement}
            
            Format your response as:
            VARIABLES: [list variable names and what they represent]
            EQUATIONS: [list equations in SymPy syntax]
            GOAL: [what we're solving for]
            """
            
            translation_response = reasoning_chat.send_message(translation_prompt)
            translation_text = translation_response.text
            
            variables_section = None
            equations_section = None
            goal_section = None
            
            # Parse the response
            for line in translation_text.split('\n'):
                if line.startswith('VARIABLES:'):
                    variables_section = line[len('VARIABLES:'):].strip()
                elif line.startswith('EQUATIONS:'):
                    equations_section = line[len('EQUATIONS:'):].strip()
                elif line.startswith('GOAL:'):
                    goal_section = line[len('GOAL:'):].strip()
            
            if not variables_section or not equations_section or not goal_section:
                return {
                    "success": False,
                    "error": "Could not parse problem into symbolic form",
                    "result": None
                }
            
            # Execute symbolic math using SymPy
            # This is a simplified approach - a full implementation would need more robust parsing
            try:
                # Create symbolic variables
                var_list = variables_section.split(',')
                var_symbols = {}
                
                for var in var_list:
                    var_name = var.strip().split(' ')[0]
                    var_symbols[var_name] = symbols(var_name)
                
                # Parse equations
                equations = []
                for eq_str in equations_section.split(','):
                    eq_str = eq_str.strip()
                    if '=' in eq_str:
                        left, right = eq_str.split('=')
                        eq = Eq(sympify(left), sympify(right))
                        equations.append(eq)
                
                # Solve the system
                goal_var = goal_section.strip()
                solution = solve(equations, var_symbols[goal_var])
                
                return {
                    "success": True,
                    "result": str(solution),
                    "variables": variables_section,
                    "equations": equations_section,
                    "goal": goal_section
                }
                
            except Exception as e:
                # If SymPy execution fails, fallback to LLM-based reasoning
                return self.llm_reasoning(problem_statement)
                
        except Exception as e:
            print(f"Error in symbolic solving: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def llm_reasoning(self, problem_statement):
        """Use LLM for step-by-step reasoning when symbolic methods fail"""
        try:
            reasoning_prompt = f"""
            Please solve this problem using step-by-step logical reasoning:
            
            PROBLEM: {problem_statement}
            
            Break down your solution into clear steps:
            1. Identify the givens
            2. Determine what we need to find
            3. Apply relevant formulas or logical rules
            4. Show your work step by step
            5. Verify your answer if possible
            
            Format your response as:
            GIVENS: [list what is known]
            TO FIND: [what we need to calculate or determine]
            STEPS: [numbered steps of your solution]
            ANSWER: [final answer]
            """
            
            response = reasoning_chat.send_message(reasoning_prompt)
            
            return {
                "success": True,
                "result": response.text,
                "method": "llm_reasoning"
            }
            
        except Exception as e:
            print(f"Error in LLM reasoning: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def logical_deduction(self, premises, conclusion):
        """Check if conclusion follows from premises using logical deduction"""
        try:
            deduction_prompt = f"""
            Determine if the conclusion logically follows from the given premises:
            
            PREMISES:
            {premises}
            
            CONCLUSION:
            {conclusion}
            
            Use formal logical reasoning to determine if the conclusion necessarily follows.
            Analyze step by step, considering logical rules like modus ponens, modus tollens, etc.
            
            Format your response as:
            ANALYSIS: [Step by step analysis of the argument]
            VALID: [YES or NO - whether the conclusion logically follows]
            EXPLANATION: [Explain why the argument is valid or invalid]
            """
            
            response = reasoning_chat.send_message(deduction_prompt)
            
            # Parse response
            valid = "YES" in response.text and "VALID: YES" in response.text
            
            return {
                "success": True,
                "valid": valid,
                "reasoning": response.text
            }
            
        except Exception as e:
            print(f"Error in logical deduction: {e}")
            return {
                "success": False,
                "error": str(e),
                "valid": False
            }
    
    def discover_new_rules(self, domain, samples):
        """Discover potential new rules from observed patterns"""
        try:
            # Skip if ran recently (resource intensive)
            if time.time() - self.last_reasoning_time < 3600:  # Once per hour
                return False
                
            self.last_reasoning_time = time.time()
            
            samples_text = "\n".join([f"Sample {i+1}: {sample}" for i, sample in enumerate(samples)])
            
            discovery_prompt = f"""
            Analyze these examples from the domain of {domain} and identify any underlying patterns, rules, or principles:
            
            {samples_text}
            
            Identify any consistent patterns that could be formulated as general rules.
            Look for mathematical relationships, logical implications, or causal connections.
            
            Format your response as:
            PATTERN 1: [Description of the pattern]
            RULE 1: [Formal statement of the rule]
            CONFIDENCE 1: [A number between 0 and 1 indicating confidence]
            
            PATTERN 2: [Description of the pattern]
            RULE 2: [Formal statement of the rule]
            CONFIDENCE 2: [A number between 0 and 1 indicating confidence]
            
            (And so on for any additional patterns)
            """
            
            response = reasoning_chat.send_message(discovery_prompt)
            
            # Parse rules from response
            discovered_rules = []
            current_rule = {}
            
            for line in response.text.split('\n'):
                line = line.strip()
                if line.startswith('PATTERN'):
                    # Start a new rule
                    if current_rule and 'pattern' in current_rule and 'rule' in current_rule:
                        discovered_rules.append(current_rule)
                    current_rule = {'confidence': 0.7}  # Default confidence
                    current_rule['pattern'] = line.split(':', 1)[1].strip()
                elif line.startswith('RULE'):
                    current_rule['rule'] = line.split(':', 1)[1].strip()
                elif line.startswith('CONFIDENCE'):
                    try:
                        conf = float(line.split(':', 1)[1].strip())
                        current_rule['confidence'] = min(max(conf, 0), 1)  # Ensure in [0,1]
                    except:
                        pass
            
            # Add the last rule if it exists
            if current_rule and 'pattern' in current_rule and 'rule' in current_rule:
                discovered_rules.append(current_rule)
            
            # Filter by confidence and add to knowledge base
            for rule in discovered_rules:
                if rule['confidence'] >= 0.8:
                    self.add_domain_rule(
                        domain=domain,
                        rule_name=f"discovered_{int(time.time())}",
                        rule_description=rule['rule'],
                        rule_formula=rule.get('pattern')
                    )
            
            return True
            
        except Exception as e:
            print(f"Error discovering rules: {e}")
            return False

# Create singleton instance
symbolic_reasoning = SymbolicReasoning()
