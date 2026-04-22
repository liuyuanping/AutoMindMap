let currentGraph = null;
let simulation = null;

// DOM elements
const analyzeBtn = document.getElementById('analyzeBtn');
const saveBtn = document.getElementById('saveBtn');
const loadBtn = document.getElementById('loadBtn');
const dirPathInput = document.getElementById('dirPath');
const thresholdInput = document.getElementById('threshold');
const thresholdValue = document.getElementById('thresholdValue');
const statsDiv = document.getElementById('stats');
const loadingDiv = document.getElementById('loading');
const tooltip = document.getElementById('tooltip');
const nodeDetailDiv = document.getElementById('nodeDetail');
const savedFilesDiv = document.getElementById('savedFiles');

// Event listeners
analyzeBtn.addEventListener('click', analyzeDocuments);
saveBtn.addEventListener('click', saveGraph);
loadBtn.addEventListener('click', showLoadDialog);
thresholdInput.addEventListener('input', (e) => {
    thresholdValue.textContent = e.target.value;
});

async function analyzeDocuments() {
    const dirPath = dirPathInput.value.trim();
    const threshold = parseFloat(thresholdInput.value);

    if (!dirPath) {
        alert('请输入文档目录路径');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dir_path: dirPath, threshold })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '分析失败');
        }

        const data = await response.json();
        currentGraph = data.graph;

        renderGraph(currentGraph);
        updateStats(data.graph.metadata);
        saveBtn.disabled = false;

        loadSavedFiles();

    } catch (error) {
        alert('分析失败: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function renderGraph(graph) {
    const container = document.getElementById('graph');
    container.innerHTML = '';

    if (graph.nodes.length === 0) {
        container.innerHTML = '<p style="text-align:center;padding:50px;color:#666;">暂无数据</p>';
        return;
    }

    const width = container.clientWidth;
    const height = container.clientHeight;

    const svg = d3.select('#graph')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height]);

    // 创建缩放行为
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    svg.call(zoom);

    const g = svg.append('g');

    // 准备节点和边数据
    const nodes = graph.nodes.map(n => ({...n}));
    const edges = graph.edges.map(e => ({...e}));

    // 创建节点ID映射
    const nodeMap = new Map();
    nodes.forEach(n => nodeMap.set(n.id, n));

    // 转换边为D3格式
    const links = edges.map(e => ({
        source: e.source,
        target: e.target,
        score: e.score
    }));

    // 力导向图模拟
    simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(150))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(50));

    // 绘制边
    const link = g.append('g')
        .selectAll('line')
        .data(links)
        .enter()
        .append('line')
        .attr('class', 'link')
        .attr('stroke-width', d => Math.max(1, d.score * 4))
        .on('mouseover', function(event, d) {
            const source = typeof d.source === 'object' ? d.source.id : d.source;
            const target = typeof d.target === 'object' ? d.target.id : d.target;
            showTooltip(event, `相关度: ${d.score.toFixed(3)}`);
        })
        .on('mouseout', hideTooltip);

    // 绘制节点
    const node = g.append('g')
        .selectAll('g')
        .data(nodes)
        .enter()
        .append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended))
        .on('click', (event, d) => showNodeDetail(d))
        .on('mouseover', function(event, d) {
            showTooltip(event, `${d.title || '无标题'}\n${d.doc_path}`);
        })
        .on('mouseout', hideTooltip);

    // 节点圆圈
    node.append('circle')
        .attr('r', d => d.level === 1 ? 15 : 10)
        .attr('fill', d => d.level === 1 ? '#667eea' : '#764ba2');

    // 节点标签
    node.append('text')
        .attr('dx', 20)
        .attr('dy', 4)
        .text(d => d.title || `Block ${d.chapter_index}.${d.section_index}`)
        .attr('fill', '#fff')
        .attr('font-size', '11px');

    // 更新位置
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

function showNodeDetail(node) {
    const parentNode = currentGraph.nodes.find(n => n.id === node.parent_id);
    let html = `<h4>${node.title || '无标题'}</h4>`;
    html += `<p class="meta">`;
    html += `文档: ${node.doc_path}<br>`;
    html += `位置: 第${node.start_line}-${node.end_line}行<br>`;
    html += `级别: ${node.level === 1 ? '章节' : '小节'}<br>`;
    if (parentNode) {
        html += `父节点: ${parentNode.title || parentNode.id}`;
    }
    html += `</p>`;
    html += `<div class="content">${node.content_preview || node.content}</div>`;
    nodeDetailDiv.innerHTML = html;
}

function updateStats(metadata) {
    statsDiv.innerHTML = `
        <span>文档数: ${metadata.doc_count}</span> |
        <span>块数: ${metadata.block_count}</span> |
        <span>创建时间: ${new Date(metadata.created_at).toLocaleString()}</span>
    `;
    statsDiv.classList.add('show');
}

async function saveGraph() {
    if (!currentGraph) return;

    const filename = prompt('请输入文件名:', `graph_${Date.now()}.json`);
    if (!filename) return;

    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ graph: currentGraph, filename })
        });

        const data = await response.json();
        if (data.success) {
            alert('保存成功: ' + data.path);
            loadSavedFiles();
        }
    } catch (error) {
        alert('保存失败: ' + error.message);
    }
}

async function loadSavedGraphs() {
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        return data.files || [];
    } catch (error) {
        return [];
    }
}

async function loadSavedFiles() {
    const files = await loadSavedGraphs();

    if (files.length === 0) {
        savedFilesDiv.innerHTML = '<p class="placeholder">暂无保存的图表</p>';
        return;
    }

    savedFilesDiv.innerHTML = files.map(f => `
        <div class="saved-file-item" onclick="loadGraphFile('${f.path}')">
            <div class="name">${f.name}</div>
            <div class="info">${(f.size / 1024).toFixed(1)} KB | ${new Date(f.modified).toLocaleDateString()}</div>
        </div>
    `).join('');
}

async function loadGraphFile(path) {
    showLoading(true);

    try {
        const response = await fetch(`/api/load?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        if (data.graph) {
            currentGraph = data.graph;
            renderGraph(currentGraph);
            updateStats(data.graph.metadata);
            saveBtn.disabled = false;
        }
    } catch (error) {
        alert('加载失败: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function showLoadDialog() {
    const path = prompt('请输入图文件路径:');
    if (path) {
        loadGraphFile(path);
    }
}

function showLoading(show) {
    loadingDiv.classList.toggle('show', show);
}

function showTooltip(event, text) {
    tooltip.textContent = text;
    tooltip.style.left = (event.pageX + 10) + 'px';
    tooltip.style.top = (event.pageY + 10) + 'px';
    tooltip.classList.add('show');
}

function hideTooltip() {
    tooltip.classList.remove('show');
}

// 初始加载已保存的文件列表
loadSavedFiles();

// 处理窗口大小变化
window.addEventListener('resize', () => {
    if (currentGraph) {
        renderGraph(currentGraph);
    }
});