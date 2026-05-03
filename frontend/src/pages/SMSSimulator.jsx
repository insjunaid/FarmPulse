import React, { useState, useEffect } from 'react'
import { MessageSquare, Send, Phone, RefreshCw, CheckCircle, AlertCircle, Loader, Wifi, WifiOff } from 'lucide-react'
import axios from 'axios'

// Kannada action texts
const KANNADA_ACTIONS = {
  'HOLD': 'ತಡೆಹಿಡಿರಿ - ದರ ಏರಿಕೆ ನಿರೀಕ್ಷೆ',
  'WATCH': 'ನೋಡುತ್ತಿರಿ - ದರ ಬದಲಾವಣೆ ನೋಡಿ',
  'SELL NOW': 'ಈಗಲೇ ಮಾರಿಸಿ - ದರ ಕುಸಿತ',
}

// Generate SMS message for a farmer
const generateSMS = (farmer, signalData) => {
  const date = new Date()
  date.setDate(date.getDate() + 3)
  const dateStr = date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  const action = KANNADA_ACTIONS[signalData.signal] || 'ನೋಡುತ್ತಿರಿ'
  
  return `FarmPulse Alert | Crop: ${farmer.primaryCrop} | Mandi: ${farmer.preferredMandi} | Signal: ${signalData.signal} | Expected: Rs.${signalData.price}/kg by ${dateStr} | ${action}`
}

function SMSSimulator() {
  const [farmers, setFarmers] = useState([])
  const [selectedFarmer, setSelectedFarmer] = useState(null)
  const [signalData, setSignalData] = useState(null)
  const [smsMessage, setSmsMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [sendResult, setSendResult] = useState(null)
  const [apiConnected, setApiConnected] = useState(false)
  const [smsLogs, setSmsLogs] = useState([])

  useEffect(() => {
    fetchFarmers()
    fetchSmsLogs()
  }, [])

  const fetchFarmers = async () => {
    try {
      const response = await axios.get('/api/farmers', { timeout: 5000 })
      if (Array.isArray(response.data) && response.data.length > 0) {
        const mapped = response.data.map(f => ({
          id: f.id,
          name: f.name,
          phone: f.phone_number,
          district: f.district,
          primaryCrop: f.primary_crop || 'Tomato',
          preferredMandi: f.preferred_mandi || 'Mysuru',
        }))
        setFarmers(mapped)
        setApiConnected(true)
      } else {
        // Use fallback farmer list
        setFarmers([
          { id: 1, name: 'Demo Farmer', phone: '+919353903818', district: 'Mysuru', primaryCrop: 'Tomato', preferredMandi: 'Mysuru' },
        ])
      }
    } catch (error) {
      console.warn('Farmers API not available for SMS:', error.message)
      setApiConnected(false)
      setFarmers([
        { id: 1, name: 'Demo Farmer', phone: '+919353903818', district: 'Mysuru', primaryCrop: 'Tomato', preferredMandi: 'Mysuru' },
      ])
    }
  }

  const fetchSmsLogs = async () => {
    try {
      const response = await axios.get('/api/sms-logs', { timeout: 3000 })
      if (response.data?.logs) {
        setSmsLogs(response.data.logs)
      }
    } catch {
      // Silent fail
    }
  }

  const handleFarmerSelect = async (farmerId) => {
    const farmer = farmers.find(f => f.id === farmerId)
    setSelectedFarmer(farmer)
    setSendResult(null)
    
    if (farmer) {
      // Try to fetch real signal from API
      try {
        const response = await axios.get(`/api/signal/${farmer.primaryCrop}/${farmer.preferredMandi}`, { timeout: 5000 })
        const sig = response.data
        const signal = {
          signal: sig.signal,
          price: sig.expected_price || sig.current_price || 25,
          change: sig.price_change_pct || 0,
          confidence: sig.confidence || 60,
        }
        setSignalData(signal)
        setSmsMessage(generateSMS(farmer, signal))
        setApiConnected(true)
      } catch {
        // Fallback signal
        const fallbackSignal = { signal: 'HOLD', price: 28, change: 12.5, confidence: 78 }
        setSignalData(fallbackSignal)
        setSmsMessage(generateSMS(farmer, fallbackSignal))
      }
    }
  }

  const handleSendSMS = async () => {
    if (!selectedFarmer || !smsMessage) return
    
    setSending(true)
    setSendResult(null)
    
    try {
      // Send via real backend API which calls MSG91
      const expectedDate = new Date()
      expectedDate.setDate(expectedDate.getDate() + 3)
      
      const response = await axios.post('/api/send-sms', {
        phone_number: selectedFarmer.phone,
        crop: selectedFarmer.primaryCrop,
        mandi: selectedFarmer.preferredMandi,
        signal: signalData?.signal || 'HOLD',
        expected_price: signalData?.price || 25,
        expected_date: expectedDate.toISOString().split('T')[0],
        message: smsMessage,
      }, { timeout: 15000 })
      
      const result = response.data
      setApiConnected(true)
      
      setSendResult({
        success: result.success !== false,
        message: result.success !== false 
          ? `SMS sent successfully to ${selectedFarmer.phone}! 🎉` 
          : `SMS failed: ${result.error || 'Unknown error'}`,
        messageId: result.message_id || null,
        apiResponse: result,
      })
      
      // Refresh SMS logs
      fetchSmsLogs()
    } catch (error) {
      console.error('SMS send error:', error)
      setSendResult({
        success: false,
        message: `Failed to send SMS: ${error.response?.data?.detail || error.message}. Make sure the backend is running.`,
      })
    } finally {
      setSending(false)
    }
  }

  const getSignalBadge = (signal) => {
    if (signal === 'HOLD') {
      return <span className="px-3 py-1 rounded-full text-sm font-bold bg-signal-green/20 text-signal-green border border-signal-green">HOLD</span>
    }
    if (signal === 'WATCH') {
      return <span className="px-3 py-1 rounded-full text-sm font-bold bg-signal-amber/20 text-signal-amber border border-signal-amber">WATCH</span>
    }
    if (signal === 'SELL NOW') {
      return <span className="px-3 py-1 rounded-full text-sm font-bold bg-signal-red/20 text-signal-red border border-signal-red">SELL NOW</span>
    }
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <MessageSquare className="w-6 h-6 text-accent" />
            <span>SMS <span className="text-accent">Simulator</span></span>
          </h1>
          <div className="flex items-center space-x-3 mt-1">
            <p className="text-gray-400">
              Send real SMS alerts to farmers via MSG91
            </p>
            <div className="flex items-center space-x-1">
              {apiConnected ? (
                <Wifi className="w-3 h-3 text-signal-green" />
              ) : (
                <WifiOff className="w-3 h-3 text-signal-amber" />
              )}
              <span className={`text-xs ${apiConnected ? 'text-signal-green' : 'text-signal-amber'}`}>
                {apiConnected ? 'Live API' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Farmer Selection */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">
            Select Farmer
          </h2>
          
          <div className="space-y-3">
            {farmers.map(farmer => (
              <button
                key={farmer.id}
                onClick={() => handleFarmerSelect(farmer.id)}
                className={`w-full p-4 rounded-lg border transition-all text-left ${
                  selectedFarmer?.id === farmer.id
                    ? 'bg-accent/10 border-accent'
                    : 'bg-dark-bg border-dark-border hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center">
                      <span className="text-accent font-medium">
                        {farmer.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-white font-medium">{farmer.name}</p>
                      <p className="text-sm text-gray-400">{farmer.phone}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-400">{farmer.primaryCrop}</p>
                    <p className="text-sm text-accent">{farmer.preferredMandi}</p>
                  </div>
                </div>
              </button>
            ))}
            
            {farmers.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <p>No farmers registered yet.</p>
                <p className="text-sm mt-1">Go to Farmer Management to register.</p>
              </div>
            )}
          </div>
        </div>

        {/* SMS Preview */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">
            SMS Preview
          </h2>
          
          {selectedFarmer ? (
            <div className="space-y-4">
              {/* Phone Mockup */}
              <div className="flex justify-center">
                <div className="w-full max-w-sm bg-dark-bg rounded-3xl border-4 border-gray-800 p-4">
                  {/* Phone Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center">
                        <MessageSquare className="w-4 h-4 text-dark-bg" />
                      </div>
                      <div>
                        <p className="text-white text-sm font-medium">FarmPulse</p>
                        <p className="text-gray-500 text-xs">SMS to {selectedFarmer.phone}</p>
                      </div>
                    </div>
                    <span className="text-gray-500 text-xs">now</span>
                  </div>
                  
                  {/* Message */}
                  <div className="bg-dark-card rounded-2xl p-4">
                    <p className="text-white text-sm leading-relaxed whitespace-pre-line">
                      {smsMessage || 'Select a farmer to preview SMS'}
                    </p>
                  </div>
                  
                  {/* Signal Badge */}
                  {signalData && (
                    <div className="flex justify-center mt-4">
                      {getSignalBadge(signalData.signal)}
                    </div>
                  )}
                  
                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-2 mt-4">
                    <div className="bg-dark-card rounded-lg p-2 text-center">
                      <p className="text-gray-500 text-xs">Expected Price</p>
                      <p className="text-white font-bold">₹{signalData?.price || 0}/kg</p>
                    </div>
                    <div className="bg-dark-card rounded-lg p-2 text-center">
                      <p className="text-gray-500 text-xs">Confidence</p>
                      <p className="text-accent font-bold">{signalData?.confidence || 0}%</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Send Result */}
              {sendResult && (
                <div className={`p-4 rounded-lg flex items-start space-x-2 ${
                  sendResult.success 
                    ? 'bg-signal-green/20 border border-signal-green'
                    : 'bg-signal-red/20 border border-signal-red'
                }`}>
                  {sendResult.success ? (
                    <CheckCircle className="w-5 h-5 text-signal-green flex-shrink-0 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-signal-red flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <p className={sendResult.success ? 'text-signal-green' : 'text-signal-red'}>
                      {sendResult.message}
                    </p>
                    {sendResult.success && sendResult.messageId && (
                      <p className="text-sm text-gray-400 mt-1">Message ID: {sendResult.messageId}</p>
                    )}
                  </div>
                </div>
              )}
              
              {/* Send Button */}
              <button
                onClick={handleSendSMS}
                disabled={sending || !smsMessage}
                className={`btn-primary w-full flex items-center justify-center space-x-2 ${
                  sending ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                {sending ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    <span>Sending via MSG91...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Send Real SMS via MSG91</span>
                  </>
                )}
              </button>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <Phone className="w-12 h-12 mb-4" />
              <p>Select a farmer to preview SMS</p>
            </div>
          )}
        </div>
      </div>

      {/* SMS History */}
      {smsLogs.length > 0 && (
        <div className="card mt-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            SMS History (This Session)
          </h2>
          <div className="space-y-3">
            {smsLogs.slice().reverse().map((log, i) => (
              <div key={i} className="bg-dark-bg rounded-lg p-3 border border-dark-border">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-400">To: {log.phone_number}</p>
                    <p className="text-sm text-white mt-1">{log.message}</p>
                  </div>
                  <span className="text-xs text-gray-500">{new Date(log.sent_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Message Format Info */}
      <div className="card mt-6">
        <h2 className="text-lg font-semibold text-white mb-4">
          SMS Format
        </h2>
        <div className="bg-dark-bg rounded-lg p-4 font-mono text-sm text-gray-300">
          <p>FarmPulse Alert | Crop: [crop] | Mandi: [mandi] | Signal: [HOLD/WATCH/SELL NOW] | Expected: Rs.[price]/kg by [date] | [action in Kannada]</p>
        </div>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-signal-green/10 border border-signal-green rounded-lg p-3">
            <p className="text-signal-green font-medium text-sm">HOLD (ತಡೆಹಿಡಿರಿ)</p>
            <p className="text-gray-400 text-xs mt-1">Price expected to rise - hold for better returns</p>
          </div>
          <div className="bg-signal-amber/10 border border-signal-amber rounded-lg p-3">
            <p className="text-signal-amber font-medium text-sm">WATCH (ನೋಡುತ್ತಿರಿ)</p>
            <p className="text-gray-400 text-xs mt-1">Price may change - monitor closely</p>
          </div>
          <div className="bg-signal-red/10 border border-signal-red rounded-lg p-3">
            <p className="text-signal-red font-medium text-sm">SELL NOW (ಈಗಲೇ ಮಾರಿಸಿ)</p>
            <p className="text-gray-400 text-xs mt-1">Price expected to drop - sell now to avoid loss</p>
          </div>
        </div>
      </div>

      {/* Kannada Translations */}
      <div className="card mt-6">
        <h2 className="text-lg font-semibold text-white mb-4">
          Kannada Translations
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <p className="text-gray-400 text-sm">Tomato = ಟೊಮಾಟೊ</p>
            <p className="text-gray-400 text-sm">Onion = ಈರುಳ್ಳಿ</p>
            <p className="text-gray-400 text-sm">Potato = ಆಲೂಗಡ್ಡೆ</p>
            <p className="text-gray-400 text-sm">Cabbage = ಎಲೆಕೋಸು</p>
            <p className="text-gray-400 text-sm">Chilli = ಮೆಣಸಿನಕಾಯಿ</p>
          </div>
          <div className="space-y-2">
            <p className="text-gray-400 text-sm">Mysuru = ಮೈಸೂರು</p>
            <p className="text-gray-400 text-sm">Chamarajanagar = ಚಾಮರಾಜನಗರ</p>
            <p className="text-gray-400 text-sm">Hold = ತಡೆಹಿಡಿರಿ</p>
            <p className="text-gray-400 text-sm">Watch = ನೋಡುತ್ತಿರಿ</p>
            <p className="text-gray-400 text-sm">Sell Now = ಈಗಲೇ ಮಾರಿಸಿ</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SMSSimulator
