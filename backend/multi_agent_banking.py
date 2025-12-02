from typing import Annotated, TypedDict, List
from langchain_core.messages import  BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

# Import existing banking infrastructure
from banking_app import (
ai_client, get_user_accounts, create_new_account,
transfer_money, get_transactions_summary, search_support_documents,
query_tool)

# Multi-Agent State
class BankingAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The messages in the conversation"]
    current_agent: str
    task_type: str
    user_id: str
    session_id: str
    final_result: str

# Create LLM
def create_banking_llm():
    return ai_client
# Specialized Banking Agents

def create_account_management_agent():
    """Agent specialized in account management operations."""
    llm = create_banking_llm()
    tools = [get_user_accounts, create_new_account]
    
    system_prompt = """You are an Account Management Agent for a banking system.
    
    Your responsibilities:
    1. Help customers view their accounts and account details
    2. Assist with creating new accounts (checking, savings, etc.)
    3. Provide account information and balances
    4. Handle account-related inquiries
    
    Always use the appropriate tools to get accurate, real-time account information.
    Be professional, secure, and helpful in all interactions.
    """
    
    return create_react_agent(
        llm, 
        tools, 
        prompt=system_prompt,
        checkpointer=MemorySaver()
    )

def create_transaction_agent():
    """Agent specialized in transaction operations."""
    llm = create_banking_llm()
    tools = [transfer_money, get_transactions_summary, query_tool]
    
    system_prompt = """You are a Transaction Agent for a banking system.
    
    Your responsibilities:
    1. Process money transfers between accounts
    2. Provide transaction summaries and spending analysis
    3. Help customers understand their transaction history
    4. Assist with payment-related inquiries
    
    Always verify account details and ensure sufficient funds before processing transfers.
    Be careful with financial transactions and provide clear confirmations.
    """
    
    return create_react_agent(
        llm, 
        tools, 
        prompt=system_prompt,
        checkpointer=MemorySaver()
    )

def create_support_agent():
    """Agent specialized in customer support."""
    llm = create_banking_llm()
    tools = [search_support_documents]
    
    system_prompt = """You are a Customer Support Agent for a banking system.
    
    Your responsibilities:
    1. Answer general banking questions using the knowledge base
    2. Provide information about banking policies and procedures
    3. Help customers with non-transactional inquiries
    4. Direct customers to appropriate specialists when needed
    
    Always search the support documents first to provide accurate information.
    Be helpful, empathetic, and professional in all customer interactions.
    """
    
    return create_react_agent(
        llm, 
        tools, 
        prompt=system_prompt,
        checkpointer=MemorySaver()
    )

def create_coordinator_agent():
    """Agent that routes customer requests to appropriate specialists."""
    llm = create_banking_llm()
    
    system_prompt = """You are a Banking Coordinator that routes customer requests to the right specialist.
    
    Route requests to:
    - account_agent: For account viewing, account creation, balance inquiries
    - transaction_agent: For money transfers, payment history, spending analysis
    - support_agent: For general questions, policies, troubleshooting
    
    Analyze the customer's request and respond with ONLY the agent name: 
    "account_agent", "transaction_agent", or "support_agent"
    """
    
    return create_react_agent(
        llm, 
        [], 
        prompt=system_prompt,
        checkpointer=MemorySaver()
    )

# Multi-Agent Node Functions

def coordinator_node(state: BankingAgentState):
    """Route customer requests to appropriate specialist agent."""
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    # Enhanced routing logic
    message_lower = last_message.lower()
    
    # Account-related keywords
    account_keywords = ["account", "balance", "create account", "new account", "checking", "savings", "accounts"]
    
    # Transaction-related keywords  
    transaction_keywords = ["transfer", "send money", "payment", "transaction", "spending", "summary", "history"]
    
    
    if any(keyword in message_lower for keyword in account_keywords):
        state["current_agent"] = "account_agent"
        state["task_type"] = "account_management"
    elif any(keyword in message_lower for keyword in transaction_keywords):
        state["current_agent"] = "transaction_agent"
        state["task_type"] = "transaction"
    else:
        state["current_agent"] = "support_agent"
        state["task_type"] = "support"
    
    return state

def account_agent_node(state: BankingAgentState):
    """Handle account management tasks."""
    account_agent = create_account_management_agent()
    
    thread_config = {"configurable": {"thread_id": f"account_{state['session_id']}"}}
    
    response = account_agent.invoke({"messages": state["messages"]}, config=thread_config)
    
    state["messages"] = response["messages"]
    state["final_result"] = response["messages"][-1].content
    
    return state

def transaction_agent_node(state: BankingAgentState):
    """Handle transaction-related tasks."""
    transaction_agent = create_transaction_agent()
    
    thread_config = {"configurable": {"thread_id": f"transaction_{state['session_id']}"}}
    
    response = transaction_agent.invoke({"messages": state["messages"]}, config=thread_config)
    
    state["messages"] = response["messages"]
    state["final_result"] = response["messages"][-1].content
    
    return state

def support_agent_node(state: BankingAgentState):
    """Handle customer support tasks."""
    support_agent = create_support_agent()
    
    thread_config = {"configurable": {"thread_id": f"support_{state['session_id']}"}}
    
    response = support_agent.invoke({"messages": state["messages"]}, config=thread_config)
    
    state["messages"] = response["messages"]
    state["final_result"] = response["messages"][-1].content
    
    return state

# Create Multi-Agent Banking System

def create_multi_agent_banking_system():
    """Create the multi-agent banking workflow."""
    
    workflow = StateGraph(BankingAgentState)
    
    # Add nodes
    workflow.add_node("coordinator", coordinator_node)
    workflow.add_node("account_agent", account_agent_node)
    workflow.add_node("transaction_agent", transaction_agent_node)
    workflow.add_node("support_agent", support_agent_node)
    
    # Set entry point
    workflow.set_entry_point("coordinator")
    
    # Add conditional routing
    def route_to_specialist(state: BankingAgentState):
        return state["current_agent"]
    
    workflow.add_conditional_edges(
        "coordinator",
        route_to_specialist,
        {
            "account_agent": "account_agent",
            "transaction_agent": "transaction_agent",
            "support_agent": "support_agent"
        }
    )
    
    # All agents end the workflow
    workflow.add_edge("account_agent", END)
    workflow.add_edge("transaction_agent", END)
    workflow.add_edge("support_agent", END)
    
    return workflow.compile(checkpointer=MemorySaver())
