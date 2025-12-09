import React, { useState, useMemo } from 'react';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import { AlertCircle, RefreshCw } from 'lucide-react';
import type { AIWidget } from '../types/aiModule';

interface AIWidgetRendererProps {
  widget: AIWidget;
  data?: any[];
}

// Pre-defined color palettes
const COLOR_PALETTES = {
  blue: ['#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#DBEAFE'],
  green: ['#10B981', '#34D399', '#6EE7B7', '#A7F3D0', '#D1FAE5'],
  purple: ['#8B5CF6', '#A78BFA', '#C4B5FD', '#DDD6FE', '#EDE9FE'],
  orange: ['#F59E0B', '#FBBF24', '#FCD34D', '#FDE68A', '#FEF3C7'],
  mixed: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'],
};

const AIWidgetRenderer: React.FC<AIWidgetRendererProps> = ({ widget, data }) => {
  const [error, setError] = useState<string | null>(null);

  const colors = widget.config.colors || COLOR_PALETTES.mixed;

  const renderedContent = useMemo(() => {
    try {
      const chartData = data || widget.config.customProps?.data || [];
      const { chartType, xAxis, yAxis } = widget.config;

      if (chartData.length === 0) {
        return (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <p className="text-sm">No data available</p>
            <p className="text-xs mt-1">Ask the AI to update this widget with data</p>
          </div>
        );
      }

      switch (chartType) {
        case 'line':
          return (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey={xAxis || 'name'} stroke="#6B7280" fontSize={12} />
                <YAxis stroke="#6B7280" fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#FFFFFF', 
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }} 
                />
                <Legend />
                {Object.keys(chartData[0] || {})
                  .filter(key => key !== (xAxis || 'name'))
                  .map((key, index) => (
                    <Line
                      key={key}
                      type="monotone"
                      dataKey={key}
                      stroke={colors[index % colors.length]}
                      strokeWidth={2}
                      dot={{ fill: colors[index % colors.length], strokeWidth: 2, r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  ))}
              </LineChart>
            </ResponsiveContainer>
          );

        case 'bar':
          return (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey={xAxis || 'name'} stroke="#6B7280" fontSize={12} />
                <YAxis stroke="#6B7280" fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#FFFFFF', 
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }} 
                />
                <Legend />
                {Object.keys(chartData[0] || {})
                  .filter(key => key !== (xAxis || 'name'))
                  .map((key, index) => (
                    <Bar
                      key={key}
                      dataKey={key}
                      fill={colors[index % colors.length]}
                      radius={[4, 4, 0, 0]}
                    />
                  ))}
              </BarChart>
            </ResponsiveContainer>
          );

        case 'pie':
          return (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey={yAxis || 'value'}
                  nameKey={xAxis || 'name'}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  labelLine={{ stroke: '#9CA3AF', strokeWidth: 1 }}
                >
                  {chartData.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#FFFFFF', 
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }} 
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          );

        case 'area':
          return (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey={xAxis || 'name'} stroke="#6B7280" fontSize={12} />
                <YAxis stroke="#6B7280" fontSize={12} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#FFFFFF', 
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                  }} 
                />
                <Legend />
                {Object.keys(chartData[0] || {})
                  .filter(key => key !== (xAxis || 'name'))
                  .map((key, index) => (
                    <Area
                      key={key}
                      type="monotone"
                      dataKey={key}
                      stroke={colors[index % colors.length]}
                      fill={colors[index % colors.length]}
                      fillOpacity={0.3}
                      strokeWidth={2}
                    />
                  ))}
              </AreaChart>
            </ResponsiveContainer>
          );

        default:
          return (
            <div className="flex items-center justify-center h-full text-gray-400">
              <p>Unknown widget type: {chartType}</p>
            </div>
          );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to render widget');
      return null;
    }
  }, [widget, data, colors]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-red-400 p-4">
        <AlertCircle className="h-8 w-8 mb-2" />
        <p className="text-sm text-center">{error}</p>
        <button 
          onClick={() => setError(null)}
          className="mt-2 text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
        >
          <RefreshCw className="h-3 w-3" />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      {renderedContent}
    </div>
  );
};

export default AIWidgetRenderer;