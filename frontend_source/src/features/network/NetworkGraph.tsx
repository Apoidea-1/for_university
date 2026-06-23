import { useCallback, useMemo, useRef, useState } from "react";

import type { NetworkGraphData, NetworkGraphNode } from "@/types/api";
import { useTheme } from "@/hooks/useTheme";

const VW = 920;
const VH = 560;
const DRAG_THRESHOLD = 5; // SVG units — below this a mousedown+up is a click

function shortLabel(label: string) {
  const parts = label.split(" ").filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 12);
  return `${parts[0]} ${parts[1][0] ?? ""}.`.trim();
}

function toKey(id: number | "user") {
  return typeof id === "number" ? String(id) : id;
}

const STATUS_GLOW: Record<string, string> = {
  active:  "rgba(20,184,166,0.75)",
  target:  "rgba(245,158,11,0.75)",
  dormant: "rgba(244,63,94,0.75)",
};

const FILTER_ID: Record<string, string> = {
  active:  "glow-teal",
  target:  "glow-amber",
  dormant: "glow-rose",
};

export function NetworkGraph({
  data,
  onContactClick,
}: {
  data: NetworkGraphData;
  onContactClick?: (id: number) => void;
}) {
  const { theme } = useTheme();
  const isCream = theme === "cream";

  const c = useMemo(() => ({
    bg:           isCream ? "#ede8de"                 : "#08101d",
    gridStroke:   isCream ? "rgba(140,100,50,0.06)"   : "rgba(255,255,255,0.025)",
    bgGlowStop:   isCream ? "rgba(237,232,222,0)"     : "rgba(8,16,29,0)",
    nodeLabel:    isCream ? "#2d2016"                 : "#e2e8f0",
    nodeStroke:         isCream ? "rgba(60,30,10,0.18)"   : "rgba(255,255,255,0.14)",
    nodeStrokeHot:      isCream ? "rgba(60,30,10,0.65)"   : "rgba(255,255,255,0.65)",
    tooltipBg:    isCream ? "rgba(253,248,240,0.97)"  : "rgba(4,17,29,0.95)",
    tooltipText:  isCream ? "#0f766e"                 : "#14b8a6",
    linkDim:      isCream ? "rgba(100,70,30,0.06)"    : "rgba(148,163,184,0.05)",
    linkUser:     isCream ? "rgba(20,184,166,0.45)"   : "rgba(20,184,166,0.38)",
    linkUserHot:  isCream ? "rgba(20,184,166,0.85)"   : "rgba(20,184,166,0.8)",
    linkOther:    isCream ? "rgba(20,184,166,0.28)"   : "rgba(20,184,166,0.22)",
    linkOtherHot: isCream ? "rgba(20,184,166,0.65)"   : "rgba(20,184,166,0.6)",
  }), [isCream]);

  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredKey, setHoveredKey] = useState<string | null>(null);
  const [offsets, setOffsets] = useState<Map<string, { dx: number; dy: number }>>(new Map());
  const [drag, setDrag] = useState<{
    key: string;
    startSvgX: number;
    startSvgY: number;
    baseDx: number;
    baseDy: number;
    moved: boolean; // true once pointer moved beyond DRAG_THRESHOLD
  } | null>(null);

  const baseLayout = useMemo(() => {
    const cx = VW / 2;  // 460
    const cy = VH / 2;  // 280
    const map = new Map<string, { x: number; y: number; node: NetworkGraphNode }>();

    const userNode = data.nodes.find((n) => n.id === "user");
    if (userNode) map.set("user", { x: cx, y: cy, node: userNode });

    // Simple circular layout: sort by status, spread evenly around center.
    // This guarantees all nodes stay within the viewBox regardless of count.
    const nonUser = data.nodes
      .filter((n) => n.id !== "user")
      .sort((a, b) => {
        const order = { active: 0, target: 1, dormant: 2 };
        return (order[a.status as keyof typeof order] ?? 3) - (order[b.status as keyof typeof order] ?? 3);
      });

    if (nonUser.length === 0) return map;

    // Distribute evenly on a circle. Start from top (-90° = 270°) so the
    // first node appears at the top and they fan out clockwise.
    nonUser.forEach((node, i) => {
      const angleDeg = -90 + (360 / nonUser.length) * i;
      const angle = (angleDeg * Math.PI) / 180;
      // Radius scales with canvas to keep nodes well inside bounds.
      // For 1 node: r=190; for many nodes: r stays ~180-200 (canvas is 920×560,
      // so max safe r is min(460,280)*0.7 ≈ 196).
      const baseR = Math.min(185, 140 + 30 / Math.max(nonUser.length, 1));
      const r = baseR + Math.min(node.degree * 4, 20);
      map.set(toKey(node.id), {
        x: cx + Math.cos(angle) * r,
        y: cy + Math.sin(angle) * r,
        node,
      });
    });

    return map;
  }, [data]);

  const toSvgCoords = useCallback((clientX: number, clientY: number) => {
    const el = svgRef.current;
    if (!el) return { x: 0, y: 0 };
    const rect = el.getBoundingClientRect();
    return {
      x: ((clientX - rect.left) / rect.width) * VW,
      y: ((clientY - rect.top) / rect.height) * VH,
    };
  }, []);

  const handleNodeMouseDown = useCallback(
    (e: React.MouseEvent, key: string) => {
      e.stopPropagation();
      e.preventDefault();
      const { x, y } = toSvgCoords(e.clientX, e.clientY);
      const base = offsets.get(key) ?? { dx: 0, dy: 0 };
      setDrag({ key, startSvgX: x, startSvgY: y, baseDx: base.dx, baseDy: base.dy, moved: false });
      setHoveredKey(null);
    },
    [offsets, toSvgCoords],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      if (!drag) return;
      const { x, y } = toSvgCoords(e.clientX, e.clientY);
      const dx = drag.baseDx + (x - drag.startSvgX);
      const dy = drag.baseDy + (y - drag.startSvgY);
      const moved =
        drag.moved ||
        Math.abs(x - drag.startSvgX) > DRAG_THRESHOLD ||
        Math.abs(y - drag.startSvgY) > DRAG_THRESHOLD;
      setDrag((prev) => (prev ? { ...prev, moved } : null));
      if (moved) {
        setOffsets((prev) => {
          const next = new Map(prev);
          next.set(drag.key, { dx, dy });
          return next;
        });
      }
    },
    [drag, toSvgCoords],
  );

  const stopDrag = useCallback(
    (e: React.MouseEvent<SVGSVGElement>) => {
      if (!drag) return;
      // If pointer barely moved — treat as a click, navigate to contact
      if (!drag.moved && drag.key !== "user" && onContactClick) {
        const numericId = Number(drag.key);
        if (!isNaN(numericId)) onContactClick(numericId);
      }
      setDrag(null);
    },
    [drag, onContactClick],
  );

  const getPos = useCallback(
    (key: string) => {
      const base = baseLayout.get(key);
      if (!base) return null;
      const off = offsets.get(key) ?? { dx: 0, dy: 0 };
      return { x: base.x + off.dx, y: base.y + off.dy, node: base.node };
    },
    [baseLayout, offsets],
  );

  const connectedToHovered = useMemo(() => {
    if (!hoveredKey) return new Set<string>();
    const set = new Set<string>();
    data.links.forEach((link) => {
      const s = toKey(link.source);
      const t = toKey(link.target);
      if (s === hoveredKey) set.add(t);
      if (t === hoveredKey) set.add(s);
    });
    return set;
  }, [hoveredKey, data.links]);

  return (
    <div className="space-y-4">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${VW} ${VH}`}
        className="h-[560px] w-full rounded-3xl"
        style={{ background: c.bg, cursor: drag ? "grabbing" : "default" }}
        onMouseMove={handleMouseMove}
        onMouseUp={stopDrag}
        onMouseLeave={() => setDrag(null)}
      >
        <defs>
          {(["teal", "amber", "rose"] as const).map((name) => (
            <filter key={name} id={`glow-${name}`} x="-60%" y="-60%" width="220%" height="220%">
              <feGaussianBlur stdDeviation={name === "amber" ? "6" : "5"} result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          ))}
          <filter id="glow-you" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="10" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="glow-link" x="-20%" y="-200%" width="140%" height="500%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <radialGradient id="bgGlow" cx="50%" cy="50%" r="55%">
            <stop offset="0%" stopColor="rgba(20,184,166,0.1)" />
            <stop offset="65%" stopColor="rgba(20,184,166,0.03)" />
            <stop offset="100%" stopColor={c.bgGlowStop} />
          </radialGradient>
          <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
            <path d="M 48 0 L 0 0 0 48" fill="none" stroke={c.gridStroke} strokeWidth="1" />
          </pattern>

          <style>{`
            @keyframes np-pulse {
              0%   { r: 4;  opacity: 0.7; }
              100% { r: 30; opacity: 0;   }
            }
            @keyframes np-ping1 {
              0%   { r: 24; opacity: 0.45; }
              100% { r: 62; opacity: 0;    }
            }
            @keyframes np-ping2 {
              0%   { r: 24; opacity: 0.22; }
              100% { r: 78; opacity: 0;    }
            }
            @keyframes np-flow {
              to { stroke-dashoffset: -12; }
            }
            @keyframes np-orbit {
              to { stroke-dashoffset: -36; }
            }
            @keyframes np-shimmer {
              0%, 100% { opacity: 0.45; }
              50%       { opacity: 0.9;  }
            }
            /* Scale animation on a CHILD group so it doesn't conflict with
               the parent SVG transform="translate(x,y)" attribute. */
            @keyframes np-enter {
              0%   { opacity: 0; transform: scale(0.15); }
              65%  {             transform: scale(1.12); }
              100% { opacity: 1; transform: scale(1);    }
            }
            .np-anim-inner {
              animation: np-enter 0.55s cubic-bezier(.34,1.56,.64,1) both;
              transform-origin: 0 0;
            }
            .np-flow   { stroke-dasharray: 6 5; animation: np-flow   1.6s linear infinite; }
            .np-flow-s { stroke-dasharray: 4 6; animation: np-flow   2.6s linear infinite; }
            .np-pulse  { animation: np-pulse   2.2s ease-out   infinite; }
            .np-ping1  { animation: np-ping1   2.8s ease-out   infinite; }
            .np-ping2  { animation: np-ping2   2.8s ease-out 1.4s infinite; }
            .np-orbit  { animation: np-orbit   3s   linear     infinite; }
            .np-shimmer{ animation: np-shimmer 2.2s ease-in-out infinite; }
          `}</style>
        </defs>

        {/* Background */}
        <rect width={VW} height={VH} fill={c.bg} rx="24" />
        <rect width={VW} height={VH} fill="url(#grid)" rx="24" />
        <ellipse cx={VW / 2} cy={VH / 2} rx={340} ry={260} fill="url(#bgGlow)" />

        {/* Links */}
        {data.links.map((link, i) => {
          const src = getPos(toKey(link.source));
          const tgt = getPos(toKey(link.target));
          if (!src || !tgt) return null;
          const sk = toKey(link.source);
          const tk = toKey(link.target);
          const isHot = hoveredKey != null && (sk === hoveredKey || tk === hoveredKey);
          const isDim = hoveredKey != null && !isHot;
          const w = Math.max(1.2, Math.min(link.weight, 5));
          const isUserLink = link.kind === "user_contact";
          return (
            <line
              key={`${sk}-${tk}-${link.kind}`}
              x1={src.x} y1={src.y}
              x2={tgt.x} y2={tgt.y}
              stroke={
                isDim        ? c.linkDim
                : isHot      ? (isUserLink ? c.linkUserHot : c.linkOtherHot)
                : isUserLink ? c.linkUser
                :              c.linkOther
              }
              strokeWidth={isHot ? w + 1.2 : w}
              strokeLinecap="round"
              filter={isHot ? "url(#glow-link)" : undefined}
              className={isUserLink ? "np-flow" : "np-flow-s"}
              style={{ animationDelay: `${i * 0.18}s`, transition: "stroke 0.22s, stroke-width 0.22s" }}
            />
          );
        })}

        {/* Nodes
            IMPORTANT: outer <g> carries only SVG transform="translate(x,y)" — NO className with CSS transform.
            Inner <g className="np-anim-inner"> carries the scale animation so they don't conflict. */}
        {Array.from(baseLayout.keys()).map((key, idx) => {
          const pos = getPos(key);
          if (!pos) return null;
          const { node } = pos;
          const isUser = node.id === "user";
          const isDim = hoveredKey != null ? key !== hoveredKey && !connectedToHovered.has(key) : false;
          const isHot = hoveredKey === key;
          const isDraggingThis = drag?.key === key;
          const filterId = isUser ? "glow-you" : (FILTER_ID[node.status] ?? "glow-teal");

          return (
            <g
              key={key}
              transform={`translate(${pos.x}, ${pos.y})`}
              style={{
                opacity: isDim ? 0.15 : 1,
                transition: "opacity 0.25s",
                cursor: isDraggingThis ? "grabbing" : isUser ? "default" : "pointer",
              }}
              onMouseEnter={() => { if (!drag) setHoveredKey(key); }}
              onMouseLeave={() => { if (!drag) setHoveredKey(null); }}
              onMouseDown={(e) => handleNodeMouseDown(e, key)}
            >
              {/* Inner group — CSS scale animation lives here, isolated from parent translate */}
              <g
                className="np-anim-inner"
                style={{ animationDelay: `${idx * 65}ms` }}
              >
                {/* YOU double ping */}
                {isUser && (
                  <>
                    <circle r={24} fill="none" stroke="rgba(20,184,166,0.35)" strokeWidth={1.2} className="np-ping1" />
                    <circle r={24} fill="none" stroke="rgba(20,184,166,0.2)"  strokeWidth={1}   className="np-ping2" />
                  </>
                )}

                {/* Bridge orbit ring */}
                {node.is_bridge && !isUser && (
                  <circle
                    r={node.size + 11}
                    fill="none"
                    stroke="rgba(245,158,11,0.6)"
                    strokeWidth={1.5}
                    strokeDasharray="6 4"
                    className="np-orbit np-shimmer"
                  />
                )}

                {/* Status pulse ring */}
                {!isUser && (
                  <circle
                    r={node.size}
                    fill="none"
                    stroke={STATUS_GLOW[node.status] ?? "rgba(20,184,166,0.6)"}
                    strokeWidth={1.5}
                    className="np-pulse"
                    style={{ animationDelay: `${idx * 0.28}s` }}
                  />
                )}

                {/* Main circle */}
                <circle
                  r={node.size}
                  fill={node.color}
                  stroke={isUser ? "#14b8a6" : isHot ? c.nodeStrokeHot : c.nodeStroke}
                  strokeWidth={isUser ? 3 : isHot ? 2.5 : 1.4}
                  filter={`url(#${filterId})`}
                  style={{ transition: "stroke 0.2s, stroke-width 0.2s" }}
                />

                {/* Label */}
                <text
                  y={isUser ? 4 : node.size + 18}
                  textAnchor="middle"
                  fill={isUser ? "#04111d" : c.nodeLabel}
                  fontSize={11}
                  fontWeight={isUser ? 800 : 600}
                  style={{ pointerEvents: "none", userSelect: "none" }}
                >
                  {isUser ? "YOU" : shortLabel(node.label)}
                </text>

                {/* Hover tooltip */}
                {isHot && !isUser && !drag && (
                  <g transform={`translate(0, ${-(node.size + 18)})`}>
                    <rect x={-60} y={-22} width={120} height={26} rx={7} fill={c.tooltipBg} stroke="rgba(20,184,166,0.45)" strokeWidth={1} />
                    <text textAnchor="middle" y={-5} fill={c.tooltipText} fontSize={10} fontWeight={700} style={{ pointerEvents: "none" }}>
                      {node.label}
                    </text>
                  </g>
                )}
              </g>

              <title>{`${node.label} • ${node.status} • degree ${node.degree}`}</title>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
        {(
          [
            { color: "#14b8a6", label: "Активные" },
            { color: "#f59e0b", label: "Целевые" },
            { color: "#f43f5e", label: "Спящие" },
          ] as const
        ).map(({ color, label }) => (
          <div key={label} className="flex items-center gap-2">
            <span className="relative flex h-3 w-3 shrink-0 items-center justify-center">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-50" style={{ backgroundColor: color }} />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
            </span>
            {label}
          </div>
        ))}
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 shrink-0 rounded-full border border-dashed border-[#f59e0b] bg-transparent" />
          Bridge-контакты
        </div>
        <span className="ml-auto text-slate-500">Перетащите узлы для перемещения</span>
      </div>
    </div>
  );
}
