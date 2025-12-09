"""
Widget Query Executor - Executes dynamic queries for AI widgets
Supports various query types: spending_by_category, monthly_trend, account_balances, etc.
"""
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal


def execute_widget_query(query_config: dict, user_id: str, db_session) -> list:
    """
    Execute a widget query and return fresh data.
    
    query_config structure:
    {
        "query_type": "spending_by_category" | "monthly_trend" | "account_balances" | "custom_sql",
        "time_range": "last_6_months" | "this_year" | "this_month" | "all_time",
        "filters": {
            "account_id": "optional",
            "categories": ["optional", "list"],
            ...
        },
        "custom_sql": "SELECT ... (only for query_type='custom_sql')"
    }
    """
    query_type = query_config.get('query_type', 'spending_by_category')
    time_range = query_config.get('time_range', 'last_6_months')
    filters = query_config.get('filters', {})
    
    # Import models here to avoid circular imports
    from banking_app import Account, Transaction, db
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = calculate_start_date(time_range, end_date)
    
    if query_type == 'spending_by_category':
        return query_spending_by_category(user_id, start_date, end_date, filters, db_session)
    elif query_type == 'monthly_trend':
        return query_monthly_trend(user_id, start_date, end_date, filters, db_session)
    elif query_type == 'monthly_income_expenses':
        return query_monthly_income_expenses(user_id, start_date, end_date, filters, db_session)
    elif query_type == 'account_balances':
        return query_account_balances(user_id, filters, db_session)
    elif query_type == 'top_merchants':
        return query_top_merchants(user_id, start_date, end_date, filters, db_session)
    elif query_type == 'daily_spending':
        return query_daily_spending(user_id, start_date, end_date, filters, db_session)
    elif query_type == 'category_trend':
        return query_category_trend(user_id, start_date, end_date, filters, db_session)
    else:
        return []


def calculate_start_date(time_range: str, end_date: datetime) -> datetime:
    """Calculate start date based on time range string"""
    if time_range == 'last_6_months':
        return end_date - relativedelta(months=6)
    elif time_range == 'last_3_months':
        return end_date - relativedelta(months=3)
    elif time_range == 'last_12_months' or time_range == 'last_year':
        return end_date - relativedelta(months=12)
    elif time_range == 'this_year':
        return end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'this_month':
        return end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'last_30_days':
        return end_date - timedelta(days=30)
    elif time_range == 'last_7_days':
        return end_date - timedelta(days=7)
    elif time_range == 'all_time':
        return datetime(2000, 1, 1)  # Effectively all time
    else:
        # Default to last 6 months
        return end_date - relativedelta(months=6)


def get_user_account_ids(user_id: str, db_session, filters: dict = None):
    """Get account IDs for a user, optionally filtered"""
    from banking_app import Account
    
    query = db_session.query(Account.id).filter(Account.user_id == user_id)
    
    if filters and filters.get('account_id'):
        query = query.filter(Account.id == filters['account_id'])
    
    return [acc_id for (acc_id,) in query.all()]


def query_spending_by_category(user_id: str, start_date: datetime, end_date: datetime, 
                                filters: dict, db_session) -> list:
    """Query spending grouped by category"""
    from banking_app import Transaction, Account, db
    
    account_ids = get_user_account_ids(user_id, db_session, filters)
    if not account_ids:
        return []
    
    query = db_session.query(
        Transaction.category,
        db.func.sum(Transaction.amount).label('value')
    ).filter(
        Transaction.type == 'payment',
        Transaction.from_account_id.in_(account_ids),
        Transaction.created_at.between(start_date, end_date)
    )
    
    # Apply category filter if specified
    if filters and filters.get('categories'):
        query = query.filter(Transaction.category.in_(filters['categories']))
    
    results = query.group_by(Transaction.category).order_by(
        db.func.sum(Transaction.amount).desc()
    ).all()
    
    return [
        {"name": row.category or "Uncategorized", "value": round(float(row.value), 2)}
        for row in results
    ]


def query_monthly_trend(user_id: str, start_date: datetime, end_date: datetime,
                        filters: dict, db_session) -> list:
    """Query monthly spending trend"""
    from banking_app import Transaction, Account, db
    
    account_ids = get_user_account_ids(user_id, db_session, filters)
    if not account_ids:
        return []
    
    # Generate list of months in range
    months = []
    current = start_date.replace(day=1)
    while current <= end_date:
        months.append(current)
        current += relativedelta(months=1)
    
    result = []
    for month_start in months:
        month_end = month_start + relativedelta(months=1) - timedelta(seconds=1)
        
        spending = db_session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.type == 'payment',
            Transaction.from_account_id.in_(account_ids),
            Transaction.created_at.between(month_start, month_end)
        ).scalar() or 0
        
        result.append({
            "name": month_start.strftime("%b %Y"),
            "value": round(float(spending), 2)
        })
    
    return result


def query_monthly_income_expenses(user_id: str, start_date: datetime, end_date: datetime,
                                   filters: dict, db_session) -> list:
    """Query monthly income vs expenses comparison"""
    from banking_app import Transaction, Account, db
    
    account_ids = get_user_account_ids(user_id, db_session, filters)
    if not account_ids:
        return []
    
    # Generate list of months in range
    months = []
    current = start_date.replace(day=1)
    while current <= end_date:
        months.append(current)
        current += relativedelta(months=1)
    
    result = []
    for month_start in months:
        month_end = month_start + relativedelta(months=1) - timedelta(seconds=1)
        
        # Get income (deposits)
        income = db_session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.type == 'deposit',
            Transaction.to_account_id.in_(account_ids),
            Transaction.created_at.between(month_start, month_end)
        ).scalar() or 0
        
        # Get expenses (payments)
        expenses = db_session.query(
            db.func.sum(Transaction.amount)
        ).filter(
            Transaction.type == 'payment',
            Transaction.from_account_id.in_(account_ids),
            Transaction.created_at.between(month_start, month_end)
        ).scalar() or 0
        
        result.append({
            "name": month_start.strftime("%b %Y"),
            "income": round(float(income), 2),
            "expenses": round(float(expenses), 2)
        })
    
    return result


def query_account_balances(user_id: str, filters: dict, db_session) -> list:
    """Query current account balances"""
    from banking_app import Account
    
    query = db_session.query(Account).filter(Account.user_id == user_id)
    
    if filters and filters.get('account_type'):
        query = query.filter(Account.account_type == filters['account_type'])
    
    accounts = query.all()
    
    return [
        {"name": acc.name, "value": round(float(acc.balance), 2), "type": acc.account_type}
        for acc in accounts
    ]


def query_top_merchants(user_id: str, start_date: datetime, end_date: datetime,
                        filters: dict, db_session) -> list:
    """Query top merchants/payees by spending"""
    from banking_app import Transaction, Account, db
    
    account_ids = get_user_account_ids(user_id, db_session, filters)
    if not account_ids:
        return []
    
    limit = filters.get('limit', 10) if filters else 10
    
    # Extract merchant from description (simplified - takes first part before common separators)
    results = db_session.query(
        Transaction.description,
        db.func.sum(Transaction.amount).label('value'),
        db.func.count(Transaction.id).label('count')
    ).filter(
        Transaction.type == 'payment',
        Transaction.from_account_id.in_(account_ids),
        Transaction.created_at.between(start_date, end_date)
    ).group_by(
        Transaction.description
    ).order_by(
        db.func.sum(Transaction.amount).desc()
    ).limit(limit).all()
    
    return [
        {
            "name": row.description or "Unknown",
            "value": round(float(row.value), 2),
            "transactions": row.count
        }
        for row in results
    ]


def query_daily_spending(user_id: str, start_date: datetime, end_date: datetime,
                         filters: dict, db_session) -> list:
    """Query daily spending for trend analysis"""
    from banking_app import Transaction, Account, db
    
    account_ids = get_user_account_ids(user_id, db_session, filters)
    if not account_ids:
        return []
    
    # This is a simplified version - for SQL Server you'd use different date functions
    results = db_session.query(
        db.func.cast(Transaction.created_at, db.Date).label('date'),
        db.func.sum(Transaction.amount).label('value')
    ).filter(
        Transaction.type == 'payment',
        Transaction.from_account_id.in_(account_ids),
        Transaction.created_at.between(start_date, end_date)
    ).group_by(
        db.func.cast(Transaction.created_at, db.Date)
    ).order_by(
        db.func.cast(Transaction.created_at, db.Date)
    ).all()
    
    return [
        {
            "name": row.date.strftime("%Y-%m-%d") if hasattr(row.date, 'strftime') else str(row.date),
            "value": round(float(row.value), 2)
        }
        for row in results
    ]


def query_category_trend(user_id: str, start_date: datetime, end_date: datetime,
                         filters: dict, db_session) -> list:
    """Query spending trend for specific categories over time"""
    from banking_app import Transaction, Account, db
    
    account_ids = get_user_account_ids(user_id, db_session, filters)
    if not account_ids:
        return []
    
    categories = filters.get('categories', []) if filters else []
    if not categories:
        # Get top 5 categories by spending
        top_cats = db_session.query(
            Transaction.category
        ).filter(
            Transaction.type == 'payment',
            Transaction.from_account_id.in_(account_ids),
            Transaction.created_at.between(start_date, end_date)
        ).group_by(
            Transaction.category
        ).order_by(
            db.func.sum(Transaction.amount).desc()
        ).limit(5).all()
        categories = [cat[0] for cat in top_cats if cat[0]]
    
    # Generate list of months
    months = []
    current = start_date.replace(day=1)
    while current <= end_date:
        months.append(current)
        current += relativedelta(months=1)
    
    result = []
    for month_start in months:
        month_end = month_start + relativedelta(months=1) - timedelta(seconds=1)
        
        row_data = {"name": month_start.strftime("%b %Y")}
        
        for category in categories:
            spending = db_session.query(
                db.func.sum(Transaction.amount)
            ).filter(
                Transaction.type == 'payment',
                Transaction.category == category,
                Transaction.from_account_id.in_(account_ids),
                Transaction.created_at.between(month_start, month_end)
            ).scalar() or 0
            
            row_data[category] = round(float(spending), 2)
        
        result.append(row_data)
    
    return result