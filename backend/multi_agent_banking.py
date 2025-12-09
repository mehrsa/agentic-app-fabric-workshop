from typing import Annotated, TypedDict, List
from langchain_core.messages import  BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
# from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
import json
import traceback

# Import existing banking infrastructure
from banking_app import (
    ai_client, get_user_accounts, create_new_account,
    transfer_money, get_transactions_summary, search_support_documents, db
)


from tools.database_query import query_database
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
def create_visualization_agent(user_id: str):
    """Agent specialized in creating and managing AI widgets/visualizations."""
    llm = create_banking_llm()
    
    # Import widget dependencies
    from ai_widget_model import create_widget, update_widget, delete_widget, get_widget_by_id, get_user_widgets
    from widget_queries import execute_widget_query
    
    @tool
    def create_ai_widget_tool(
        title: str,
        description: str = "",
        widget_type: str = "chart",
        chart_type: str = "bar",
        x_axis: str = "name",
        y_axis: str = "value",
        data: list = None,
        colors: list = None,
        data_mode: str = "static",
        query_type: str = None,
        time_range: str = "last_6_months"
    ) -> str:
        """
        Creates a new AI widget/chart in the user's AI Module dashboard.
        Use this tool when the user asks to create a chart, visualization, graph, or custom analytics view.
        
        Args:
            title: Title for the widget (e.g., "Monthly Spending by Category")
            description: Description of what the widget shows
            widget_type: Type of widget - 'chart', 'table', 'metric', or 'custom'
            chart_type: For charts - use one of: 'line', 'bar', 'pie', 'area'
            x_axis: The data key to use for X axis labels (default: 'name')
            y_axis: The data key to use for Y axis values (default: 'value')
            data: Array of data objects for the chart (for STATIC widgets only)
            colors: Optional array of hex color codes like ["#3B82F6", "#10B981", "#F59E0B"]
            data_mode: Either 'static' (data won't change) or 'dynamic' (data refreshes from database)
            query_type: For DYNAMIC widgets only. One of:
                - 'spending_by_category': Spending grouped by category (pie/bar charts)
                - 'monthly_trend': Monthly spending over time (line/area charts)
                - 'monthly_income_expenses': Income vs expenses comparison (line/bar charts)
                - 'account_balances': Current account balances (pie/bar charts)
                - 'top_merchants': Top spending by merchant (bar charts)
                - 'category_trend': Category spending over time (line charts with multiple series)
            time_range: For DYNAMIC widgets. One of:
                - 'last_6_months', 'last_3_months', 'last_12_months'
                - 'this_year', 'this_month', 'last_30_days', 'last_7_days', 'all_time'
        
        IMPORTANT GUIDANCE:
        - Use data_mode='dynamic' when the user wants data that updates/refreshes (e.g., "last 6 months", 
          "current balances", "recent spending"). These widgets show a refresh button.
        - Use data_mode='static' when creating one-time visualizations or when using data not from the 
          database (e.g., custom comparisons, educational charts, manually entered data).
        - For dynamic widgets, DO NOT provide the 'data' parameter - it will be fetched automatically.
        - For static widgets, you MUST provide the 'data' parameter with actual values.
        
        Returns:
            JSON string with status and widget_id if successful
        """
        try:
            config = {
                "chartType": chart_type,
                "xAxis": x_axis,
                "yAxis": y_axis,
                "customProps": {
                    "data": []
                }
            }
            
            if colors:
                config["colors"] = colors
            
            query_config = None
            
            if data_mode == 'dynamic' and query_type:
                # Build query config for dynamic widgets
                query_config = {
                    "query_type": query_type,
                    "time_range": time_range,
                    "filters": {}
                }
                
                # Execute query immediately to populate initial data
                try:
                    initial_data = execute_widget_query(query_config, user_id, db.session)
                    config["customProps"]["data"] = initial_data
                except Exception as e:
                    print(f"[widget] Error fetching initial data: {e}")
                    config["customProps"]["data"] = []
                    
            elif data:
                # Static widget with provided data
                config["customProps"]["data"] = data
            
            widget = create_widget(
                user_id=user_id,
                title=title,
                description=description,
                widget_type=widget_type,
                config=config,
                code=None,
                data_mode=data_mode,
                query_config=query_config
            )
            
            mode_msg = "dynamic (refreshable)" if data_mode == "dynamic" else "static"
            return json.dumps({
                "status": "success",
                "message": f"Successfully created {mode_msg} widget '{title}'. The user can view it in their AI Module tab.",
                "widget_id": widget['id'],
                "data_mode": data_mode
            })
            
        except Exception as e:
            traceback.print_exc()
            return json.dumps({
                "status": "error",
                "message": f"Failed to create widget: {str(e)}"
            })
    
    @tool
    def update_ai_widget_tool(
        widget_id: str,
        title: str = None,
        description: str = None,
        chart_type: str = None,
        colors: list = None,
        data_mode: str = None,
        query_type: str = None,
        time_range: str = None
    ) -> str:
        """
        Updates an existing AI widget in the user's AI Module dashboard.
        Use this tool when the user wants to modify an existing chart/widget.
        
        Args:
            widget_id: The ID of the widget to update (REQUIRED)
            title: New title for the widget (optional)
            description: New description (optional)
            chart_type: New chart type - 'line', 'bar', 'pie', 'area' (optional)
            colors: New color array like ["#3B82F6", "#10B981"] (optional)
            data_mode: Change to 'static' or 'dynamic' (optional)
            query_type: For dynamic widgets, change query type (optional)
            time_range: For dynamic widgets, change time range (optional)
        
        Returns:
            JSON string with status and updated widget info
        """
        try:
            # Get the existing widget
            existing = get_widget_by_id(widget_id, user_id)
            if not existing:
                return json.dumps({
                    "status": "error",
                    "message": f"Widget with ID '{widget_id}' not found or you don't have access to it."
                })
            
            # Build updates dict
            updates = {}
            
            if title is not None:
                updates['title'] = title
                
            if description is not None:
                updates['description'] = description
            
            # Handle config updates
            config = existing.get('config', {})
            config_changed = False
            
            if chart_type is not None:
                config['chartType'] = chart_type
                config_changed = True
                
            if colors is not None:
                config['colors'] = colors
                config_changed = True
            
            if config_changed:
                updates['config'] = config
            
            # Handle data mode change
            if data_mode is not None:
                updates['data_mode'] = data_mode
            
            # Handle query config updates for dynamic widgets
            if query_type is not None or time_range is not None:
                query_config = existing.get('query_config') or {}
                if query_type is not None:
                    query_config['query_type'] = query_type
                if time_range is not None:
                    query_config['time_range'] = time_range
                if 'filters' not in query_config:
                    query_config['filters'] = {}
                updates['query_config'] = query_config
                
                # If changing to dynamic or updating query, refresh data
                if data_mode == 'dynamic' or existing.get('data_mode') == 'dynamic':
                    try:
                        fresh_data = execute_widget_query(query_config, user_id, db.session)
                        if 'config' not in updates:
                            updates['config'] = config
                        if 'customProps' not in updates['config']:
                            updates['config']['customProps'] = {}
                        updates['config']['customProps']['data'] = fresh_data
                    except Exception as e:
                        print(f"[widget] Error refreshing data during update: {e}")
            
            if not updates:
                return json.dumps({
                    "status": "success",
                    "message": "No changes specified. Widget remains unchanged.",
                    "widget_id": widget_id
                })
            
            # Apply updates
            updated_widget = update_widget(widget_id, user_id, updates)
            
            if not updated_widget:
                return json.dumps({
                    "status": "error",
                    "message": "Failed to update widget."
                })
            
            return json.dumps({
                "status": "success",
                "message": f"Successfully updated widget '{updated_widget.get('title', widget_id)}'.",
                "widget_id": widget_id,
                "updated_fields": list(updates.keys())
            })
            
        except Exception as e:
            traceback.print_exc()
            return json.dumps({
                "status": "error",
                "message": f"Failed to update widget: {str(e)}"
            })
    
    @tool
    def create_simulation_widget_tool(
        title: str,
        description: str = "",
        simulation_type: str = "loan_repayment",
        defaults: dict = None
    ) -> str:
        """
        Creates an interactive simulation/What-If widget in the user's AI Module dashboard.
        Use this tool when the user wants to create financial planning calculators or simulators.
        
        These widgets have sliders and inputs that users can adjust to see projections change in real-time.
        
        Args:
            title: Title for the widget (e.g., "Mortgage Payoff Calculator")
            description: Description of what the simulator does
            simulation_type: Type of simulation. Must be one of:
                - 'loan_repayment': Loan/mortgage payoff calculator with extra payment analysis
                - 'savings_projector': Compound interest savings calculator  
                - 'budget_planner': Interactive budget allocation planner
                - 'retirement_calculator': Retirement savings projector
                - 'emergency_fund': Emergency fund goal tracker
            defaults: Optional dictionary of default values for sliders
        
        Returns:
            JSON string with status and widget_id if successful
        """
        try:
            # Validate simulation type
            valid_types = ['loan_repayment', 'savings_projector', 'budget_planner', 'retirement_calculator', 'emergency_fund']
            if simulation_type not in valid_types:
                return json.dumps({
                    "status": "error",
                    "message": f"Invalid simulation_type. Must be one of: {', '.join(valid_types)}"
                })
            
            # Build simulation config
            simulation_config = {
                "simulation_type": simulation_type,
                "defaults": defaults or {}
            }
            
            # Empty config for simulation widgets
            config = {
                "chartType": "simulation",
                "customProps": {}
            }
            
            widget = create_widget(
                user_id=user_id,
                title=title,
                description=description,
                widget_type="simulation",
                config=config,
                code=None,
                data_mode="static",
                query_config=None,
                simulation_config=simulation_config
            )
            
            type_descriptions = {
                'loan_repayment': 'loan/mortgage payoff calculator',
                'savings_projector': 'compound interest savings projector',
                'budget_planner': 'interactive budget allocation planner',
                'retirement_calculator': 'retirement savings projector',
                'emergency_fund': 'emergency fund goal tracker'
            }
            
            return json.dumps({
                "status": "success",
                "message": f"Successfully created an interactive {type_descriptions.get(simulation_type, simulation_type)} widget called '{title}'.",
                "widget_id": widget['id'],
                "widget_type": "simulation",
                "simulation_type": simulation_type
            })
            
        except Exception as e:
            traceback.print_exc()
            return json.dumps({
                "status": "error",
                "message": f"Failed to create simulation widget: {str(e)}"
            })
    
    @tool
    def list_user_widgets_tool() -> str:
        """
        Lists all AI widgets created by the current user.
        Use this when the user asks to see their widgets or visualizations.
        
        Returns:
            JSON string with list of widgets
        """
        try:
            widgets = get_user_widgets(user_id)
            
            if not widgets:
                return json.dumps({
                    "status": "success",
                    "message": "You don't have any widgets yet.",
                    "widgets": []
                })
            
            widget_summary = []
            for w in widgets:
                widget_summary.append({
                    "id": w['id'],
                    "title": w['title'],
                    "type": w['widget_type'],
                    "data_mode": w.get('data_mode', 'static'),
                    "created_at": w.get('created_at')
                })
            
            return json.dumps({
                "status": "success",
                "message": f"You have {len(widgets)} widget(s).",
                "widgets": widget_summary
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to list widgets: {str(e)}"
            })
    
    @tool
    def delete_widget_tool(widget_id: str) -> str:
        """
        Deletes an AI widget from the user's dashboard.
        Use this when the user wants to remove a widget.
        
        Args:
            widget_id: The ID of the widget to delete
        
        Returns:
            JSON string with status
        """
        try:
            success = delete_widget(widget_id, user_id)
            
            if not success:
                return json.dumps({
                    "status": "error",
                    "message": f"Widget '{widget_id}' not found or you don't have access to it."
                })
            
            return json.dumps({
                "status": "success",
                "message": f"Successfully deleted widget '{widget_id}'."
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to delete widget: {str(e)}"
            })
    
    tools = [
        create_ai_widget_tool,
        update_ai_widget_tool,
        create_simulation_widget_tool,
        list_user_widgets_tool,
        delete_widget_tool
    ]
    
    system_prompt = f"""You are an AI visualization specialist helping user_id: {user_id}.

## CRITICAL RULES ##
1. **COMPLETE ANSWERS ONLY**: Provide full answer in FIRST response.
2. **USE TOOLS IMMEDIATELY**: Call tools without announcing.
3. **USER OWNERSHIP**: All widgets are user-specific. Only this user can see/edit their widgets.

## Your Capabilities ##
You help users create, update, and manage AI-powered visualizations and calculators:

### 1. Data Visualizations (Charts)
- **Static Charts**: One-time visualizations with fixed data
- **Dynamic Charts**: Auto-refreshing charts that pull live data from the database
- Supported types: bar, line, pie, area charts

### 2. Interactive Simulators
- Loan/mortgage calculators
- Savings projectors
- Budget planners
- Retirement calculators
- Emergency fund trackers

## When to Use DYNAMIC vs STATIC ##

✅ Use **data_mode='dynamic'** when:
- User wants "current", "latest", or "recent" data
- Time-based queries: "last 6 months", "this year", "monthly trend"
- Data that should refresh: account balances, spending categories
- Query types: spending_by_category, monthly_trend, account_balances, etc.

✅ Use **data_mode='static'** when:
- User provides specific data points
- Creating comparison charts with custom data
- Educational/example visualizations
- Simulation widgets (always static)

## Tool Selection Guide ##

📊 **create_ai_widget_tool**: Creating new data visualizations
- Example: "Create a pie chart of my spending by category"
- Example: "Show me a line chart of monthly spending trends"

🔄 **update_ai_widget_tool**: Modifying existing widgets
- Example: "Change that chart to a bar chart"
- Example: "Update the widget to show last 3 months instead"

🧮 **create_simulation_widget_tool**: Creating interactive calculators
- Example: "Create a loan calculator"
- Example: "I want a retirement savings projector"

📋 **list_user_widgets_tool**: Showing user's widgets
- Example: "What widgets do I have?"
- Example: "Show me my visualizations"

🗑️ **delete_widget_tool**: Removing widgets
- Example: "Delete that spending chart"

## Response Format ##
- Be conversational and helpful
- After creating a widget, tell the user they can view it in the "AI Module" tab
- For dynamic widgets, mention they can click refresh to update data
- For simulators, explain they can adjust the sliders

## Common Patterns ##

User: "Create a chart showing my spending by category for the last 6 months"
→ Use create_ai_widget_tool with data_mode='dynamic', query_type='spending_by_category', time_range='last_6_months'

User: "Make a loan calculator"
→ Use create_simulation_widget_tool with simulation_type='loan_repayment'

User: "Change that chart to a pie chart"
→ Use update_ai_widget_tool with chart_type='pie'
"""
    
    return create_react_agent(
        llm,
        tools,
        prompt=system_prompt,
        checkpointer=MemorySaver()
    )
# Specialized Banking Agents
def create_support_agent():
    """Agent specialized in customer support operations."""
    llm = create_banking_llm()
    
    tools = [search_support_documents]
    
    system_prompt = """You are a customer support agent that provides immediate, complete answers.

                    ## CRITICAL RULES ##
                    1. **ANSWER IMMEDIATELY**: Use the knowledge base tool and provide the complete answer in ONE response.
                    2. **NO STATUS UPDATES**: Don't say "I'm searching..." or "Let me look that up..."
                    3. **DIRECT RESPONSES**: Call the tool, get results, and answer the question fully.

                    ## Your Capabilities ##
                    - Search knowledge base using `search_support_documents` tool
                    - Answer questions about policies, procedures, and general banking topics
                    - Provide troubleshooting guidance

                    ## Response Format ##
                    - Be helpful and professional
                    - Give complete, accurate information
                    - If multiple steps are needed, provide all steps at once
                    - Include relevant details from the knowledge base

                    REMEMBER: Answer the user's question COMPLETELY in your FIRST response."""

    return create_react_agent(
        llm, 
        tools, 
        prompt=system_prompt,
        checkpointer=MemorySaver()
    )
def create_account_management_agent(user_id: str):
    """Agent specialized in account management operations."""
    llm = create_banking_llm()
    
    @tool
    def get_user_accounts_tool() -> str:
        """Retrieves all accounts for the current user."""
        return get_user_accounts(user_id=user_id)
    
    @tool
    def create_new_account_tool(account_type: str = 'checking', name: str = None, balance: float = 0.0) -> str:
        """Creates a new bank account for the current user."""
        return create_new_account(user_id=user_id, account_type=account_type, name=name, balance=balance)
    
    @tool
    def transfer_money_tool(from_account_name: str = None, to_account_name: str = None, amount: float = 0.0, to_external_details: dict = None) -> str:
        """Transfers money between the current user's accounts or to an external account."""
        return transfer_money(user_id=user_id, from_account_name=from_account_name, to_account_name=to_account_name, amount=amount, to_external_details=to_external_details)
    
    @tool
    def get_transactions_summary_tool(time_period: str = 'this year', account_name: str = None) -> str:
        """Provides a categorical summary of the current user's spending for general periods."""
        return get_transactions_summary(user_id=user_id, time_period=time_period, account_name=account_name)
    
    tools = [get_user_accounts_tool, create_new_account_tool,
             transfer_money_tool, get_transactions_summary_tool,
             query_database]
    
    system_prompt=f"""
            You are a customer support agent for a banking application.
            
            **IMPORTANT: You are currently helping user_id: {user_id}**
            All operations must be performed for this user only.
            
            You have access to the following capabilities:
            1. Standard banking operations (get_user_accounts_tool, get_transactions_summary_tool, transfer_money_tool, create_new_account_tool)
            2. Direct database queries (query_database)
            
            ## How to Answer Questions ##
            - For simple requests like "what are my accounts?" or "what's my spending summary?", use the standard banking tools.
            - **'get_transactions_summary_tool' Tool**: Use this ONLY for general categorical summaries (e.g., "What's my spending summary this month?"). It CANNOT handle specific dates or lists.
            - **'query_database' Tool**: Use this for ALL other data questions. This is your default tool for anything specific.
                - "Show me my last 5 transactions" -> `query_database`
                - "How many savings accounts do I have?" -> `query_database`
                - "What has been my expense in 2025?" -> `query_database`
                - "How much did I spend at Starbucks?" -> `query_database`
            - When using 'query_database', you must first use the 'describe' action to see the table structure.
                - If no accounts specified, assume all accounts for the user.
                - if no categories specified, include all categories. If categories specified, filter by those categories.
                - if no time period specified, retrieve last 12 months of data for the user.
            
            ## Database Rules ##
            - You must only access data for the user_id '{user_id}'.
            - **CRITICAL SQL FIX:** The 'datetimeoffset' column type (like 'created_at') will fail. You **MUST** 'CAST' it to a string in all SELECT or ORDER BY clauses (e.g., 'CAST(created_at AS VARCHAR(30)) AS created_at_str').
            
            ## Response Formatting ##
            - **Be concise.** Do not explain your internal process (e.g., "I described the tables...").
            - **Present results directly.**
            - When a user asks for a list of transactions, format the final answer (after all tool calls are done) as a clean bulleted list.
            - **Example of a good response:**
            "Here are your last 5 transactions:
            - [Date] - $[Amount] - [Description] - [Category] - [Status]
            - [Date] - $[Amount] - [Description] - [Category] - [Status]"
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
    
    routing_prompt = """You are a routing coordinator. Analyze the request and respond with ONLY the agent name.

    ## Routing Rules ##
    - Account/money/transaction/balance/spending/transfer queries → respond: "account_agent"
    - Help/policy/general questions/support → respond: "support_agent"
    - Visualization/chart/widget/simulation → respond: "visualization_agent"


    ## Output Format ##
    Respond with ONLY: "account_agent" or "support_agent" or "visualization_agent"
    Do NOT add any other text, explanation, or formatting."""
    
    return create_react_agent(
        llm, 
        [], 
        prompt=routing_prompt,
        checkpointer=MemorySaver()
    )

# Multi-Agent Node Functions

def coordinator_node(state: BankingAgentState):
    """Route customer requests to appropriate specialist agent."""
    messages = state["messages"]
    last_message = messages[-1].content if messages else ""
    
    # Use keyword-based routing for speed and reliability
    message_lower = last_message.lower()

        # Visualization keywords
    visualization_keywords = [
        "widget", "chart", "graph", "visualization", "visualize", "plot",
        "create chart", "show chart", "make chart", "pie chart", "bar chart",
        "line chart", "area chart", "dashboard", "calculator", "simulator",
        "simulation", "loan calculator", "savings calculator", "budget planner",
        "what-if", "projection", "ai module", "delete widget", "update widget",
        "change chart", "my widgets", "list widgets"
    ]
    
    # Account-related keywords
    account_keywords = [
        "account", "balance", "transaction", "transfer", "payment", 
        "spending", "summary", "history", "money", "deposit", "withdraw",
        "credit", "debit", "checking", "savings", "expense", "income", "breakdown",
        "income", "statement", "funds", "pay", "send", "receive"
    ]
    
    if any(keyword in message_lower for keyword in visualization_keywords):
        state["current_agent"] = "visualization_agent"
        state["task_type"] = "visualization_management"
        print(f"[COORDINATOR] Routing to: visualization_agent")
    elif any(keyword in message_lower for keyword in account_keywords):
        state["current_agent"] = "account_agent"
        state["task_type"] = "account_management"
        print(f"[COORDINATOR] Routing to: account_agent")
    else:
        state["current_agent"] = "support_agent"
        state["task_type"] = "customer_support"
        print(f"[COORDINATOR] Routing to: support_agent")
    
    return state


def account_agent_node(state: BankingAgentState):
    """Handle account management tasks."""
    user_id = state["user_id"]  # Get user_id from state
    account_agent = create_account_management_agent(user_id)  # Pass user_id
    
    thread_config = {"configurable": {"thread_id": f"account_{state['session_id']}"}}
    
    response = account_agent.invoke({"messages": state["messages"]}, config=thread_config)
    
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

def visualization_agent_node(state: BankingAgentState):
    """Handle visualization/widget creation tasks."""
    user_id = state["user_id"]
    visualization_agent = create_visualization_agent(user_id)
    
    thread_config = {"configurable": {"thread_id": f"visualization_{state['session_id']}"}}
    
    response = visualization_agent.invoke({"messages": state["messages"]}, config=thread_config)
    
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
    workflow.add_node("support_agent", support_agent_node)
    workflow.add_node("visualization_agent", visualization_agent_node)

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
            "support_agent": "support_agent",
            "visualization_agent": "visualization_agent"
        }
    )
    
    # All agents end the workflow
    workflow.add_edge("account_agent", END)
    workflow.add_edge("support_agent", END)
    workflow.add_edge("visualization_agent", END)
    
    return workflow.compile(checkpointer=MemorySaver())
