import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart,
  Legend,
} from 'recharts'
import { TrendingUp, Calendar, RefreshCw, Wifi, WifiOff } from 'lucide-react'
import axios from 'axios'

const CROPS = ['Tomato', 'Onion', 'Potato', 'Cabbage', 'Carrot', 'Bean', 'Chilli']
const MANDIS = ['Mysuru', 'Chamarajanagar']

function ForecastChart() {
  const [selectedCrop, setSelectedCrop] = useState('Tomato')
  const [selectedMandi, setSelectedMandi] = useState('Mysuru')
  const [forecastData, setForecastData] = useState([])
  const [currentPrice, setCurrentPrice] = useState(0)
  const [confidence, setConfidence] = useState(0)
  const [loading, setLoading] = useState(false)
  const [apiConnected, setApiConnected] = useState(false)

  useEffect(() => {
    fetchForecast()
  }, [selectedCrop, selectedMandi])

  const fetchForecast = async () => {
    setLoading(true)
    try {
      // Try real backend API
      const response = await axios.get(`/api/forecast/${selectedCrop}/${selectedMandi}`, { timeout: 5000 })
      
      const data = response.data
      setCurrentPrice(data.current_price || 0)
      setConfidence(data.confidence || 0)
      setApiConnected(true)
      
      // Format forecast data for chart
      if (data.forecasts && data.forecasts.length > 0) {
        const formatted = data.forecasts.map((f, i) => {
          const dateObj = new Date(f.date)
          const dateStr = dateObj.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
          return {
            date: dateStr,
            fullDate: f.date,
            price: Math.round(f.price * 10) / 10,
            lower: Math.round(f.lower * 10) / 10,
            upper: Math.round(f.upper * 10) / 10,
            day: i + 1,
          }
        })
        setForecastData(formatted)
      }
    } catch (error) {
      console.warn('Forecast API not available, using generated data:', error.message)
      setApiConnected(false)
      
      // Generate client-side fallback data
      const basePrices = {
        'Tomato': { 'Mysuru': 25, 'Chamarajanagar': 18 },
        'Onion': { 'Mysuru': 22, 'Chamarajanagar': 18 },
        'Potato': { 'Mysuru': 20, 'Chamarajanagar': 16 },
        'Cabbage': { 'Mysuru': 15, 'Chamarajanagar': 12 },
        'Carrot': { 'Mysuru': 28, 'Chamarajanagar': 22 },
        'Bean': { 'Mysuru': 40, 'Chamarajanagar': 32 },
        'Chilli': { 'Mysuru': 60, 'Chamarajanagar': 50 },
      }
      
      const base = basePrices[selectedCrop]?.[selectedMandi] || 25
      const data = []
      
      for (let i = 0; i < 7; i++) {
        const day = new Date()
        day.setDate(day.getDate() + i + 1)
        const dateStr = day.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
        
        const trend = (Math.random() - 0.3) * 5
        const price = base + trend * (i + 1) * 0.3
        const variance = 3 + Math.random() * 3
        
        data.push({
          date: dateStr,
          fullDate: day.toISOString().split('T')[0],
          price: Math.round(price * 10) / 10,
          lower: Math.round((price - variance) * 10) / 10,
          upper: Math.round((price + variance) * 10) / 10,
          day: i + 1,
        })
      }
      
      setForecastData(data)
      setCurrentPrice(base)
      setConfidence(65 + Math.floor(Math.random() * 20))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <TrendingUp className="w-6 h-6 text-accent" />
            <span>Forecast <span className="text-accent">Chart</span></span>
          </h1>
          <p className="text-gray-400 mt-1">
            7-day price forecast with confidence band
          </p>
        </div>
        <div className="flex items-center space-x-2 mt-2 md:mt-0">
          {apiConnected ? (
            <Wifi className="w-4 h-4 text-signal-green" />
          ) : (
            <WifiOff className="w-4 h-4 text-signal-amber" />
          )}
          <span className={`text-xs ${apiConnected ? 'text-signal-green' : 'text-signal-amber'}`}>
            {apiConnected ? 'Live API' : 'Offline Mode'}
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-2">Crop</label>
            <select
              value={selectedCrop}
              onChange={(e) => setSelectedCrop(e.target.value)}
              className="input w-full"
            >
              {CROPS.map(crop => (
                <option key={crop} value={crop}>{crop}</option>
              ))}
            </select>
          </div>
          
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-2">Mandi</label>
            <select
              value={selectedMandi}
              onChange={(e) => setSelectedMandi(e.target.value)}
              className="input w-full"
            >
              {MANDIS.map(mandi => (
                <option key={mandi} value={mandi}>{mandi}</option>
              ))}
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={fetchForecast}
              disabled={loading}
              className="btn-secondary"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card">
          <p className="text-sm text-gray-400">Current Price</p>
          <p className="text-2xl font-bold text-white mt-1">
            ₹{currentPrice.toFixed(1)}/kg
          </p>
        </div>
        
        <div className="card">
          <p className="text-sm text-gray-400">Forecast Confidence</p>
          <p className="text-2xl font-bold text-accent mt-1">
            {Math.round(confidence)}%
          </p>
        </div>
        
        <div className="card">
          <p className="text-sm text-gray-400">Expected Change</p>
          <p className={`text-2xl font-bold mt-1 ${
            forecastData[6]?.price > currentPrice ? 'text-signal-green' : 'text-signal-red'
          }`}>
            {forecastData.length > 0 && currentPrice > 0 ? (
              <>
                {forecastData[forecastData.length - 1]?.price > currentPrice ? '+' : ''}
                {((forecastData[forecastData.length - 1]?.price - currentPrice) / currentPrice * 100).toFixed(1)}%
              </>
            ) : '—'}
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="card">
        <h2 className="text-lg font-semibold text-white mb-4">
          7-Day Price Forecast
        </h2>
        
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={forecastData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00E5D4" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#00E5D4" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
              <XAxis 
                dataKey="date" 
                stroke="#64748B"
                tick={{ fill: '#64748B', fontSize: 12 }}
              />
              <YAxis 
                stroke="#64748B"
                tick={{ fill: '#64748B', fontSize: 12 }}
                domain={['auto', 'auto']}
                tickFormatter={(value) => `₹${value}`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0F1824',
                  border: '1px solid #1E293B',
                  borderRadius: '8px',
                }}
                labelStyle={{ color: '#94A3B8' }}
                formatter={(value, name) => [
                  `₹${value}/kg`,
                  name === 'price' ? 'Expected Price' : 
                  name === 'upper' ? 'Upper Bound' : 'Lower Bound'
                ]}
              />
              <Legend 
                wrapperStyle={{ paddingTop: '20px' }}
                formatter={(value) => <span style={{ color: '#94A3B8' }}>{value}</span>}
              />
              <Area
                type="monotone"
                dataKey="upper"
                stroke="transparent"
                fill="url(#colorPrice)"
                fillOpacity={0.5}
              />
              <Area
                type="monotone"
                dataKey="lower"
                stroke="transparent"
                fill="#070D14"
                fillOpacity={1}
              />
              <Line
                type="monotone"
                dataKey="upper"
                stroke="#00E5D4"
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
                name="Upper Bound"
              />
              <Line
                type="monotone"
                dataKey="lower"
                stroke="#00E5D4"
                strokeWidth={1}
                strokeDasharray="5 5"
                dot={false}
                name="Lower Bound"
              />
              <Line
                type="monotone"
                dataKey="price"
                stroke="#00E5D4"
                strokeWidth={3}
                dot={{ fill: '#00E5D4', strokeWidth: 2 }}
                activeDot={{ r: 6, fill: '#00E5D4' }}
                name="Expected Price"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Forecast Table */}
      <div className="card mt-6">
        <h2 className="text-lg font-semibold text-white mb-4">
          Detailed Forecast
        </h2>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-border">
                <th className="text-left text-sm font-medium text-gray-400 px-4 py-3">
                  <Calendar className="w-4 h-4 inline mr-2" />
                  Date
                </th>
                <th className="text-right text-sm font-medium text-gray-400 px-4 py-3">
                  Expected Price
                </th>
                <th className="text-right text-sm font-medium text-gray-400 px-4 py-3">
                  Lower Bound
                </th>
                <th className="text-right text-sm font-medium text-gray-400 px-4 py-3">
                  Upper Bound
                </th>
                <th className="text-right text-sm font-medium text-gray-400 px-4 py-3">
                  Change
                </th>
              </tr>
            </thead>
            <tbody>
              {forecastData.map((day, index) => (
                <tr key={index} className="border-b border-dark-border hover:bg-dark-border/30">
                  <td className="px-4 py-3 text-white">
                    {day.date}
                  </td>
                  <td className="px-4 py-3 text-right text-white font-medium">
                    ₹{day.price.toFixed(1)}/kg
                  </td>
                  <td className="px-4 py-3 text-right text-gray-400">
                    ₹{day.lower.toFixed(1)}/kg
                  </td>
                  <td className="px-4 py-3 text-right text-gray-400">
                    ₹{day.upper.toFixed(1)}/kg
                  </td>
                  <td className="px-4 py-3 text-right">
                    {currentPrice > 0 ? (
                      <span className={`text-sm ${
                        day.price > currentPrice ? 'text-signal-green' : 'text-signal-red'
                      }`}>
                        {day.price > currentPrice ? '+' : ''}
                        {((day.price - currentPrice) / currentPrice * 100).toFixed(1)}%
                      </span>
                    ) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default ForecastChart
