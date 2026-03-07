/**
 * graph-viz.js — Mini graph traversal visualization using Canvas.
 * Renders nodes and edges to show which SurrealDB tables/relations
 * the agent traversed during a query.
 */

const NODE_COLORS = {
  query:    '#ff00a0',
  product:  '#00d4aa',
  customer: '#9600ff',
  category: '#ffaa00',
  review:   '#ff4466',
  order:    '#5e9eff',
  faq:      '#c77dff',
  learned:  '#c77dff',
};

const EDGE_COLORS = {
  vector:     '#ff00a0',
  graph:      '#9600ff',
  bm25:       '#00d4aa',
  relational: '#ffaa00',
};

function renderGraphViz(graphData) {
  const container = document.createElement('div');
  container.className = 'graph-viz-container';

  const label = document.createElement('div');
  label.className = 'graph-viz-label';
  label.textContent = 'Graph traversal';
  container.appendChild(label);

  const canvas = document.createElement('canvas');
  canvas.className = 'graph-viz-canvas';
  canvas.width = 360;
  canvas.height = 200;
  container.appendChild(canvas);

  // Legend
  const legend = document.createElement('div');
  legend.className = 'graph-viz-legend';
  const types = [...new Set(graphData.edges.map(e => e.type))];
  legend.innerHTML = types.map(t =>
    `<span class="graph-legend-item">
      <span class="graph-legend-dot" style="background:${EDGE_COLORS[t] || '#5E5A73'}"></span>${t}
    </span>`
  ).join('');
  container.appendChild(legend);

  // Layout: position nodes using simple force-directed-ish placement
  requestAnimationFrame(() => drawGraph(canvas, graphData));

  return container;
}

function drawGraph(canvas, graphData) {
  const ctx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;
  const dpr = window.devicePixelRatio || 1;

  canvas.width = W * dpr;
  canvas.height = H * dpr;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';
  ctx.scale(dpr, dpr);

  const nodes = graphData.nodes;
  const edges = graphData.edges;

  // Simple layout: place nodes in a grid-like arrangement
  const positions = {};
  const cols = Math.ceil(Math.sqrt(nodes.length));
  const padX = 50, padY = 36;
  const spacingX = (W - padX * 2) / Math.max(cols - 1, 1);
  const spacingY = (H - padY * 2) / Math.max(Math.ceil(nodes.length / cols) - 1, 1);

  nodes.forEach((node, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    positions[node.id] = {
      x: padX + col * spacingX,
      y: padY + row * spacingY,
    };
  });

  // Draw edges
  edges.forEach(edge => {
    const from = positions[edge.from];
    const to = positions[edge.to];
    if (!from || !to) return;

    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.strokeStyle = EDGE_COLORS[edge.type] || '#5E5A73';
    ctx.lineWidth = 1.5;
    ctx.globalAlpha = 0.6;
    ctx.stroke();
    ctx.globalAlpha = 1;

    // Arrow head
    const angle = Math.atan2(to.y - from.y, to.x - from.x);
    const arrowLen = 8;
    const endX = to.x - Math.cos(angle) * 16;
    const endY = to.y - Math.sin(angle) * 16;
    ctx.beginPath();
    ctx.moveTo(endX, endY);
    ctx.lineTo(endX - arrowLen * Math.cos(angle - 0.4), endY - arrowLen * Math.sin(angle - 0.4));
    ctx.lineTo(endX - arrowLen * Math.cos(angle + 0.4), endY - arrowLen * Math.sin(angle + 0.4));
    ctx.closePath();
    ctx.fillStyle = EDGE_COLORS[edge.type] || '#5E5A73';
    ctx.globalAlpha = 0.6;
    ctx.fill();
    ctx.globalAlpha = 1;

    // Edge label
    if (edge.label) {
      const midX = (from.x + to.x) / 2;
      const midY = (from.y + to.y) / 2;
      ctx.font = '9px Inter, sans-serif';
      ctx.fillStyle = EDGE_COLORS[edge.type] || '#5E5A73';
      ctx.globalAlpha = 0.8;
      ctx.textAlign = 'center';
      ctx.fillText(edge.label, midX, midY - 4);
      ctx.globalAlpha = 1;
    }
  });

  // Draw nodes
  nodes.forEach(node => {
    const pos = positions[node.id];
    const color = NODE_COLORS[node.type] || '#9B97B0';
    const radius = node.type === 'query' ? 14 : 12;

    // Glow
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius + 4, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.globalAlpha = 0.15;
    ctx.fill();
    ctx.globalAlpha = 1;

    // Circle
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = '#15131D';
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Label
    ctx.font = '10px Inter, sans-serif';
    ctx.fillStyle = '#F9F9F9';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Handle multi-line labels
    const lines = node.label.split('\n');
    if (lines.length > 1) {
      lines.forEach((line, i) => {
        ctx.fillText(line, pos.x, pos.y + radius + 12 + i * 12, 70);
      });
    } else {
      ctx.fillText(node.label, pos.x, pos.y + radius + 12, 70);
    }
  });
}
