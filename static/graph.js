let currentGraph = null;
let simulation = null;
let selectedNodeId = null;

const analyzeBtn = document.getElementById('analyzeBtn');
const saveBtn = document.getElementById('saveBtn');
const loadBtn = document.getElementById('loadBtn');
const dirPathInput = document.getElementById('dirPath');
const thresholdInput = document.getElementById('threshold');
const thresholdValue = document.getElementById('thresholdValue');
const tooltipOffsetInput = document.getElementById('tooltipOffset');
const tooltipOffsetValue = document.getElementById('tooltipOffsetValue');
const parentDepthInput = document.getElementById('parentDepth');
const parentDepthValue = document.getElementById('parentDepthValue');
let currentTooltipOffset = 30;
let currentParentDepth = 1;
const statsDiv = document.getElementById('stats');
const loadingDiv = document.getElementById('loading');
const tooltip = document.getElementById('tooltip');
const nodeDetailDiv = document.getElementById('nodeDetail');
const savedFilesDiv = document.getElementById('savedFiles');

analyzeBtn.addEventListener('click', analyzeDocuments);
saveBtn.addEventListener('click', saveGraph);
loadBtn.addEventListener('click', showLoadDialog);
thresholdInput.addEventListener('input', (e) => {
    thresholdValue.textContent = e.target.value;
});

tooltipOffsetInput.addEventListener('input', (e) => {
    tooltipOffsetValue.textContent = e.target.value;
    currentTooltipOffset = parseInt(e.target.value);
});

parentDepthInput.addEventListener('input', (e) => {
    parentDepthValue.textContent = e.target.value;
    currentParentDepth = parseInt(e.target.value);
    if (selectedNodeId && currentGraph) {
        renderGraph(currentGraph);
    }
});

async function analyzeDocuments() {
    const dirPath = dirPathInput.value.trim();
    const threshold = parseFloat(thresholdInput.value);

    if (!dirPath) {
        alert('请输入文档目录路径');
        return;
    }

    showLoading(true);
    selectedNodeId = null;

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

function getNodeColor(level) {
    const colors = [
        '#667eea', // 0: 顶级段落
        '#764ba2', // 1: # 标题
        '#48bb78', // 2: ## 标题
        '#ed8936', // 3: ### 标题
        '#f56565', // 4: #### 标题
        '#9f7aea', // 5: ##### 标题
        '#38b2ac'  // 6: ###### 标题
    ];
    return colors[Math.min(level, 6)];
}

function getNodeRadius(level) {
    return Math.max(8, 20 - level * 2);
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

    const zoom = d3.zoom()
        .scaleExtent([0.05, 5])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    svg.call(zoom);

    const g = svg.append('g');

    const nodes = graph.nodes.map(n => ({...n}));
    const edges = graph.edges.map(e => ({...e}));

    // 父子关系边（树状结构）
    const parentLinks = nodes
        .filter(n => n.parent_id)
        .map(n => ({
            source: n.parent_id,
            target: n.id,
            isParent: true
        }));

    // 相似度边
    const similarityLinks = edges.map(e => ({
        source: e.source,
        target: e.target,
        score: e.score,
        isParent: false
    }));

    let visibleNodes = nodes;
    let visibleLinks = [...parentLinks, ...similarityLinks];

    if (selectedNodeId) {
        const connected = new Set([selectedNodeId]);

        // 通过相似度边连接
        edges.forEach(e => {
            if (e.source === selectedNodeId || e.target === selectedNodeId) {
                connected.add(e.source);
                connected.add(e.target);
            }
        });

        // 通过父子关系连接（向上找祖先，向下找后代）
        const findAncestors = (nodeId, depth) => {
            if (depth <= 0) return;
            const node = nodes.find(n => n.id === nodeId);
            if (node && node.parent_id) {
                connected.add(node.parent_id);
                findAncestors(node.parent_id, depth - 1);
            }
        };
        const findDescendants = (nodeId, depth) => {
            if (depth <= 0) return;
            nodes.forEach(n => {
                if (n.parent_id === nodeId) {
                    connected.add(n.id);
                    findDescendants(n.id, depth - 1);
                }
            });
        };
        findAncestors(selectedNodeId, currentParentDepth);
        findDescendants(selectedNodeId, currentParentDepth);

        visibleNodes = nodes.filter(n => connected.has(n.id));
        visibleLinks = [...parentLinks, ...similarityLinks].filter(l => {
            const srcId = typeof l.source === 'object' ? l.source.id : l.source;
            const tgtId = typeof l.target === 'object' ? l.target.id : l.target;
            return connected.has(srcId) && connected.has(tgtId);
        });
    }

    simulation = d3.forceSimulation(visibleNodes)
        .force('link', d3.forceLink(visibleLinks).id(d => d.id).distance(d => d.isParent ? 80 : 150))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(30))
        .force('x', d3.forceX(width / 2).strength(0.05))
        .force('y', d3.forceY(height / 2).strength(0.05));

    // 分离父子边和相似度边
    const visibleParentLinks = visibleLinks.filter(l => l.isParent);
    const visibleSimLinks = visibleLinks.filter(l => !l.isParent);

    // 绘制父子关系边（实线）
    const parentLink = g.append('g')
        .selectAll('line')
        .data(visibleParentLinks)
        .enter()
        .append('line')
        .attr('class', 'parent-link')
        .attr('stroke', '#888')
        .attr('stroke-width', 1.5)
        .attr('stroke-opacity', 0.6);

    // 绘制相似度边（虚线）
    const simLink = g.append('g')
        .selectAll('line')
        .data(visibleSimLinks)
        .enter()
        .append('line')
        .attr('class', 'sim-link')
        .attr('stroke', '#667eea')
        .attr('stroke-width', d => Math.max(1, d.score * 3))
        .attr('stroke-opacity', 0.5)
        .attr('stroke-dasharray', '5,5')
        .on('mouseover', function(event, d) {
            d3.select(this).attr('stroke-opacity', 1);
            showTooltip(event, `相关度: ${d.score.toFixed(3)}`);
        })
        .on('mouseout', function() {
            d3.select(this).attr('stroke-opacity', 0.5);
            hideTooltip();
        });

    // 相似度标签
    const simLabel = g.append('g')
        .selectAll('text')
        .data(visibleSimLinks)
        .enter()
        .append('text')
        .attr('class', 'sim-label')
        .attr('fill', '#667eea')
        .attr('font-size', '10px')
        .attr('text-anchor', 'middle')
        .text(d => d.score.toFixed(2));

    // 绘制节点
    const node = g.append('g')
        .selectAll('g')
        .data(visibleNodes)
        .enter()
        .append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended))
        .on('click', (event, d) => {
            event.stopPropagation();
            if (selectedNodeId === d.id) {
                selectedNodeId = null;
            } else {
                selectedNodeId = d.id;
            }
            renderGraph(currentGraph);
            showNodeDetail(d);
        })
        .on('mouseover', function(event, d) {
            const label = d.title || `Block ${d.chapter_index}.${d.section_index}`;
            showTooltip(event, `${label}\n${d.doc_path} | lines ${d.start_line}-${d.end_line}`);
        })
        .on('mouseout', hideTooltip);

    // 节点外圈
    node.append('circle')
        .attr('r', d => getNodeRadius(d.level))
        .attr('fill', d => selectedNodeId === d.id ? '#fff' : getNodeColor(d.level))
        .attr('stroke', d => selectedNodeId === d.id ? getNodeColor(d.level) : '#fff')
        .attr('stroke-width', d => selectedNodeId === d.id ? 3 : 2);

    // 节点内圈
    node.append('circle')
        .attr('r', d => d.level <= 1 ? 5 : 3)
        .attr('fill', selectedNodeId ? '#667eea' : '#fff')
        .attr('cx', 0)
        .attr('cy', 0);

    // 节点标签
    node.append('text')
        .attr('dx', d => getNodeRadius(d.level) + 5)
        .attr('dy', 4)
        .text(d => {
            const label = d.title || `P${d.chapter_index}.${d.section_index}`;
            return label.length > 20 ? label.substring(0, 18) + '...' : label;
        })
        .attr('fill', '#ccc')
        .attr('font-size', '10px');

    svg.on('click', () => {
        selectedNodeId = null;
        renderGraph(currentGraph);
    });

    simulation.on('tick', () => {
        parentLink
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        simLink
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        simLabel
            .attr('x', d => (d.source.x + d.target.x) / 2)
            .attr('y', d => (d.source.y + d.target.y) / 2);

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
    if (!currentGraph) return;

    const parentNode = currentGraph.nodes.find(n => n.id === node.parent_id);
    const levelNames = ['顶级段落', '章节', '子章节', '小节', '小小节', '极小节', '微节'];
    const levelName = levelNames[Math.min(node.level, 6)] || '段落';

    let html = `<h4>${node.title || '(段落)'}</h4>`;
    html += `<p class="meta">`;
    html += `文档: ${node.doc_path}<br>`;
    html += `位置: 第${node.start_line}-${node.end_line}行<br>`;
    html += `级别: ${levelName} (level ${node.level})`;
    html += `</p>`;

    if (parentNode) {
        const parentTitle = parentNode.title || '(段落)';
        html += `<p class="meta">父节点: ${parentTitle}</p>`;
    }

    const connectedEdges = currentGraph.edges.filter(e =>
        e.source === node.id || e.target === node.id
    );
    if (connectedEdges.length > 0) {
        html += `<p class="meta">关联块 (${connectedEdges.length}):</p>`;
        connectedEdges.forEach(e => {
            const otherId = e.source === node.id ? e.target : e.source;
            const otherNode = currentGraph.nodes.find(n => n.id === otherId);
            if (otherNode) {
                const otherTitle = otherNode.title || '(段落)';
                html += `<p class="meta" style="margin-left:10px;">• ${otherTitle} (${e.score.toFixed(2)})</p>`;
            }
        });
    }

    const renderedContent = node.content ? marked.parse(node.content) : '(无内容)';
    html += `<div class="content">${renderedContent}</div>`;
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
    selectedNodeId = null;

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
    tooltip.style.left = (event.clientX + currentTooltipOffset) + 'px';
    tooltip.style.top = (event.clientY + currentTooltipOffset) + 'px';
    tooltip.classList.add('show');
}

function hideTooltip() {
    tooltip.classList.remove('show');
}

loadSavedFiles();

window.addEventListener('resize', () => {
    if (currentGraph) {
        renderGraph(currentGraph);
    }
});