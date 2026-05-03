import React, { useState, useEffect } from 'react'
import { LayoutGrid, RefreshCw, AlertCircle, Wifi, WifiOff } from 'lucide-react'
import axios from 'axios'

// Signal colors and styles
const getSignalStyle = (signal) => {
  if (signal === 'HOLD') {
    return {
      bg: 'bg-signal-green/20',
      text: 'text-signal-green',
      border: 'border-signal-green',
      label: 'HOLD',
    }
  }
  if (signal === 'WATCH') {
    return {
      bg: 'bg-signal-amber/20',
      text: 'text-signal-amber',
      border: 'border-signal-amber',
      label: 'WATCH',
    }
  }
  if (signal === 'SELL NOW') {
    return {
      bg: 'bg-signal-red/20',
      text: 'text-signal-red',
      border: 'border-signal-red',
      label: 'SELL NOW',
    }
  }
  return {
    bg: 'bg-gray-500/20',
    text: 'text-gray-400',
    border: 'border-gray-500',
    label: 'UNKNOWN',
  }
}

const CROPS = ['Tomato', 'Onion', 'Potato', 'Cabbage', 'Carrot', 'Bean', 'Chilli']
const MANDIS = ['Mysuru', 'Chamarajanagar']

function SignalGrid() {
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [apiConnected, setApiConnected] = useState(false)

  const fetchSignals = async () => {
    setLoading(true)
    try {
      // Try to fetch from real backend API
      const response = await axios.get('/api/signals/all', { timeout: 5000 })
      
      if (Array.isArray(response.data)) {
        const mapped = response.data.map(s => ({
          crop: s.crop,
          mandi: s.mandi,
          signal: s.signal,
          confidence: s.confidence || 0,
          price: s.current_price || s.expected_price || 0,
          change: s.price_change_pct || 0,
          expectedPrice: s.expected_price || 0,
          reason: s.reason || '',
        }))
        setSignals(mapped)
        setApiConnected(true)
      }
      setLastUpdated(new Date())
    } catch (error) {
      console.warn('API not available, using fallback data:', error.message)
      setApiConnected(false)
      // Fallback to generated data
      const fallback = []
      for (const crop of CROPS) {
        for (const mandi of MANDIS) {
          try {
            const res = await axios.get(`/api/signal/${crop}/${mandi}`, { timeout: 3000 })
            fallback.push({
              crop: res.data.crop,
              mandi: res.data.mandi,
              signal: res.data.signal,
              confidence: res.data.confidence || 0,
              price: res.data.current_price || res.data.expected_price || 0,
              change: res.data.price_change_pct || 0,
              expectedPrice: res.data.expected_price || 0,
              reason: res.data.reason || '',
            })
            setApiConnected(true)
          } catch {
            // Individual signal failed, use mock
            const signals = ['HOLD', 'WATCH', 'SELL NOW']
            const sig = signals[Math.floor(Math.random() * 3)]
            const price = 15 + Math.floor(Math.random() * 40)
            fallback.push({
              crop, mandi, signal: sig,
              confidence: 60 + Math.floor(Math.random() * 25),
              price, change: (Math.random() - 0.4) * 20,
              expectedPrice: price * (1 + (Math.random() - 0.3) * 0.2),
              reason: 'Simulated data',
            })
          }
        }
      }
      setSignals(fallback)
      setLastUpdated(new Date())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSignals()
  }, [])

  const getSignal = (crop, mandi) => {
    return signals.find(s => s.crop === crop && s.mandi === mandi)
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <LayoutGrid className="w-6 h-6 text-accent" />
            <span>Signal <span className="text-accent">Grid</span></span>
          </h1>
          <p className="text-gray-400 mt-1">
            Real-time crop price signals across all mandis
          </p>
        </div>
        
        <div className="flex items-center space-x-4 mt-4 md:mt-0">
          {/* API status indicator */}
          <div className="flex items-center space-x-2">
            {apiConnected ? (
              <Wifi className="w-4 h-4 text-signal-green" />
            ) : (
              <WifiOff className="w-4 h-4 text-signal-amber" />
            )}
            <span className={`text-xs ${apiConnected ? 'text-signal-green' : 'text-signal-amber'}`}>
              {apiConnected ? 'Live API' : 'Offline Mode'}
            </span>
          </div>
          
          {lastUpdated && (
            <span className="text-sm text-gray-500">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={fetchSignals}
            disabled={loading}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="card mb-6">
        <div className="flex flex-wrap items-center space-x-6">
          <span className="text-sm text-gray-400">Signal Legend:</span>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-signal-green"></span>
            <span className="text-sm text-gray-300">HOLD</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-signal-amber"></span>
            <span className="text-sm text-gray-300">WATCH</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-signal-red"></span>
            <span className="text-sm text-gray-300">SELL NOW</span>
          </div>
        </div>
      </div>

      {/* Signal Grid Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-border">
                <th className="text-left text-sm font-medium text-gray-400 px-4 py-3">
                  Crop / Mandi
                </th>
                {MANDIS.map(mandi => (
                  <th key={mandi} className="text-center text-sm font-medium text-gray-400 px-4 py-3">
                    {mandi}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CROPS.map(crop => (
                <tr key={crop} className="border-b border-dark-border hover:bg-dark-border/30">
                  <td className="px-4 py-3 font-medium text-white">
                    {crop}
                  </td>
                  {MANDIS.map(mandi => {
                    const signalData = getSignal(crop, mandi)
                    const style = getSignalStyle(signalData?.signal)
                    
                    return (
                      <td key={mandi} className="px-4 py-3">
                        {signalData ? (
                          <div className={`inline-flex flex-col items-center px-3 py-2 rounded-lg border ${style.bg} ${style.border}`}>
                            <span className={`text-sm font-bold ${style.text}`}>
                              {style.label}
                            </span>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className="text-xs text-gray-400">
                                ₹{Math.round(signalData.price)}/kg
                              </span>
                              <span className={`text-xs ${signalData.change >= 0 ? 'text-signal-green' : 'text-signal-red'}`}>
                                {signalData.change >= 0 ? '+' : ''}{Number(signalData.change).toFixed(1)}%
                              </span>
                            </div>
                            <span className="text-xs text-gray-500 mt-1">
                              {Math.round(signalData.confidence)}% conf.
                            </span>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center text-gray-500">
                            <AlertCircle className="w-4 h-4" />
                          </div>
                        )}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-signal-green/20 flex items-center justify-center">
              <span className="text-signal-green text-lg">✓</span>
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                {signals.filter(s => s.signal === 'HOLD').length}
              </p>
              <p className="text-sm text-gray-400">HOLD Signals</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-signal-amber/20 flex items-center justify-center">
              <span className="text-signal-amber text-lg">⏱</span>
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                {signals.filter(s => s.signal === 'WATCH').length}
              </p>
              <p className="text-sm text-gray-400">WATCH Signals</p>
            </div>
          </div>
        </div>
        
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-signal-red/20 flex items-center justify-center">
              <span className="text-signal-red text-lg">↓</span>
            </div>
            <div>
              <p className="text-2xl font-bold text-white">
                {signals.filter(s => s.signal === 'SELL NOW').length}
              </p>
              <p className="text-sm text-gray-400">SELL NOW Signals</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SignalGrid
