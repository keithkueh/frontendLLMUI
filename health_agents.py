# health_agents.py
from agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool
from openai import AsyncOpenAI
from lab_processor import extract_lab_values
from pdf_processor import process_pdf, query_pdf_knowledge


import os
# Debug proxy settings
print("HTTP_PROXY:", os.environ.get("HTTP_PROXY"))
print("http_proxy:", os.environ.get("http_proxy"))
# Set no_proxy to avoid proxy issues
os.environ["no_proxy"] = "localhost,127.0.0.1,127.0.0.0"

# def create_llama_model(model_name="llama3.2"):
def create_llama_model(model_name="gemma3:12b"):
    """Create a model instance for the specified model"""
    return OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=AsyncOpenAI(
            base_url="http://127.0.0.1:11435/v1",
            api_key="ollama"  # Dummy API key
        )
    )

#def create_specialized_model(model_name="llama3.2"):
def create_specialized_model(model_name="gemma3:12b"):
    """Create a specialized model that can be swapped for BioMedLM later"""
    if model_name == "biomedlm":
        # Future implementation for Stanford BioMedLM
        return OpenAIChatCompletionsModel(
            model="biomedlm",
            openai_client=AsyncOpenAI(
                base_url="http://your-biomedlm-endpoint/v1",
                api_key="dummy_key"  # Replace with actual key when implementing
            )
        )
    else:
        # Default to Llama 3.2
        return OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=AsyncOpenAI(
                base_url="http://127.0.0.1:11435/v1",
                api_key="ollama"  # Dummy API key
            )
        )

# Lab Report Agent
lab_report_agent = Agent(
    name="Lab Report Specialist",
    instructions="""You are a medical AI assistant specialized in interpreting lab test reports.
    Focus only on explaining lab results, reference ranges, and their implications.
    Provide clear explanations of medical terminology.
    Always mention when a value is outside the normal range and what that might indicate.
    Use your advanced understanding of medical terminology to provide accurate interpretations.
    Do not provide medical advice or diagnosis, only factual information about the lab results.""",
    model=create_specialized_model(),
    tools=[extract_lab_values]
)

# General Health Agent
general_health_agent = Agent(
    name="General Health Assistant",
    instructions="""You are a general health information assistant.
    Answer questions about general health topics, but NOT about specific lab test results.
    Provide factual health information and general wellness tips.
    Do not interpret specific medical data or provide medical advice.
    If asked about lab results, politely redirect to the Lab Report Specialist.""",
    model=create_llama_model()
)

# Update the Consolidation Agent instructions
consolidation_agent = Agent(
    name="Health Information Coordinator",
    instructions="""You are a coordinator that combines and organizes information from the Lab Report Specialist and General Health Assistant.
    Your job is to present a clear, coherent summary of the information provided by both specialists.
    
    Important guidelines:
    1. DO NOT repeat detailed lab test analyses that have already been provided in previous responses.
    2. If lab results were already explained earlier, only briefly reference them or focus on new insights.
    3. For follow-up questions about previously discussed lab results, refer to your earlier explanation and only add new information.
    4. Organize information logically, starting with lab result interpretations (if new) followed by general health information.
    5. Highlight important points and ensure there are no contradictions between information sources.
    6. Use simple language appropriate for patients.
    7. Keep your responses concise and focused on answering the current question.""",
    model=create_llama_model()
)


# Update the Lab Report Agent to include PDF tools
lab_report_agent = Agent(
    name="Lab Report Specialist",
    instructions="""You are a medical AI assistant specialized in interpreting lab test reports.
    Focus only on explaining lab results, reference ranges, and their implications.
    Provide clear explanations of medical terminology.
    Always mention when a value is outside the normal range and what that might indicate.
    Do not provide medical advice or diagnosis, only factual information about the lab results.
    When available, use information from processed PDF documents to enhance your explanations.""",
    model=create_specialized_model()
    # tools=[extract_lab_values, process_pdf, query_pdf_knowledge]
)

# Add a function to track which lab tests have been explained
def track_explained_lab_tests(conversation_history):
    """Extract lab tests that have already been explained in the conversation"""
    explained_tests = set()
    
    for message in conversation_history:
        if message["role"] == "assistant":
            content = message["content"].lower()
            
            # Check for common patterns indicating lab test explanations
            for test in ['cholesterol', 'glucose', 'hemoglobin', 'wbc', 'rbc', 'platelet', 
                        'creatinine', 'bilirubin', 'albumin', 'protein', 'sodium', 'potassium',
                        'calcium', 'magnesium', 'chloride', 'bicarbonate', 'phosphate', 
                        'triglycerides', 'hdl', 'ldl', 'a1c', 'hba1c', 'tsh', 'alt', 'ast',
                        'alp', 'ggt', 'inr', 'ptt', 'pt']:
                if test in content and any(phrase in content for phrase in 
                                          ['normal range', 'reference range', 'your result', 
                                           'your level', 'your value', 'indicates', 'suggests']):
                    explained_tests.add(test)
    
    return explained_tests

def format_conversation_history(conversation_history):
    """Format the conversation history into a string"""
    if not conversation_history:
        return "No previous conversation."
    
    formatted = ""
    for message in conversation_history:
        role = "Patient" if message["role"] == "user" else "Assistant"
        formatted += f"{role}: {message['content']}\n\n"
    
    return formatted

def summarize_conversation(conversation_history):
    """Summarize the conversation history if it gets too long"""
    if len(conversation_history) <= 6:  # Keep recent conversations intact
        return conversation_history
    
    # Extract the most recent messages (last 4 exchanges)
    recent_messages = conversation_history[-4:]
    
    # Format older messages for summarization
    older_messages = conversation_history[:-4]
    formatted_older = format_conversation_history(older_messages)
    
    # Create a summarization prompt
    summarization_prompt = f"""
    Please summarize the following conversation between a patient and a health assistant.
    Focus on key medical information, lab results mentioned, and important questions asked:
    
    {formatted_older}
    """
    
    # Get the summary using the consolidation agent
    result = Runner.run_sync(consolidation_agent, summarization_prompt)
    summary = result.final_output
    
    # Return a new conversation history with the summary and recent messages
    return [{"role": "system", "content": f"Previous conversation summary: {summary}"}] + recent_messages

# Function to process lab report questions
def process_lab_report_query(query, conversation_history=None):
    """Process queries related to lab reports using the specialized agent"""
    if conversation_history is None:
        conversation_history = []
    
    # Check if conversation history is too long and needs summarization
    if len(conversation_history) > 6:
        conversation_history = summarize_conversation(conversation_history)
    
    # Format the conversation history for the model
    formatted_history = format_conversation_history(conversation_history)
    
    # Create a prompt that includes the conversation history
    prompt = f"""
    Previous conversation:
    {formatted_history}
    
    Current question: {query}
    
    Please provide information about the lab results mentioned, considering the context of our conversation.
    """
    
    result = Runner.run_sync(lab_report_agent, prompt)
    return result.final_output

# Function to process general health questions
def process_general_query(query, conversation_history=None):
    """Process general health queries using the general health agent"""
    if conversation_history is None:
        conversation_history = []
    
    # Check if conversation history is too long and needs summarization
    if len(conversation_history) > 6:
        conversation_history = summarize_conversation(conversation_history)
    
    # Format the conversation history for the model
    formatted_history = format_conversation_history(conversation_history)
    
    # Create a prompt that includes the conversation history
    prompt = f"""
    Previous conversation:
    {formatted_history}
    
    Current question: {query}
    
    Please provide general health information, considering the context of our conversation.
    """
    
    result = Runner.run_sync(general_health_agent, prompt)
    return result.final_output

# Update the consolidate_responses function
def consolidate_responses(lab_response, general_response, original_query, conversation_history=None):
    """Combine and organize responses from both agents"""
    if conversation_history is None:
        conversation_history = []
    
    # Format the conversation history for context
    formatted_history = format_conversation_history(conversation_history[-4:] if len(conversation_history) > 4 else conversation_history)
    
    # Track which lab tests have already been explained
    explained_tests = track_explained_lab_tests(conversation_history)
    explained_tests_str = ", ".join(explained_tests) if explained_tests else "None"
    
    prompt = f"""
    Previous conversation:
    {formatted_history}
    
    Original patient question: {original_query}
    
    Lab Report Specialist response:
    {lab_response}
    
    General Health Assistant response:
    {general_response}
    
    Lab tests already explained in previous responses: {explained_tests_str}
    
    Please provide a consolidated, well-organized response that combines these insights.
    Consider the context of our previous conversation when crafting your response.
    
    IMPORTANT: DO NOT repeat detailed explanations of lab tests that have already been explained in previous responses.
    If the patient is asking about a lab test that was already explained, briefly acknowledge it and focus on answering
    their new question or providing new information only.
    """
    
    result = Runner.run_sync(consolidation_agent, prompt)
    return result.final_output
