import React, { useState, useMemo, useCallback } from 'react';
import { 
  LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { Calculator, TrendingUp, PiggyBank, Home, CreditCard, Target, Sliders } from 'lucide-react';
import type { AIWidget, SimulationConfig } from '../types/aiModule';

interface SimulationWidgetRendererProps {
  widget: AIWidget;
}

// Slider Input Component
interface SliderInputProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit?: string;
  prefix?: string;
  onChange: (value: number) => void;
  color?: string;
}

const SliderInput: React.FC<SliderInputProps> = ({ 
  label, value, min, max, step, unit = '', prefix = '', onChange, color = '#3B82F6' 
}) => {
  const percentage = ((value - min) / (max - min)) * 100;
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-sm font-bold" style={{ color }}>
          {prefix}{value.toLocaleString()}{unit}
        </span>
      </div>
      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider-thumb"
          style={{
            background: `linear-gradient(to right, ${color} 0%, ${color} ${percentage}%, #E5E7EB ${percentage}%, #E5E7EB 100%)`
          }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-400">
        <span>{prefix}{min.toLocaleString()}{unit}</span>
        <span>{prefix}{max.toLocaleString()}{unit}</span>
      </div>
    </div>
  );
};

// Loan Repayment Simulator
const LoanRepaymentSimulator: React.FC<{ config: SimulationConfig }> = ({ config }) => {
  const defaults = config.defaults || {};
  const [principal, setPrincipal] = useState(defaults.principal || 250000);
  const [interestRate, setInterestRate] = useState(defaults.interestRate || 6.5);
  const [termYears, setTermYears] = useState(defaults.termYears || 30);
  const [extraPayment, setExtraPayment] = useState(defaults.extraPayment || 0);

  const calculations = useMemo(() => {
    const monthlyRate = interestRate / 100 / 12;
    const totalPayments = termYears * 12;
    
    // Standard monthly payment (without extra)
    const standardMonthly = principal * (monthlyRate * Math.pow(1 + monthlyRate, totalPayments)) 
      / (Math.pow(1 + monthlyRate, totalPayments) - 1);
    
    // Generate amortization schedule
    const standardSchedule: any[] = [];
    const acceleratedSchedule: any[] = [];
    
    let standardBalance = principal;
    let acceleratedBalance = principal;
    let standardTotalInterest = 0;
    let acceleratedTotalInterest = 0;
    
    for (let month = 1; month <= totalPayments && (standardBalance > 0 || acceleratedBalance > 0); month++) {
      const year = Math.ceil(month / 12);
      
      // Standard payment
      if (standardBalance > 0) {
        const standardInterestPayment = standardBalance * monthlyRate;
        const standardPrincipalPayment = Math.min(standardMonthly - standardInterestPayment, standardBalance);
        standardBalance = Math.max(0, standardBalance - standardPrincipalPayment);
        standardTotalInterest += standardInterestPayment;
        
        if (month % 12 === 0 || month === totalPayments || standardBalance === 0) {
          standardSchedule.push({
            year,
            balance: Math.round(standardBalance),
            totalInterest: Math.round(standardTotalInterest)
          });
        }
      }
      
      // Accelerated payment
      if (acceleratedBalance > 0) {
        const acceleratedInterestPayment = acceleratedBalance * monthlyRate;
        const acceleratedPrincipalPayment = Math.min(
          standardMonthly + extraPayment - acceleratedInterestPayment, 
          acceleratedBalance
        );
        acceleratedBalance = Math.max(0, acceleratedBalance - acceleratedPrincipalPayment);
        acceleratedTotalInterest += acceleratedInterestPayment;
        
        if (month % 12 === 0 || acceleratedBalance === 0) {
          const existingEntry = acceleratedSchedule.find(e => e.year === year);
          if (!existingEntry) {
            acceleratedSchedule.push({
              year,
              acceleratedBalance: Math.round(acceleratedBalance),
              acceleratedInterest: Math.round(acceleratedTotalInterest)
            });
          } else {
            existingEntry.acceleratedBalance = Math.round(acceleratedBalance);
            existingEntry.acceleratedInterest = Math.round(acceleratedTotalInterest);
          }
        }
      }
    }
    
    // Merge schedules
    const chartData = standardSchedule.map(std => {
      const acc = acceleratedSchedule.find(a => a.year === std.year) || {};
      return {
        year: `Year ${std.year}`,
        'Standard Balance': std.balance,
        'With Extra Payment': acc.acceleratedBalance ?? std.balance,
      };
    });
    
    const payoffYearsStandard = termYears;
    const payoffYearsAccelerated = acceleratedSchedule.length > 0 
      ? acceleratedSchedule.findIndex(s => s.acceleratedBalance === 0) + 1 || termYears
      : termYears;
    
    const interestSaved = standardTotalInterest - acceleratedTotalInterest;
    const yearsSaved = payoffYearsStandard - payoffYearsAccelerated;
    
    return {
      monthlyPayment: standardMonthly,
      totalInterestStandard: standardTotalInterest,
      totalInterestAccelerated: acceleratedTotalInterest,
      interestSaved,
      yearsSaved,
      chartData: chartData.filter((_, i) => i % Math.ceil(chartData.length / 15) === 0 || i === chartData.length - 1)
    };
  }, [principal, interestRate, termYears, extraPayment]);

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <SliderInput
          label="Loan Amount"
          value={principal}
          min={50000}
          max={1000000}
          step={10000}
          prefix="$"
          onChange={setPrincipal}
          color="#3B82F6"
        />
        <SliderInput
          label="Interest Rate"
          value={interestRate}
          min={2}
          max={12}
          step={0.25}
          unit="%"
          onChange={setInterestRate}
          color="#EF4444"
        />
        <SliderInput
          label="Loan Term"
          value={termYears}
          min={5}
          max={30}
          step={5}
          unit=" years"
          onChange={setTermYears}
          color="#8B5CF6"
        />
        <SliderInput
          label="Extra Monthly Payment"
          value={extraPayment}
          min={0}
          max={2000}
          step={50}
          prefix="$"
          onChange={setExtraPayment}
          color="#10B981"
        />
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-blue-50 rounded-lg p-3 text-center">
          <p className="text-xs text-blue-600 font-medium">Monthly Payment</p>
          <p className="text-lg font-bold text-blue-700">${Math.round(calculations.monthlyPayment).toLocaleString()}</p>
        </div>
        <div className="bg-green-50 rounded-lg p-3 text-center">
          <p className="text-xs text-green-600 font-medium">Interest Saved</p>
          <p className="text-lg font-bold text-green-700">${Math.round(calculations.interestSaved).toLocaleString()}</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-3 text-center">
          <p className="text-xs text-purple-600 font-medium">Years Saved</p>
          <p className="text-lg font-bold text-purple-700">{calculations.yearsSaved.toFixed(1)}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={calculations.chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="year" tick={{ fontSize: 10 }} />
            <YAxis tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 10 }} />
            <Tooltip 
              formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #E5E7EB', borderRadius: '8px' }}
            />
            <Legend />
            <Area 
              type="monotone" 
              dataKey="Standard Balance" 
              stroke="#94A3B8" 
              fill="#94A3B8" 
              fillOpacity={0.3}
              strokeWidth={2}
            />
            <Area 
              type="monotone" 
              dataKey="With Extra Payment" 
              stroke="#10B981" 
              fill="#10B981" 
              fillOpacity={0.5}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// Savings Projector
const SavingsProjector: React.FC<{ config: SimulationConfig }> = ({ config }) => {
  const defaults = config.defaults || {};
  const [initialDeposit, setInitialDeposit] = useState(defaults.initialDeposit || 5000);
  const [monthlyContribution, setMonthlyContribution] = useState(defaults.monthlyContribution || 500);
  const [annualReturn, setAnnualReturn] = useState(defaults.annualReturn || 7);
  const [yearsToGrow, setYearsToGrow] = useState(defaults.yearsToGrow || 20);

  const calculations = useMemo(() => {
    const monthlyRate = annualReturn / 100 / 12;
    const totalMonths = yearsToGrow * 12;
    
    const chartData: any[] = [];
    let balance = initialDeposit;
    let totalContributions = initialDeposit;
    
    for (let month = 0; month <= totalMonths; month++) {
      if (month > 0) {
        balance = balance * (1 + monthlyRate) + monthlyContribution;
        totalContributions += monthlyContribution;
      }
      
      if (month % 12 === 0) {
        chartData.push({
          year: `Year ${month / 12}`,
          'Total Value': Math.round(balance),
          'Contributions': Math.round(totalContributions),
          'Interest Earned': Math.round(balance - totalContributions)
        });
      }
    }
    
    const finalValue = balance;
    const totalInterest = finalValue - totalContributions;
    
    return {
      finalValue,
      totalContributions,
      totalInterest,
      chartData
    };
  }, [initialDeposit, monthlyContribution, annualReturn, yearsToGrow]);

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <SliderInput
          label="Initial Deposit"
          value={initialDeposit}
          min={0}
          max={100000}
          step={1000}
          prefix="$"
          onChange={setInitialDeposit}
          color="#3B82F6"
        />
        <SliderInput
          label="Monthly Contribution"
          value={monthlyContribution}
          min={0}
          max={5000}
          step={50}
          prefix="$"
          onChange={setMonthlyContribution}
          color="#10B981"
        />
        <SliderInput
          label="Expected Annual Return"
          value={annualReturn}
          min={1}
          max={15}
          step={0.5}
          unit="%"
          onChange={setAnnualReturn}
          color="#F59E0B"
        />
        <SliderInput
          label="Investment Period"
          value={yearsToGrow}
          min={1}
          max={40}
          step={1}
          unit=" years"
          onChange={setYearsToGrow}
          color="#8B5CF6"
        />
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-3 text-center border border-blue-100">
          <p className="text-xs text-blue-600 font-medium">Final Value</p>
          <p className="text-lg font-bold text-blue-700">${Math.round(calculations.finalValue).toLocaleString()}</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-3 text-center border border-green-100">
          <p className="text-xs text-green-600 font-medium">Total Contributions</p>
          <p className="text-lg font-bold text-green-700">${Math.round(calculations.totalContributions).toLocaleString()}</p>
        </div>
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg p-3 text-center border border-amber-100">
          <p className="text-xs text-amber-600 font-medium">Interest Earned</p>
          <p className="text-lg font-bold text-amber-700">${Math.round(calculations.totalInterest).toLocaleString()}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={calculations.chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="year" tick={{ fontSize: 10 }} />
            <YAxis tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 10 }} />
            <Tooltip 
              formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #E5E7EB', borderRadius: '8px' }}
            />
            <Legend />
            <Area 
              type="monotone" 
              dataKey="Interest Earned" 
              stackId="1"
              stroke="#F59E0B" 
              fill="#F59E0B" 
              fillOpacity={0.6}
            />
            <Area 
              type="monotone" 
              dataKey="Contributions" 
              stackId="1"
              stroke="#3B82F6" 
              fill="#3B82F6" 
              fillOpacity={0.6}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// Budget Planner Simulator
const BudgetPlannerSimulator: React.FC<{ config: SimulationConfig }> = ({ config }) => {
  const defaults = config.defaults || {};
  const [income, setIncome] = useState(defaults.income || 6000);
  const [housing, setHousing] = useState(defaults.housing || 30);
  const [transportation, setTransportation] = useState(defaults.transportation || 15);
  const [food, setFood] = useState(defaults.food || 12);
  const [savings, setSavings] = useState(defaults.savings || 20);

  const calculations = useMemo(() => {
    const totalAllocated = housing + transportation + food + savings;
    const remaining = 100 - totalAllocated;
    
    const housingAmount = (income * housing) / 100;
    const transportationAmount = (income * transportation) / 100;
    const foodAmount = (income * food) / 100;
    const savingsAmount = (income * savings) / 100;
    const remainingAmount = (income * remaining) / 100;
    
    const annualSavings = savingsAmount * 12;
    const fiveYearProjection = annualSavings * 5 * 1.05; // 5% compound
    
    return {
      totalAllocated,
      remaining,
      housingAmount,
      transportationAmount,
      foodAmount,
      savingsAmount,
      remainingAmount,
      annualSavings,
      fiveYearProjection,
      chartData: [
        { name: 'Housing', value: housingAmount, percent: housing, fill: '#3B82F6' },
        { name: 'Transport', value: transportationAmount, percent: transportation, fill: '#8B5CF6' },
        { name: 'Food', value: foodAmount, percent: food, fill: '#F59E0B' },
        { name: 'Savings', value: savingsAmount, percent: savings, fill: '#10B981' },
        { name: 'Other', value: remainingAmount, percent: remaining, fill: '#6B7280' },
      ]
    };
  }, [income, housing, transportation, food, savings]);

  const isOverBudget = calculations.totalAllocated > 100;

  return (
    <div className="h-full flex flex-col">
      {/* Income Slider */}
      <div className="mb-4">
        <SliderInput
          label="Monthly Income"
          value={income}
          min={2000}
          max={20000}
          step={500}
          prefix="$"
          onChange={setIncome}
          color="#10B981"
        />
      </div>

      {/* Category Sliders */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <SliderInput
          label="🏠 Housing"
          value={housing}
          min={0}
          max={50}
          step={1}
          unit="%"
          onChange={setHousing}
          color="#3B82F6"
        />
        <SliderInput
          label="🚗 Transportation"
          value={transportation}
          min={0}
          max={30}
          step={1}
          unit="%"
          onChange={setTransportation}
          color="#8B5CF6"
        />
        <SliderInput
          label="🍔 Food"
          value={food}
          min={0}
          max={30}
          step={1}
          unit="%"
          onChange={setFood}
          color="#F59E0B"
        />
        <SliderInput
          label="💰 Savings"
          value={savings}
          min={0}
          max={50}
          step={1}
          unit="%"
          onChange={setSavings}
          color="#10B981"
        />
      </div>

      {/* Warning if over budget */}
      {isOverBudget && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-2 mb-3 text-center">
          <p className="text-sm text-red-600 font-medium">
            ⚠️ Over budget by {(calculations.totalAllocated - 100).toFixed(0)}%
          </p>
        </div>
      )}

      {/* Visual Budget Breakdown */}
      <div className="mb-4">
        <div className="flex h-8 rounded-lg overflow-hidden">
          {calculations.chartData.map((item, i) => (
            <div
              key={item.name}
              className="flex items-center justify-center text-xs font-medium text-white transition-all duration-300"
              style={{ 
                width: `${Math.max(item.percent, 0)}%`, 
                backgroundColor: item.fill,
                minWidth: item.percent > 0 ? '20px' : '0'
              }}
              title={`${item.name}: $${item.value.toLocaleString()} (${item.percent}%)`}
            >
              {item.percent >= 10 && `${item.percent}%`}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          {calculations.chartData.map(item => (
            <div key={item.name} className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.fill }} />
              <span>{item.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Projections */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-3 text-center border border-green-100">
          <p className="text-xs text-green-600 font-medium">Monthly Savings</p>
          <p className="text-xl font-bold text-green-700">${Math.round(calculations.savingsAmount).toLocaleString()}</p>
        </div>
        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-3 text-center border border-blue-100">
          <p className="text-xs text-blue-600 font-medium">5-Year Projection</p>
          <p className="text-xl font-bold text-blue-700">${Math.round(calculations.fiveYearProjection).toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
};

// Retirement Calculator
const RetirementCalculator: React.FC<{ config: SimulationConfig }> = ({ config }) => {
  const defaults = config.defaults || {};
  const [currentAge, setCurrentAge] = useState(defaults.currentAge || 30);
  const [retirementAge, setRetirementAge] = useState(defaults.retirementAge || 65);
  const [currentSavings, setCurrentSavings] = useState(defaults.currentSavings || 50000);
  const [monthlyContribution, setMonthlyContribution] = useState(defaults.monthlyContribution || 1000);
  const [expectedReturn, setExpectedReturn] = useState(defaults.expectedReturn || 7);

  const calculations = useMemo(() => {
    const yearsToRetirement = retirementAge - currentAge;
    const monthlyRate = expectedReturn / 100 / 12;
    const totalMonths = yearsToRetirement * 12;
    
    const chartData: any[] = [];
    let balance = currentSavings;
    
    for (let year = 0; year <= yearsToRetirement; year++) {
      chartData.push({
        age: currentAge + year,
        'Savings': Math.round(balance),
      });
      
      // Compound for next year
      for (let month = 0; month < 12 && year < yearsToRetirement; month++) {
        balance = balance * (1 + monthlyRate) + monthlyContribution;
      }
    }
    
    const finalBalance = balance;
    const totalContributions = currentSavings + (monthlyContribution * totalMonths);
    const totalGrowth = finalBalance - totalContributions;
    
    // Safe withdrawal rate (4% rule)
    const monthlyRetirementIncome = (finalBalance * 0.04) / 12;
    
    return {
      finalBalance,
      totalContributions,
      totalGrowth,
      monthlyRetirementIncome,
      yearsToRetirement,
      chartData
    };
  }, [currentAge, retirementAge, currentSavings, monthlyContribution, expectedReturn]);

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <SliderInput
          label="Current Age"
          value={currentAge}
          min={18}
          max={60}
          step={1}
          unit=" yrs"
          onChange={setCurrentAge}
          color="#6B7280"
        />
        <SliderInput
          label="Retirement Age"
          value={retirementAge}
          min={50}
          max={75}
          step={1}
          unit=" yrs"
          onChange={setRetirementAge}
          color="#8B5CF6"
        />
        <SliderInput
          label="Current Savings"
          value={currentSavings}
          min={0}
          max={500000}
          step={5000}
          prefix="$"
          onChange={setCurrentSavings}
          color="#3B82F6"
        />
        <SliderInput
          label="Monthly Contribution"
          value={monthlyContribution}
          min={0}
          max={5000}
          step={100}
          prefix="$"
          onChange={setMonthlyContribution}
          color="#10B981"
        />
      </div>

      <div className="mb-4">
        <SliderInput
          label="Expected Annual Return"
          value={expectedReturn}
          min={3}
          max={12}
          step={0.5}
          unit="%"
          onChange={setExpectedReturn}
          color="#F59E0B"
        />
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-3 text-center border border-indigo-100">
          <p className="text-xs text-indigo-600 font-medium">Retirement Nest Egg</p>
          <p className="text-lg font-bold text-indigo-700">${Math.round(calculations.finalBalance).toLocaleString()}</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-teal-50 rounded-lg p-3 text-center border border-green-100">
          <p className="text-xs text-green-600 font-medium">Monthly Income (4% rule)</p>
          <p className="text-lg font-bold text-green-700">${Math.round(calculations.monthlyRetirementIncome).toLocaleString()}</p>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-[180px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={calculations.chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="age" tick={{ fontSize: 10 }} label={{ value: 'Age', position: 'bottom', fontSize: 10 }} />
            <YAxis tickFormatter={(v) => `$${(v/1000000).toFixed(1)}M`} tick={{ fontSize: 10 }} />
            <Tooltip 
              formatter={(value: number) => [`$${value.toLocaleString()}`, 'Savings']}
              labelFormatter={(label) => `Age ${label}`}
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #E5E7EB', borderRadius: '8px' }}
            />
            <ReferenceLine x={retirementAge} stroke="#8B5CF6" strokeDasharray="5 5" label={{ value: '🎉 Retirement', fontSize: 10 }} />
            <Area 
              type="monotone" 
              dataKey="Savings" 
              stroke="#3B82F6" 
              fill="url(#retirementGradient)" 
              strokeWidth={2}
            />
            <defs>
              <linearGradient id="retirementGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.6} />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity={0.1} />
              </linearGradient>
            </defs>
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// Emergency Fund Calculator
const EmergencyFundCalculator: React.FC<{ config: SimulationConfig }> = ({ config }) => {
  const defaults = config.defaults || {};
  const [monthlyExpenses, setMonthlyExpenses] = useState(defaults.monthlyExpenses || 4000);
  const [targetMonths, setTargetMonths] = useState(defaults.targetMonths || 6);
  const [currentSavings, setCurrentSavings] = useState(defaults.currentSavings || 5000);
  const [monthlySavings, setMonthlySavings] = useState(defaults.monthlySavings || 500);

  const calculations = useMemo(() => {
    const targetAmount = monthlyExpenses * targetMonths;
    const remaining = Math.max(0, targetAmount - currentSavings);
    const monthsToGoal = monthlySavings > 0 ? Math.ceil(remaining / monthlySavings) : Infinity;
    const progress = Math.min(100, (currentSavings / targetAmount) * 100);
    
    // Generate projection data
    const chartData: any[] = [];
    let balance = currentSavings;
    const maxMonths = Math.min(monthsToGoal + 6, 36);
    
    for (let month = 0; month <= maxMonths; month++) {
      chartData.push({
        month: `M${month}`,
        'Savings': Math.min(balance, targetAmount * 1.2),
        'Target': targetAmount
      });
      balance += monthlySavings;
    }
    
    return {
      targetAmount,
      remaining,
      monthsToGoal,
      progress,
      chartData
    };
  }, [monthlyExpenses, targetMonths, currentSavings, monthlySavings]);

  const getProgressColor = (progress: number) => {
    if (progress >= 100) return '#10B981';
    if (progress >= 50) return '#F59E0B';
    return '#EF4444';
  };

  return (
    <div className="h-full flex flex-col">
      {/* Controls */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <SliderInput
          label="Monthly Expenses"
          value={monthlyExpenses}
          min={1000}
          max={15000}
          step={500}
          prefix="$"
          onChange={setMonthlyExpenses}
          color="#EF4444"
        />
        <SliderInput
          label="Target Months"
          value={targetMonths}
          min={3}
          max={12}
          step={1}
          unit=" mo"
          onChange={setTargetMonths}
          color="#8B5CF6"
        />
        <SliderInput
          label="Current Emergency Fund"
          value={currentSavings}
          min={0}
          max={100000}
          step={1000}
          prefix="$"
          onChange={setCurrentSavings}
          color="#3B82F6"
        />
        <SliderInput
          label="Monthly Savings"
          value={monthlySavings}
          min={0}
          max={3000}
          step={100}
          prefix="$"
          onChange={setMonthlySavings}
          color="#10B981"
        />
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">Progress to Goal</span>
          <span className="font-bold" style={{ color: getProgressColor(calculations.progress) }}>
            {calculations.progress.toFixed(0)}%
          </span>
        </div>
        <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full rounded-full transition-all duration-500"
            style={{ 
              width: `${calculations.progress}%`,
              backgroundColor: getProgressColor(calculations.progress)
            }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>${currentSavings.toLocaleString()}</span>
          <span>Target: ${calculations.targetAmount.toLocaleString()}</span>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-3 text-center border border-blue-100">
          <p className="text-xs text-blue-600 font-medium">Remaining to Save</p>
          <p className="text-lg font-bold text-blue-700">${calculations.remaining.toLocaleString()}</p>
        </div>
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-3 text-center border border-green-100">
          <p className="text-xs text-green-600 font-medium">Months to Goal</p>
          <p className="text-lg font-bold text-green-700">
            {calculations.monthsToGoal === Infinity ? '∞' : calculations.monthsToGoal}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-[150px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={calculations.chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis dataKey="month" tick={{ fontSize: 10 }} />
            <YAxis tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} tick={{ fontSize: 10 }} />
            <Tooltip 
              formatter={(value: number) => [`$${value.toLocaleString()}`, '']}
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #E5E7EB', borderRadius: '8px' }}
            />
            <ReferenceLine y={calculations.targetAmount} stroke="#10B981" strokeDasharray="5 5" />
            <Line 
              type="monotone" 
              dataKey="Savings" 
              stroke="#3B82F6" 
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

// Main Simulation Widget Renderer
const SimulationWidgetRenderer: React.FC<SimulationWidgetRendererProps> = ({ widget }) => {
  const simulationConfig = widget.simulation_config;
  
  if (!simulationConfig) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400">
        <Sliders className="h-8 w-8 mb-2" />
        <p className="text-sm">No simulation configuration found</p>
      </div>
    );
  }

  const renderSimulator = () => {
    switch (simulationConfig.simulation_type) {
      case 'loan_repayment':
        return <LoanRepaymentSimulator config={simulationConfig} />;
      case 'savings_projector':
        return <SavingsProjector config={simulationConfig} />;
      case 'budget_planner':
        return <BudgetPlannerSimulator config={simulationConfig} />;
      case 'retirement_calculator':
        return <RetirementCalculator config={simulationConfig} />;
      case 'emergency_fund':
        return <EmergencyFundCalculator config={simulationConfig} />;
      default:
        return (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Calculator className="h-8 w-8 mb-2" />
            <p className="text-sm">Unknown simulation type: {simulationConfig.simulation_type}</p>
          </div>
        );
    }
  };

  return (
    <div className="w-full h-full">
      <style>{`
        .slider-thumb::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: white;
          border: 2px solid currentColor;
          cursor: pointer;
          box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        .slider-thumb::-moz-range-thumb {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: white;
          border: 2px solid currentColor;
          cursor: pointer;
          box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
      `}</style>
      {renderSimulator()}
    </div>
  );
};

export default SimulationWidgetRenderer;