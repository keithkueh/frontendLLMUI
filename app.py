# app.py
import chainlit as cl
import re
from health_agents import process_lab_report_query, process_general_query, consolidate_responses

# Function to detect if query is about lab reports
def is_lab_report_query(query):
    """Determine if a query is related to lab reports based on keywords"""
    lab_keywords = [
        'lab', 'test', 'result', 'blood', 'urine', 'cholesterol', 'glucose', 
        'hemoglobin', 'wbc', 'rbc', 'platelet', 'creatinine', 'bilirubin',
        'albumin', 'protein', 'sodium', 'potassium', 'calcium', 'magnesium',
        'chloride', 'bicarbonate', 'phosphate', 'triglycerides', 'hdl', 'ldl',
        'a1c', 'hba1c', 'tsh', 'alt', 'ast', 'alp', 'ggt', 'inr', 'ptt', 'pt'
    ]
    
    # Check if any lab keywords are in the query
    for keyword in lab_keywords:
        if re.search(r'\b' + keyword + r'\b', query.lower()):
            return True
    
    return False

@cl.on_message
async def main(message: cl.Message):
    """Process incoming messages and route to appropriate agents"""
    query = message.content
    
    # Check for conversation reset command
    if query.lower() in ["reset", "start over", "new conversation"]:
        cl.user_session.set("conversation_history", [])
        await cl.Message(content="I've reset our conversation. How can I help you with your health questions?", author="Health Assistant").send()
        return
    
    # Retrieve conversation history or initialize if not exists
    conversation_history = cl.user_session.get("conversation_history", [])
    
    # Add user message to history
    conversation_history.append({"role": "user", "content": query})
    
    # Send a thinking message
    thinking_msg = cl.Message(content="Give me a few seconds to think......", author="Health Assistant")
    await thinking_msg.send()
    
    try:
        # Process with appropriate agent based on query content
        is_lab_query = is_lab_report_query(query)
        
        # Get lab report response with conversation history
        lab_response = process_lab_report_query(query, conversation_history) if is_lab_query else "No lab report information requested."
        
        # Get general health response with conversation history
        general_response = process_general_query(query, conversation_history) if not is_lab_query else "Focus is on lab results for this query."
        
        # Consolidate responses
        final_response = consolidate_responses(lab_response, general_response, query, conversation_history)
        
        # Add assistant response to history
        conversation_history.append({"role": "assistant", "content": final_response})
        
        # Update conversation history in session
        cl.user_session.set("conversation_history", conversation_history)
        
        # Create a new message with the final response
        response_msg = cl.Message(content=final_response, author="Health Assistant")
        await response_msg.send()
        await thinking_msg.remove()
        
    except Exception as e:
        # Handle errors by creating a new message
        error_msg = cl.Message(content=f"I encountered an error while processing your question: {str(e)}", author="Health Assistant")
        await error_msg.send()
        await thinking_msg.remove()


@cl.on_chat_start
async def start():
    """Initialize the chat with a welcome message"""
    # Initialize an empty conversation history
    cl.user_session.set("conversation_history", [])
    
    welcome_message = """Welcome to the Medicia AI Health Assistant! 
        
Let me answer your lab results.

Regarding lab result questions, please be more specific on what you are asking about.

You can type "reset" at any time to start a new conversation.

How can I assist you today?"""
    
    await cl.Message(content=welcome_message, author="Health Assistant").send()
