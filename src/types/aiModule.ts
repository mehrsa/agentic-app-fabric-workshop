export interface AIWidget {
  id: string;
  user_id: string;
  title: string;
  description: string;
  widget_type: 'chart' | 'table' | 'metric' | 'custom' | 'simulation';
  config: WidgetConfig;
  code: string | null;
  
  // Dynamic data support
  data_mode: 'static' | 'dynamic';
  query_config: QueryConfig | null;
  last_refreshed: string | null;
  
  // Simulation support
  simulation_config: SimulationConfig | null;
  
  created_at: string;
  updated_at: string;
}

export interface WidgetConfig {
  chartType?: 'line' | 'bar' | 'pie' | 'area' | 'scatter';
  dataSource?: string;
  colors?: string[];
  title?: string;
  xAxis?: string;
  yAxis?: string;
  filters?: Record<string, any>;
  customProps?: {
    data?: any[];
    [key: string]: any;
  };
}

export interface QueryConfig {
  query_type: 
    | 'spending_by_category' 
    | 'monthly_trend' 
    | 'monthly_income_expenses'
    | 'account_balances'
    | 'top_merchants'
    | 'daily_spending'
    | 'category_trend';
  time_range: 
    | 'last_6_months' 
    | 'last_3_months' 
    | 'last_12_months'
    | 'this_year' 
    | 'this_month' 
    | 'last_30_days'
    | 'last_7_days'
    | 'all_time';
  filters?: {
    account_id?: string;
    categories?: string[];
    limit?: number;
    [key: string]: any;
  };
}

export interface SimulationConfig {
  simulation_type: 
    | 'loan_repayment'
    | 'savings_projector'
    | 'budget_planner'
    | 'retirement_calculator'
    | 'emergency_fund';
  defaults?: {
    // Loan Repayment defaults
    principal?: number;
    interestRate?: number;
    termYears?: number;
    extraPayment?: number;
    
    // Savings Projector defaults
    initialDeposit?: number;
    monthlyContribution?: number;
    annualReturn?: number;
    yearsToGrow?: number;
    
    // Budget Planner defaults
    income?: number;
    housing?: number;
    transportation?: number;
    food?: number;
    savings?: number;
    
    // Retirement Calculator defaults
    currentAge?: number;
    retirementAge?: number;
    currentSavings?: number;
    expectedReturn?: number;
    
    // Emergency Fund defaults
    monthlyExpenses?: number;
    targetMonths?: number;
    monthlySavings?: number;
    
    [key: string]: any;
  };
}

export interface AIWidgetCreateRequest {
  title: string;
  description: string;
  widget_type: 'chart' | 'table' | 'metric' | 'custom' | 'simulation';
  config: WidgetConfig;
  code?: string;
  data_mode?: 'static' | 'dynamic';
  query_config?: QueryConfig;
  simulation_config?: SimulationConfig;
}

export interface AIWidgetUpdateRequest {
  title?: string;
  description?: string;
  config?: WidgetConfig;
  code?: string;
  data_mode?: 'static' | 'dynamic';
  query_config?: QueryConfig;
  simulation_config?: SimulationConfig;
}

export interface WidgetRefreshResponse {
  status: 'success' | 'error';
  message: string;
  widget?: AIWidget;
  data_points?: number;
  error?: string;
}