import React from 'react';

export const FinancialImpactMap: React.FC = () => {
  // Static representation for MVP
  const metrics = [
    { label: "Total LTV at Risk", value: "₹4.2M", trend: "+12%", trendColor: "text-red-400" },
    { label: "Saved Expected Value", value: "₹1.8M", trend: "+24%", trendColor: "text-emerald-400" },
    { label: "Intervention ROI", value: "340%", trend: "+15%", trendColor: "text-emerald-400" },
  ];

  return (
    <div className="bg-[#12121A]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl relative">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-teal-500"></div>
      
      <h3 className="text-xl font-bold text-white mb-6">Financial Impact Map</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {metrics.map((m, i) => (
          <div key={i} className="bg-black/40 rounded-xl p-4 border border-white/5 flex flex-col justify-between">
            <span className="text-xs text-slate-400">{m.label}</span>
            <div className="mt-2 flex items-end justify-between">
              <span className="text-2xl font-bold text-white">{m.value}</span>
              <span className={`text-xs font-semibold ${m.trendColor}`}>{m.trend}</span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-emerald-400">Guardrail Status</span>
          <span className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded-full">Active</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          Strategy Agent is enforcing positive expected profit: <br/>
          <code className="text-xs text-emerald-300 bg-black/30 px-1 py-0.5 rounded mt-1 inline-block">Expected Profit = (P(Retain) × LTV) − Cost &gt; 0</code>
        </p>
      </div>
    </div>
  );
};
