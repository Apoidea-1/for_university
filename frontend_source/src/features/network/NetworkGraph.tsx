import { useMemo } from "react";

import type { NetworkGraphData, NetworkGraphNode } from "@/types/api";

function shortLabel(label: string) {
  const parts = label.split(" ").filter(Boolean);
  if (parts.length === 1) {
    return parts[0].slice(0, 12);
  }
  return `${parts[0]} ${parts[1][0] ?? ""}.`.trim();
}

function toKey(id: number | "user") {
  return typeof id === "number" ? String(id) : id;
}

export function NetworkGraph({ data }: { data: NetworkGraphData }) {
  const layout = useMemo(() => {
    const width = 920;
    const height = 560;
    const centerX = width / 2;
    const centerY = height / 2;
    const positions = new Map<string, { x: number; y: number; node: NetworkGraphNode }>();

    const userNode = data.nodes.find((node) => node.id === "user");
    if (userNode) {
      positions.set("user", { x: centerX, y: centerY, node: userNode });
    }

    const ranges: Record<"active" | "target" | "dormant", { start: number; end: number; radius: number }> = {
      active: { start: -135, end: -15, radius: 170 },
      target: { start: 15, end: 155, radius: 235 },
      dormant: { start: 165, end: 335, radius: 300 },
    };

    (["active", "target", "dormant"] as const).forEach((status) => {
      const nodes = data.nodes
        .filter((node) => node.status === status)
        .sort((left, right) => right.degree - left.degree || left.label.localeCompare(right.label));
      if (!nodes.length) {
        return;
      }
      const range = ranges[status];
      nodes.forEach((node, index) => {
        const ratio = nodes.length === 1 ? 0.5 : index / (nodes.length - 1);
        const angle = ((range.start + (range.end - range.start) * ratio) * Math.PI) / 180;
        const radius = range.radius + Math.min(node.degree * 6, 32);
        positions.set(toKey(node.id), {
          x: centerX + Math.cos(angle) * radius,
          y: centerY + Math.sin(angle) * radius,
          node,
        });
      });
    });

    return { width, height, positions };
  }, [data]);

  return (
    <div className="space-y-4">
      <svg viewBox={`0 0 ${layout.width} ${layout.height}`} className="h-[560px] w-full rounded-3xl bg-[#08101d]">
        <defs>
          <radialGradient id="graphGlow" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stopColor="rgba(20,184,166,0.18)" />
            <stop offset="100%" stopColor="rgba(8,16,29,0)" />
          </radialGradient>
        </defs>

        <rect width={layout.width} height={layout.height} fill="#08101d" />
        <ellipse cx={layout.width / 2} cy={layout.height / 2} rx={280} ry={220} fill="url(#graphGlow)" />

        {data.links.map((link) => {
          const source = layout.positions.get(toKey(link.source));
          const target = layout.positions.get(toKey(link.target));
          if (!source || !target) {
            return null;
          }
          return (
            <line
              key={`${toKey(link.source)}-${toKey(link.target)}-${link.kind}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke={link.kind === "user_contact" ? "rgba(148, 163, 184, 0.24)" : "rgba(20, 184, 166, 0.46)"}
              strokeWidth={Math.max(1.2, Math.min(link.weight, 5))}
              strokeLinecap="round"
            />
          );
        })}

        {Array.from(layout.positions.values()).map(({ x, y, node }) => (
          <g key={toKey(node.id)} transform={`translate(${x}, ${y})`}>
            {node.is_bridge ? (
              <circle r={node.size + 8} fill="rgba(245, 158, 11, 0.08)" stroke="rgba(245, 158, 11, 0.45)" strokeDasharray="5 4" />
            ) : null}
            <circle
              r={node.size}
              fill={node.color}
              stroke={node.id === "user" ? "#14b8a6" : "rgba(255,255,255,0.12)"}
              strokeWidth={node.id === "user" ? 3 : 1.4}
            />
            <text
              y={node.id === "user" ? 4 : node.size + 18}
              textAnchor="middle"
              fill={node.id === "user" ? "#04111d" : "#e2e8f0"}
              fontSize={node.id === "user" ? 11 : 11}
              fontWeight={node.id === "user" ? 800 : 600}
            >
              {node.id === "user" ? "YOU" : shortLabel(node.label)}
            </text>
            <title>{`${node.label} • ${node.status} • degree ${node.degree}`}</title>
          </g>
        ))}
      </svg>

      <div className="flex flex-wrap gap-3 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-[#14b8a6]" />
          Активные
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-[#f59e0b]" />
          Целевые
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-[#f43f5e]" />
          Спящие
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full border border-dashed border-[#f59e0b] bg-transparent" />
          Bridge-контакты
        </div>
      </div>
    </div>
  );
}
