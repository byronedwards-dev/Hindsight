'use client'

import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea
} from 'recharts'
import { MonthlyData } from '@/lib/api'

interface AssetChartProps {
  data: MonthlyData[]
  showForward?: boolean
  showPredictionLine?: boolean  // Show vertical line at month 24
  startDate?: string  // Date of month 24 (the prediction point, e.g., "2010-01-01")
}

// Helper to format month index to actual date label
function getMonthLabel(monthIndex: number, startDateStr?: string): string {
  if (!startDateStr) {
    return `Month ${monthIndex}`
  }
  // Parse the date string (YYYY-MM-DD) to get year and month directly
  const [year, month] = startDateStr.split('-').map(Number)
  // startDateStr is month 24, calculate offset from there
  // monthIndex 24 = startDate, monthIndex 1 = 23 months before, monthIndex 36 = 12 months after
  const totalMonths = (year * 12 + (month - 1)) + (monthIndex - 24)
  const resultYear = Math.floor(totalMonths / 12)
  const resultMonth = totalMonths % 12
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  return `${monthNames[resultMonth]} ${resultYear}`
}

export function AssetChart({ data, showForward = false, showPredictionLine = false, startDate }: AssetChartProps) {
  // Filter to historical data unless showForward is true
  const chartData = showForward 
    ? data 
    : data.filter(d => !d.is_forward)
  
  // Format data for recharts
  const formattedData = chartData.map(d => ({
    month: getMonthLabel(d.month_index, startDate),
    monthIndex: d.month_index,
    stocks: Number(d.idx_stocks.toFixed(1)),
    bonds: Number(d.idx_bonds.toFixed(1)),
    cash: Number(d.idx_cash.toFixed(1)),
    gold: Number(d.idx_gold.toFixed(1)),
    isForward: d.is_forward,
  }))
  
  // Find the label for month 24 (prediction point) from actual data
  const month24Label = formattedData.find(d => d.monthIndex === 24)?.month
  const month25Label = formattedData.find(d => d.monthIndex === 25)?.month
  const lastMonthLabel = formattedData[formattedData.length - 1]?.month

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0]?.payload
      const isForward = dataPoint?.isForward
      
      return (
        <div className="chart-tooltip bg-terminal-card border border-terminal-border rounded-lg p-3">
          <p className="font-mono text-sm text-terminal-text mb-2">
            {label}
            {isForward && <span className="ml-2 text-gain text-xs">(Forward Period)</span>}
          </p>
          {payload.map((entry: any, index: number) => (
            <p 
              key={index} 
              className="font-mono text-xs"
              style={{ color: entry.color }}
            >
              {entry.name}: {entry.value.toFixed(1)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formattedData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2a36" />
          <XAxis 
            dataKey="month" 
            tick={{ fill: '#64748b', fontSize: 11 }}
            tickLine={{ stroke: '#1e2a36' }}
            axisLine={{ stroke: '#1e2a36' }}
            interval={5}
          />
          <YAxis 
            tick={{ fill: '#64748b', fontSize: 11 }}
            tickLine={{ stroke: '#1e2a36' }}
            axisLine={{ stroke: '#1e2a36' }}
            domain={['auto', 'auto']}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ paddingTop: 10 }}
            formatter={(value) => <span className="text-terminal-text text-sm">{value}</span>}
          />
          
          {/* Shaded area for forward period */}
          {showPredictionLine && showForward && month25Label && lastMonthLabel && (
            <ReferenceArea
              x1={month25Label}
              x2={lastMonthLabel}
              fill="#22c55e"
              fillOpacity={0.15}
              ifOverflow="visible"
            />
          )}
          
          {/* Vertical line at month 24 - the prediction point */}
          {showPredictionLine && month24Label && (
            <ReferenceLine 
              x={month24Label} 
              stroke="#f59e0b" 
              strokeWidth={3}
              strokeDasharray="8 4"
              ifOverflow="extendDomain"
              isFront={true}
              label={{
                value: "← Your Prediction",
                position: 'insideTopLeft',
                fill: '#f59e0b',
                fontSize: 11,
                fontWeight: 'bold'
              }}
            />
          )}
          
          <Line 
            type="monotone" 
            dataKey="stocks" 
            name="Stocks"
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#3b82f6' }}
          />
          <Line 
            type="monotone" 
            dataKey="bonds" 
            name="Bonds"
            stroke="#22c55e" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#22c55e' }}
          />
          <Line 
            type="monotone" 
            dataKey="cash" 
            name="Cash"
            stroke="#94a3b8" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#94a3b8' }}
          />
          <Line 
            type="monotone" 
            dataKey="gold" 
            name="Gold"
            stroke="#eab308" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#eab308' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
