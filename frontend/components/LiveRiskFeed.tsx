import React, { useState, useEffect } from 'react';

type RiskEvent = {
  id: string;
  customerId: string;
  segment: string;
  churnProb: number;
  expectedProfit: number;
  timestamp: string;
};

export const LiveRiskFeed: React.FC = () => {
  const [events, setEvents] = useState<RiskEvent[]>([]);

  // Simulate incoming events for the MVP dashboard
  useEffect(() => {
    // Initial events
    setEvents([
      { id: '1', customerId: 'CUST-8422', segment: 'Salaried', churnProb: 0.88, expectedProfit: 4500, timestamp: new Date(Date.now() - 10000).toLocaleTimeString() },
      { id: '2', customerId: 'CUST-1934', segment: 'MSME', churnProb: 0.95, expectedProfit: 12500, timestamp: new Date(Date.now() - 25000).toLocaleTimeString() }
    ]);

    const interval = setInterval(() => {
      const newEvent: RiskEvent = {
        id: Math.random().toString(36).substr(2, 9),
        customerId: `CUST-${Math.floor(Math.random() * 10000)}`,
        segment: ['Salaried', 'MSME', 'Student', 'HNI', 'Jan Dhan'][Math.floor(Math.random() * 5)],
        churnProb: 0.6 + (Math.random() * 0.35),
        expectedProfit: Math.floor(Math.random() * 15000),
        timestamp: new Date().toLocaleTimeString(),
      };
      setEvents(prev => [newEvent, ...prev].slice(0, 5));
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-[#12121A]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-orange-500"></div>
      
      <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.7)]"></span>
        Live Risk Signals
      </h3>
      
      <div className="space-y-3">
        {events.map(ev => (
          <div key={ev.id} className="bg-white/5 rounded-xl p-4 border border-white/5 hover:border-white/20 hover:bg-white/10 transition-all cursor-default group">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm font-semibold text-white group-hover:text-blue-400 transition-colors">{ev.customerId}</p>
                <p className="text-xs text-slate-400 mt-1">{ev.segment}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-bold text-red-400">Risk: {(ev.churnProb * 100).toFixed(1)}%</p>
                <p className="text-xs font-medium text-emerald-400 mt-1">+₹{ev.expectedProfit.toLocaleString()} EV</p>
              </div>
            </div>
            <div className="mt-3 flex justify-between items-center text-[10px] text-slate-500">
              <span>{ev.timestamp}</span>
              <button className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 hover:bg-blue-500/40 transition-colors">
                Run Intervention
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
