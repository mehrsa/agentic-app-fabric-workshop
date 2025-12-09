"""
AI Widget Data Model - Stores user-specific AI-generated widgets
Supports static, dynamic (query-based), and simulation (interactive) data modes
"""
import copy
import uuid
from datetime import datetime
from sqlalchemy.orm.attributes import flag_modified

# Global variables that will be set by the main app
db = None
AIWidget = None

def init_ai_widget_db(database):
    """Initialize the database reference and create AI Widget model"""
    global db, AIWidget
    db = database

    def to_dict_helper(instance):
        d = {}
        for column in instance.__table__.columns:
            value = getattr(instance, column.name)
            if isinstance(value, datetime):
                d[column.name] = value.isoformat()
            else:
                d[column.name] = value
        return d

    class AIWidgetModel(db.Model):
        __tablename__ = 'ai_widgets'
        id = db.Column(db.String(255), primary_key=True, default=lambda: f"widget_{uuid.uuid4()}")
        user_id = db.Column(db.String(255), nullable=False, index=True)
        title = db.Column(db.String(500), nullable=False)
        description = db.Column(db.Text)
        widget_type = db.Column(db.String(50), nullable=False)  # 'chart', 'table', 'metric', 'custom', 'simulation'
        config = db.Column(db.JSON, nullable=False)  # Chart configuration
        code = db.Column(db.Text)  # Optional: stored React component code
        
        # Dynamic data support fields
        data_mode = db.Column(db.String(20), nullable=False, default='static')  # 'static' or 'dynamic'
        query_config = db.Column(db.JSON, nullable=True)  # For dynamic widgets: query definition
        last_refreshed = db.Column(db.DateTime, nullable=True)  # When data was last fetched
        
        # Simulation support fields
        simulation_config = db.Column(db.JSON, nullable=True)  # For simulation widgets: type and defaults
        
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def to_dict(self):
            return to_dict_helper(self)

    AIWidget = AIWidgetModel
    globals()['AIWidget'] = AIWidget
    return AIWidget


def get_user_widgets(user_id: str):
    """Get all widgets for a specific user"""
    widgets = AIWidget.query.filter_by(user_id=user_id).order_by(AIWidget.updated_at.desc()).all()
    return [widget.to_dict() for widget in widgets]


def create_widget(user_id: str, title: str, description: str, widget_type: str, config: dict, 
                  code: str = None, data_mode: str = 'static', query_config: dict = None,
                  simulation_config: dict = None):
    """Create a new AI widget for a user"""
    widget = AIWidget(
        user_id=user_id,
        title=title,
        description=description,
        widget_type=widget_type,
        config=config,
        code=code,
        data_mode=data_mode,
        query_config=query_config,
        simulation_config=simulation_config,
        last_refreshed=datetime.utcnow() if data_mode == 'dynamic' else None
    )
    db.session.add(widget)
    db.session.commit()
    return widget.to_dict()


def update_widget(widget_id: str, user_id: str, updates: dict):
    """Update an existing widget (only if owned by the user)"""
    widget = AIWidget.query.filter_by(id=widget_id, user_id=user_id).first()
    if not widget:
        return None
    
    if 'title' in updates:
        widget.title = updates['title']
    if 'description' in updates:
        widget.description = updates['description']
    if 'widget_type' in updates:
        widget.widget_type = updates['widget_type']
    if 'config' in updates:
        widget.config = updates['config']
    if 'code' in updates:
        widget.code = updates['code']
    if 'data_mode' in updates:
        widget.data_mode = updates['data_mode']
    if 'query_config' in updates:
        widget.query_config = updates['query_config']
    if 'simulation_config' in updates:
        widget.simulation_config = updates['simulation_config']
    if 'last_refreshed' in updates:
        widget.last_refreshed = updates['last_refreshed']
    
    widget.updated_at = datetime.utcnow()
    db.session.commit()
    return widget.to_dict()


def update_widget_data(widget_id: str, user_id: str, new_data: list):
    """Update just the data portion of a widget's config (for refresh)"""
    widget = AIWidget.query.filter_by(id=widget_id, user_id=user_id).first()
    if not widget:
        return None
    
    # IMPORTANT: Create a NEW dict object instead of modifying in place
    # This ensures SQLAlchemy detects the change to the JSON column
    new_config = copy.deepcopy(widget.config) if widget.config else {}
    
    if 'customProps' not in new_config:
        new_config['customProps'] = {}
    new_config['customProps']['data'] = new_data
    
    # Assign the new dict to trigger SQLAlchemy's change detection
    widget.config = new_config
    
    # Also explicitly flag the column as modified (belt and suspenders)
    flag_modified(widget, 'config')
    
    widget.last_refreshed = datetime.utcnow()
    widget.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Re-query to get the fresh data from database
    db.session.refresh(widget)
    
    return widget.to_dict()


def update_simulation_defaults(widget_id: str, user_id: str, new_defaults: dict):
    """Update simulation widget defaults"""
    widget = AIWidget.query.filter_by(id=widget_id, user_id=user_id).first()
    if not widget or widget.widget_type != 'simulation':
        return None
    
    # Create a new dict to ensure SQLAlchemy detects changes
    new_simulation_config = copy.deepcopy(widget.simulation_config) if widget.simulation_config else {}
    
    if 'defaults' not in new_simulation_config:
        new_simulation_config['defaults'] = {}
    
    new_simulation_config['defaults'].update(new_defaults)
    
    widget.simulation_config = new_simulation_config
    flag_modified(widget, 'simulation_config')
    
    widget.updated_at = datetime.utcnow()
    
    db.session.commit()
    db.session.refresh(widget)
    
    return widget.to_dict()


def delete_widget(widget_id: str, user_id: str):
    """Delete a widget (only if owned by the user)"""
    widget = AIWidget.query.filter_by(id=widget_id, user_id=user_id).first()
    if not widget:
        return False
    
    db.session.delete(widget)
    db.session.commit()
    return True


def get_widget_by_id(widget_id: str, user_id: str):
    """Get a specific widget by ID (only if owned by the user)"""
    widget = AIWidget.query.filter_by(id=widget_id, user_id=user_id).first()
    return widget.to_dict() if widget else None