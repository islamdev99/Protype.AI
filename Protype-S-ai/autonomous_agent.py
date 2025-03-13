
import os
import time
import json
import random
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import datetime
import traceback

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model for agent
agent_config = {
    "temperature": 0.2,  # Lower temperature for more deterministic responses
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 4096,
}

gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=agent_config,
)

agent_chat = gemini_model.start_chat(history=[])

class AutonomousAgent:
    def __init__(self):
        self.objectives = []
        self.completed_objectives = []
        self.knowledge_gained = {}
        self.action_history = []
        self.max_steps = 10  # Maximum steps per objective
        self.max_search_results = 3
        self.min_search_term_length = 5
        self.agent_state = "idle"  # idle, active, paused
        self.decision_history = []
        self.decision_file = "agent_decisions.json"
        self.autonomous_mode = False  # controls full autonomy
        self.last_objective_generation = 0  # timestamp of last auto-generated objective
        self.auto_objective_interval = 86400  # generate new objectives daily (in seconds)
        self.load_state()
        self.load_decisions()
        
    def load_state(self):
        """Load agent state from disk"""
        try:
            if os.path.exists('agent_state.json'):
                with open('agent_state.json', 'r') as f:
                    state = json.load(f)
                    self.objectives = state.get('objectives', [])
                    self.completed_objectives = state.get('completed_objectives', [])
                    self.knowledge_gained = state.get('knowledge_gained', {})
                    self.action_history = state.get('action_history', [])
                    self.agent_state = state.get('agent_state', 'idle')
                    self.autonomous_mode = state.get('autonomous_mode', False)
                    self.last_objective_generation = state.get('last_objective_generation', 0)
                print(f"Loaded agent state: {len(self.objectives)} active objectives, {len(self.completed_objectives)} completed")
        except Exception as e:
            print(f"Error loading agent state: {e}")
    
    def load_decisions(self):
        """Load agent decisions from disk"""
        try:
            if os.path.exists(self.decision_file):
                with open(self.decision_file, 'r') as f:
                    self.decision_history = json.load(f)
            else:
                self.decision_history = []
        except Exception as e:
            print(f"Error loading decisions: {e}")
            self.decision_history = []
    
    def save_decisions(self):
        """Save agent decisions to disk"""
        try:
            with open(self.decision_file, 'w') as f:
                json.dump(self.decision_history, f, indent=2)
        except Exception as e:
            print(f"Error saving decisions: {e}")
            
    def save_state(self):
        """Save agent state to disk"""
        try:
            state = {
                'objectives': self.objectives,
                'completed_objectives': self.completed_objectives,
                'knowledge_gained': self.knowledge_gained,
                'action_history': self.action_history,
                'agent_state': self.agent_state,
                'autonomous_mode': self.autonomous_mode,
                'last_objective_generation': self.last_objective_generation
            }
            
            with open('agent_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            print("Saved agent state")
        except Exception as e:
            print(f"Error saving agent state: {e}")
    
    def add_objective(self, objective):
        """Add a new learning objective"""
        if objective not in self.objectives and objective not in [o['objective'] for o in self.completed_objectives]:
            self.objectives.append(objective)
            self.log_action("add_objective", f"Added new objective: {objective}")
            self.save_state()
            return True
        return False
    
    def start_agent(self, autonomous_mode=False):
        """Start the autonomous agent"""
        if self.agent_state == "active":
            return "Agent is already active"
            
        self.agent_state = "active"
        self.autonomous_mode = autonomous_mode
        
        if autonomous_mode:
            self.log_action("system", "Agent activated in autonomous mode")
        else:
            self.log_action("system", "Agent activated in supervised mode")
            
        self.save_state()
        
        # Start autonomous thread if in autonomous mode
        if self.autonomous_mode:
            self.autonomous_thread = threading.Thread(target=self.autonomous_loop, daemon=True)
            self.autonomous_thread.start()
            return "Agent started in autonomous mode"
        else:
            # Process objectives until none remain or agent is paused
            while self.objectives and self.agent_state == "active":
                self.process_next_objective()
                time.sleep(2)  # Prevent overloading
                
            if not self.objectives:
                self.agent_state = "idle"
                self.log_action("system", "All objectives completed, agent returning to idle state")
            
            self.save_state()
            return "Agent process completed"
    
    def autonomous_loop(self):
        """Main loop for autonomous operation"""
        self.log_action("autonomous", "Started autonomous operation loop")
        
        while self.agent_state == "active" and self.autonomous_mode:
            try:
                # If no objectives, generate some
                if not self.objectives:
                    self.auto_generate_objectives()
                
                # Check knowledge gaps
                self.identify_knowledge_gaps()
                
                # Process next objective if available
                if self.objectives:
                    self.process_next_objective()
                
                # Reflect on recent outcomes
                self.reflect_on_outcomes()
                
                # Generate new related objectives
                self.auto_expand_knowledge()
                
                # Sleep to prevent overloading
                time.sleep(10)
                
            except Exception as e:
                self.log_action("error", f"Error in autonomous loop: {str(e)}")
                traceback.print_exc()
                time.sleep(30)  # Longer sleep on error
        
        self.log_action("autonomous", "Exited autonomous operation loop")
    
    def auto_generate_objectives(self, count=3):
        """Automatically generate new learning objectives"""
        # Check if enough time has passed since last generation
        current_time = time.time()
        if current_time - self.last_objective_generation < self.auto_objective_interval:
            return
            
        self.last_objective_generation = current_time
        
        try:
            # Generate objectives based on trending topics or from existing knowledge
            if random.random() < 0.7 and self.knowledge_gained:
                # 70% chance to expand on existing knowledge
                topics = list(self.knowledge_gained.keys())
                if topics:
                    base_topic = random.choice(topics)
                    self.log_action("autonomous", f"Generating objectives based on existing topic: {base_topic}")
                    self.generate_new_objectives(base_topic, count)
            else:
                # 30% chance to explore trending topics
                trending_prompt = """
                Generate 3 interesting educational topics that are worth learning about right now.
                These should be specific, diverse topics that would expand knowledge in different areas.
                
                Format your response as a numbered list with no additional text.
                """
                
                response = agent_chat.send_message(trending_prompt)
                
                topics = []
                for line in response.text.strip().split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() and line[1] in ['.', ')', ':']):
                        topic = line[2:].strip() if line[1] in [')', ':'] else line[3:].strip()
                        topics.append(topic)
                
                if topics:
                    topic = random.choice(topics)
                    self.log_action("autonomous", f"Generating objectives based on trending topic: {topic}")
                    self.generate_new_objectives(topic, count)
            
            self.save_state()
            
        except Exception as e:
            self.log_action("error", f"Error generating objectives: {str(e)}")
    
    def identify_knowledge_gaps(self):
        """Identify and address knowledge gaps"""
        if not self.knowledge_gained or len(self.knowledge_gained) < 5:
            return  # Not enough knowledge to identify gaps
            
        try:
            # Select random topics from knowledge base
            topics = list(self.knowledge_gained.keys())
            selected_topics = random.sample(topics, min(5, len(topics)))
            
            # Create knowledge context
            knowledge_context = ""
            for topic in selected_topics:
                knowledge_context += f"Topic: {topic}\n"
                knowledge_context += f"{self.knowledge_gained[topic][:500]}...\n\n"
            
            # Ask model to identify gaps
            gap_prompt = f"""
            Based on the following knowledge excerpts, identify important gaps or areas that need further exploration:
            
            {knowledge_context}
            
            Identify 1-3 specific knowledge gaps or questions that should be researched.
            Format as a numbered list with no additional text.
            """
            
            response = agent_chat.send_message(gap_prompt)
            
            # Extract gaps
            gaps = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() and line[1] in ['.', ')', ':']):
                    gap = line[2:].strip() if line[1] in [')', ':'] else line[3:].strip()
                    gaps.append(gap)
            
            # Add gaps as objectives
            if gaps:
                for gap in gaps:
                    self.add_objective(gap)
                    self.log_action("autonomous", f"Added knowledge gap as objective: {gap}")
                
                self.save_state()
                
        except Exception as e:
            self.log_action("error", f"Error identifying knowledge gaps: {str(e)}")
    
    def reflect_on_outcomes(self):
        """Reflect on recent outcomes to improve future performance"""
        # Get recent completed objectives (last 5)
        recent_completed = self.completed_objectives[-5:] if len(self.completed_objectives) >= 5 else self.completed_objectives
        
        if not recent_completed:
            return
            
        try:
            # Create reflection context
            reflection_context = "Recent completed objectives:\n"
            for obj in recent_completed:
                status = obj.get("status", "completed")
                reflection_context += f"- {obj['objective']} ({status})\n"
            
            # Ask model to reflect
            reflection_prompt = f"""
            Reflect on these recently completed objectives:
            
            {reflection_context}
            
            Based on these outcomes:
            1. What patterns or themes do you observe?
            2. What approaches worked well?
            3. What could be improved in future research?
            4. What related areas might be worth exploring next?
            
            Provide your reflection in a concise format.
            """
            
            response = agent_chat.send_message(reflection_prompt)
            
            # Record the reflection
            reflection = {
                "timestamp": time.time(),
                "completed_objectives": [obj["objective"] for obj in recent_completed],
                "reflection": response.text,
                "type": "outcome_reflection"
            }
            
            self.decision_history.append(reflection)
            self.save_decisions()
            
            self.log_action("reflection", "Completed reflection on recent outcomes")
            
        except Exception as e:
            self.log_action("error", f"Error reflecting on outcomes: {str(e)}")
    
    def auto_expand_knowledge(self):
        """Automatically expand knowledge in related areas"""
        # Limit frequency of expansion
        if random.random() > 0.3:  # Only run 30% of the time
            return
            
        if not self.knowledge_gained:
            return
            
        try:
            # Select a random topic from knowledge base
            topics = list(self.knowledge_gained.keys())
            base_topic = random.choice(topics)
            
            # Generate related topics
            expansion_prompt = f"""
            Based on the topic "{base_topic}", suggest 3 related but different topics that would complement this knowledge.
            These should be specific topics that expand the understanding in new directions.
            
            Format your response as a numbered list with no additional text.
            """
            
            response = agent_chat.send_message(expansion_prompt)
            
            # Extract topics
            related_topics = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() and line[1] in ['.', ')', ':']):
                    topic = line[2:].strip() if line[1] in [')', ':'] else line[3:].strip()
                    related_topics.append(topic)
            
            # Add one random related topic as objective
            if related_topics:
                selected_topic = random.choice(related_topics)
                self.add_objective(f"Learn about {selected_topic} and how it relates to {base_topic}")
                self.log_action("autonomous", f"Added related topic as objective: {selected_topic}")
                
                # Record decision
                decision = {
                    "timestamp": time.time(),
                    "base_topic": base_topic,
                    "expansion_topic": selected_topic,
                    "reasoning": f"Expanding knowledge from {base_topic} to related area {selected_topic}",
                    "type": "knowledge_expansion"
                }
                
                self.decision_history.append(decision)
                self.save_decisions()
                
        except Exception as e:
            self.log_action("error", f"Error expanding knowledge: {str(e)}")
    
    def make_autonomous_decision(self, context, options, decision_type):
        """Make an autonomous decision based on context and options"""
        try:
            # Format the decision prompt
            decision_prompt = f"""
            You need to make a decision based on the following context:
            
            CONTEXT:
            {context}
            
            OPTIONS:
            {options}
            
            You must select one option based on the context provided.
            Analyze the options and explain your reasoning step by step.
            Then provide your final decision.
            
            Format your response as:
            REASONING: [your step-by-step reasoning]
            DECISION: [selected option]
            CONFIDENCE: [a number between 0 and 1]
            """
            
            response = agent_chat.send_message(decision_prompt)
            
            # Parse the response
            reasoning = None
            decision = None
            confidence = 0.7  # Default confidence
            
            for line in response.text.split('\n'):
                if line.startswith('REASONING:'):
                    reasoning = line[len('REASONING:'):].strip()
                elif line.startswith('DECISION:'):
                    decision = line[len('DECISION:'):].strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line[len('CONFIDENCE:'):].strip())
                    except ValueError:
                        confidence = 0.7
            
            # Record the decision
            decision_record = {
                "timestamp": time.time(),
                "context": context,
                "options": options,
                "reasoning": reasoning or response.text,
                "decision": decision,
                "confidence": confidence,
                "type": decision_type
            }
            
            self.decision_history.append(decision_record)
            self.save_decisions()
            
            self.log_action("decision", f"Made {decision_type} decision: {decision}")
            
            return {
                "decision": decision,
                "reasoning": reasoning or response.text,
                "confidence": confidence
            }
            
        except Exception as e:
            self.log_action("error", f"Error making decision: {str(e)}")
            return {
                "decision": options.split('\n')[0] if '\n' in options else options,  # Default to first option
                "reasoning": f"Error occurred: {str(e)}",
                "confidence": 0.5
            }
    
    def pause_agent(self):
        """Pause the autonomous agent"""
        if self.agent_state != "active":
            return "Agent is not active"
            
        self.agent_state = "paused"
        self.log_action("system", "Agent paused")
        self.save_state()
        return "Agent paused"
    
    def process_next_objective(self):
        """Process the next objective in the queue"""
        if not self.objectives:
            return
            
        current_objective = self.objectives[0]
        self.log_action("process", f"Processing objective: {current_objective}")
        
        # Create a plan for the objective
        plan = self.create_plan(current_objective)
        if not plan:
            self.handle_objective_failure(current_objective, "Failed to create plan")
            return
            
        self.log_action("plan", f"Created plan with {len(plan)} steps")
        
        # Execute each step in the plan
        completion_summary = []
        success = True
        
        for step_idx, step in enumerate(plan):
            if self.agent_state != "active":
                self.log_action("system", "Agent no longer active, stopping objective processing")
                return
                
            self.log_action("step", f"Executing step {step_idx+1}/{len(plan)}: {step}")
            
            # Execute the step
            result = self.execute_step(step, current_objective)
            
            if result.get("success", False):
                completion_summary.append(f"Step {step_idx+1}: {result.get('summary', 'Completed')}")
                
                # Store any knowledge gained
                if "knowledge" in result:
                    topic = result.get("topic", current_objective)
                    self.knowledge_gained[topic] = result["knowledge"]
                    self.log_action("knowledge", f"Gained knowledge about {topic}")
            else:
                completion_summary.append(f"Step {step_idx+1}: Failed - {result.get('error', 'Unknown error')}")
                success = False
                break
        
        # Mark objective as completed or failed
        if success:
            self.completed_objectives.append({
                "objective": current_objective,
                "completed_at": datetime.datetime.now().isoformat(),
                "summary": "\n".join(completion_summary)
            })
            self.log_action("complete", f"Completed objective: {current_objective}")
        else:
            self.handle_objective_failure(current_objective, "\n".join(completion_summary))
            
        # Remove the objective from the queue
        self.objectives.pop(0)
        self.save_state()
    
    def create_plan(self, objective):
        """Create a plan to achieve the given objective"""
        try:
            prompt = f"""
            You are an autonomous research and learning agent. Your task is to create a detailed plan to achieve this learning objective:
            
            OBJECTIVE: {objective}
            
            Create a plan with 3-5 concrete steps that will help you learn about this topic effectively.
            Each step should be a specific action like "Research X concept", "Find authoritative sources about Y", etc.
            
            Return ONLY the steps as a numbered list with no additional text or explanation. 
            Each step should be short (10 words or less) and actionable.
            """
            
            response = agent_chat.send_message(prompt)
            
            # Parse steps from response
            steps = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                # Match lines that start with a number followed by a period
                if line and (line[0].isdigit() and len(line) > 2 and line[1] in ['.', ')', ':']):
                    step = line[2:].strip() if line[1] in [')', ':'] else line[3:].strip()
                    steps.append(step)
            
            # Limit to maximum steps
            return steps[:self.max_steps]
        except Exception as e:
            print(f"Error creating plan: {e}")
            traceback.print_exc()
            return []
    
    def execute_step(self, step, related_objective):
        """Execute a single step in the plan"""
        # Determine action type from step text
        step_lower = step.lower()
        
        try:
            if "research" in step_lower or "find" in step_lower or "search" in step_lower:
                return self.execute_research_step(step, related_objective)
            elif "learn" in step_lower or "understand" in step_lower or "study" in step_lower:
                return self.execute_learning_step(step, related_objective)
            elif "summarize" in step_lower or "analyze" in step_lower:
                return self.execute_analysis_step(step, related_objective)
            else:
                # Default to research for unrecognized step types
                return self.execute_research_step(step, related_objective)
        except Exception as e:
            print(f"Error executing step: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def execute_research_step(self, step, related_objective):
        """Execute a research step by searching for information"""
        try:
            # Extract search term from step
            search_term = self.extract_search_term(step, related_objective)
            
            if not search_term or len(search_term) < self.min_search_term_length:
                return {"success": False, "error": "Could not determine a valid search term"}
            
            self.log_action("search", f"Searching for: {search_term}")
            
            # Perform web search
            search_results = self.perform_search(search_term)
            
            if not search_results or len(search_results) == 0:
                return {"success": False, "error": f"No search results found for {search_term}"}
            
            # Analyze and synthesize results
            synthesis_prompt = f"""
            You are learning about "{related_objective}". Based on these search results about "{search_term}":
            
            {search_results}
            
            Synthesize the most important information that helps address the objective.
            Focus on factual information, key concepts, and significant insights.
            Format your response as a clear and concise summary of the gathered knowledge.
            """
            
            synthesis_response = agent_chat.send_message(synthesis_prompt)
            
            return {
                "success": True,
                "summary": f"Researched {search_term}",
                "topic": search_term,
                "knowledge": synthesis_response.text
            }
        except Exception as e:
            print(f"Error in research step: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def execute_learning_step(self, step, related_objective):
        """Execute a learning step by studying existing knowledge"""
        try:
            # Try to determine what to learn about
            topic = self.extract_search_term(step, related_objective)
            
            relevant_knowledge = ""
            
            # Check if we already have knowledge on this topic
            for existing_topic, knowledge in self.knowledge_gained.items():
                if topic.lower() in existing_topic.lower() or existing_topic.lower() in topic.lower():
                    relevant_knowledge += f"Knowledge about {existing_topic}:\n{knowledge}\n\n"
            
            # If no existing knowledge, do a quick search
            if not relevant_knowledge:
                search_results = self.perform_search(topic)
                if search_results:
                    relevant_knowledge = search_results
            
            # Learn from the knowledge
            learning_prompt = f"""
            You need to learn about "{topic}" as part of the objective: "{related_objective}".
            
            Available information:
            {relevant_knowledge}
            
            Your task:
            1. Identify the key concepts you need to understand
            2. Organize this information into a structured format
            3. Create a concise summary of what you've learned
            
            Format this as a clear learning summary that could be used to teach others.
            """
            
            learning_response = agent_chat.send_message(learning_prompt)
            
            return {
                "success": True,
                "summary": f"Learned about {topic}",
                "topic": topic,
                "knowledge": learning_response.text
            }
        except Exception as e:
            print(f"Error in learning step: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def execute_analysis_step(self, step, related_objective):
        """Execute an analysis step by synthesizing and analyzing information"""
        try:
            # Gather all relevant knowledge
            relevant_knowledge = []
            for topic, knowledge in self.knowledge_gained.items():
                # Check if topic is related to the objective
                if any(word in topic.lower() for word in related_objective.lower().split()):
                    relevant_knowledge.append(f"Knowledge about {topic}:\n{knowledge}")
            
            relevant_knowledge_str = "\n\n".join(relevant_knowledge)
            
            if not relevant_knowledge_str:
                # If no relevant knowledge, try to find some
                search_results = self.perform_search(related_objective)
                if search_results:
                    relevant_knowledge_str = search_results
            
            # Analyze the knowledge
            analysis_prompt = f"""
            You need to analyze information related to: "{related_objective}".
            
            Available information:
            {relevant_knowledge_str}
            
            Your task:
            1. Identify patterns, connections, and key insights from this information
            2. Analyze gaps in the current understanding
            3. Synthesize the most important learnings
            
            Provide a thoughtful analysis that goes beyond summarizing, offering deeper insights.
            """
            
            analysis_response = agent_chat.send_message(analysis_prompt)
            
            return {
                "success": True,
                "summary": f"Analyzed information about {related_objective}",
                "topic": f"Analysis of {related_objective}",
                "knowledge": analysis_response.text
            }
        except Exception as e:
            print(f"Error in analysis step: {e}")
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def extract_search_term(self, step, context):
        """Extract a search term from a step description"""
        try:
            prompt = f"""
            Extract the main search term from this task: "{step}"
            Context: This is part of learning about "{context}"
            
            Return ONLY the search term, with no additional text or explanation. Make it specific and focused.
            """
            
            response = agent_chat.send_message(prompt)
            search_term = response.text.strip()
            
            # Remove quotes if present
            if search_term.startswith('"') and search_term.endswith('"'):
                search_term = search_term[1:-1]
            
            return search_term
        except Exception as e:
            print(f"Error extracting search term: {e}")
            return context  # Fallback to the context
    
    def perform_search(self, query):
        """Perform a web search and return the results"""
        try:
            # Use SerpAPI if available
            api_key = os.environ.get('SERPAPI_KEY', "f41082ce8546f83f717679baf1318d649d123ba213a92067de9dfdee2ea5accb")
            
            params = {
                "engine": "google",
                "q": query,
                "api_key": api_key,
                "num": self.max_search_results
            }
            
            response = requests.get("https://serpapi.com/search", params=params)
            
            if response.status_code != 200:
                raise Exception(f"Search API returned status code {response.status_code}")
            
            data = response.json()
            
            # Extract and format organic results
            results = []
            for result in data.get("organic_results", [])[:self.max_search_results]:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                
                results.append(f"Title: {title}\nSnippet: {snippet}\nURL: {link}\n")
            
            return "\n".join(results)
        except Exception as e:
            print(f"Error performing search: {e}")
            traceback.print_exc()
            
            # Fallback to a more basic search approach if SerpAPI fails
            try:
                # Simple scraping approach as fallback (for educational purposes)
                search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                
                response = requests.get(search_url, headers=headers)
                
                if response.status_code != 200:
                    return ""
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract search results
                results = []
                for result in soup.select("div.g")[:self.max_search_results]:
                    title_elem = result.select_one("h3")
                    snippet_elem = result.select_one("div.IsZvec")
                    
                    title = title_elem.text if title_elem else "No title"
                    snippet = snippet_elem.text if snippet_elem else "No snippet"
                    
                    results.append(f"Title: {title}\nSnippet: {snippet}\n")
                
                return "\n".join(results)
            except Exception as e2:
                print(f"Error in fallback search: {e2}")
                return ""
    
    def handle_objective_failure(self, objective, reason):
        """Handle a failed objective"""
        self.log_action("failure", f"Failed objective: {objective}. Reason: {reason}")
        
        # Add to completed with failure status
        self.completed_objectives.append({
            "objective": objective,
            "completed_at": datetime.datetime.now().isoformat(),
            "status": "failed",
            "reason": reason
        })
    
    def generate_new_objectives(self, base_topic, count=3):
        """Generate new learning objectives based on a topic"""
        try:
            prompt = f"""
            Based on the topic "{base_topic}", generate {count} specific learning objectives that would expand knowledge in this area.
            Each objective should be focused, specific, and achievable through online research.
            
            Format your response as a numbered list with no additional text. Each objective should be a complete sentence.
            """
            
            response = agent_chat.send_message(prompt)
            
            # Parse objectives from response
            objectives = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                # Match lines that start with a number followed by a period
                if line and (line[0].isdigit() and len(line) > 2 and line[1] in ['.', ')', ':']):
                    objective = line[2:].strip() if line[1] in [')', ':'] else line[3:].strip()
                    objectives.append(objective)
            
            # Add the new objectives
            added_count = 0
            for objective in objectives:
                if self.add_objective(objective):
                    added_count += 1
                    
            self.log_action("generate", f"Generated {added_count} new objectives from {base_topic}")
            return objectives
        except Exception as e:
            print(f"Error generating new objectives: {e}")
            traceback.print_exc()
            return []
    
    def export_knowledge(self, format="markdown"):
        """Export all gained knowledge in the specified format"""
        try:
            if format == "markdown":
                output = "# Autonomous Agent Knowledge Base\n\n"
                output += f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                
                # Add completed objectives
                output += "## Completed Learning Objectives\n\n"
                for obj in self.completed_objectives:
                    status = obj.get("status", "completed")
                    completion_time = obj.get("completed_at", "").split("T")[0]  # Just get the date part
                    output += f"- **{obj['objective']}** ({status} on {completion_time})\n"
                
                # Add knowledge by topic
                output += "\n## Knowledge Base\n\n"
                for topic, knowledge in self.knowledge_gained.items():
                    output += f"### {topic}\n\n{knowledge}\n\n"
                
                # Save to file
                with open("agent_knowledge.md", "w") as f:
                    f.write(output)
                
                return {
                    "success": True,
                    "path": "agent_knowledge.md",
                    "format": "markdown"
                }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported export format: {format}"
                }
        except Exception as e:
            print(f"Error exporting knowledge: {e}")
            return {"success": False, "error": str(e)}
    
    def log_action(self, action_type, description):
        """Log an agent action"""
        timestamp = datetime.datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "type": action_type,
            "description": description
        }
        
        self.action_history.append(log_entry)
        print(f"[{action_type.upper()}] {description}")
        
        # Keep log size manageable
        if len(self.action_history) > 100:
            self.action_history = self.action_history[-100:]

# Create singleton instance
autonomous_agent = AutonomousAgent()
