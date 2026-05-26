'use client';
import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

export const GraphVisualization: React.FC = () => {
  const [mounted, setMounted] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const containerRef = React.useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight
      });
    }
  }, []);

  const graphData = {
    nodes: [
      { id: "CUST-8422", group: 1, val: 20, name: "At-Risk Hub" },
      { id: "n1", group: 2, val: 5, name: "Peer Node" },
      { id: "n2", group: 2, val: 5, name: "Peer Node" },
      { id: "n3", group: 2, val: 5, name: "Peer Node" },
      { id: "n4", group: 2, val: 8, name: "Vendor" },
      { id: "n5", group: 2, val: 5, name: "Peer Node" },
      { id: "n6", group: 2, val: 5, name: "Dependent" },
    ],
    links: [
      { source: "CUST-8422", target: "n1" },
      { source: "CUST-8422", target: "n2" },
      { source: "CUST-8422", target: "n3" },
      { source: "n4", target: "CUST-8422" },
      { source: "n5", target: "CUST-8422" },
      { source: "n1", target: "n2" },
      { source: "CUST-8422", target: "n6" },
    ]
  };

  return (
    <div className="bg-[#12121A]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl relative h-full flex flex-col min-h-[400px]">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500"></div>
      
      <div className="mb-4">
        <h3 className="text-xl font-bold text-white">Network Influence (PageRank)</h3>
        <p className="text-xs text-slate-400 mt-1">Simulated graph intelligence to prevent churn cascades.</p>
      </div>
      
      <div ref={containerRef} className="flex-grow w-full rounded-xl overflow-hidden border border-white/5 relative bg-black/40">
        {!mounted ? (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm">
            Loading visualization...
          </div>
        ) : (
          <ForceGraph2D
            graphData={graphData}
            width={dimensions.width || 500}
            height={dimensions.height || 300}
            nodeLabel="name"
            nodeColor={node => node.id === "CUST-8422" ? "#ef4444" : "#3b82f6"}
            linkColor={() => "rgba(255,255,255,0.2)"}
            backgroundColor="transparent"
            nodeRelSize={4}
          />
        )}
      </div>
    </div>
  );
};
