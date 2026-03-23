// Coach-School Relationship Visualizer - D3.js Application

document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const CONFIG = {
        width: 1200,
        height: 600,
        nodeRadius: 8,
        chargeStrength: -300,
        linkDistance: 100,
        coachColor: '#3498db',
        schoolColor: '#e67e22',
        linkColor: '#95a5a6',
        highlightColor: '#e74c3c'
    };

    // State
    let graphData = null;
    let filteredGraphData = null;
    let simulation = null;
    let svg = null;
    let g = null;
    let nodes = null;
    let links = null;
    let nodeElements = null;
    let linkElements = null;
    let nodeTextElements = null;
    let selectedNode = null;
    
    // DOM Elements
    const searchInput = document.getElementById('search');
    const showCoachesCheckbox = document.getElementById('show-coaches');
    const showSchoolsCheckbox = document.getElementById('show-schools');
    const yearRangeInput = document.getElementById('year-range');
    const minYearSpan = document.getElementById('min-year');
    const maxYearSpan = document.getElementById('max-year');
    const selectedYearSpan = document.getElementById('selected-year');
    const resetViewButton = document.getElementById('reset-view');
    const exportJsonButton = document.getElementById('export-json');
    const statsDiv = document.getElementById('stats');
    const selectionInfoDiv = document.getElementById('selection-info');
    const nodeDetailsDiv = document.getElementById('node-details');
    const loadingDiv = document.getElementById('loading');
    const noDataDiv = document.getElementById('no-data');
    const nodeCountSpan = document.getElementById('node-count');
    const edgeCountSpan = document.getElementById('edge-count');
    const generatedDateSpan = document.getElementById('generated-date');
    
    // Initialize
    init();
    
    async function init() {
        setupEventListeners();
        await loadGraphData();
        if (graphData) {
            initializeVisualization();
            updateStats();
            updateDateDisplay();
        }
    }
    
    function setupEventListeners() {
        // Search
        searchInput.addEventListener('input', debounce(filterGraph, 300));
        
        // Filter checkboxes
        showCoachesCheckbox.addEventListener('change', filterGraph);
        showSchoolsCheckbox.addEventListener('change', filterGraph);
        
        // Year range
        yearRangeInput.addEventListener('input', function() {
            const year = parseInt(this.value);
            updateYearDisplay(year);
            filterGraph();
        });
        
        // Reset view
        resetViewButton.addEventListener('click', resetView);
        
        // Export JSON
        exportJsonButton.addEventListener('click', exportGraphData);
    }
    
    async function loadGraphData() {
        try {
            // Try to load from web_graph.json first, then fall back to data/graph.json
            let response = await fetch('web_graph.json');
            if (!response.ok) {
                response = await fetch('../data/graph.json');
            }
            
            if (response.ok) {
                graphData = await response.json();
                filteredGraphData = JSON.parse(JSON.stringify(graphData)); // Deep copy
                hideLoading();
                return true;
            } else {
                showNoData();
                return false;
            }
        } catch (error) {
            console.error('Error loading graph data:', error);
            showNoData();
            return false;
        }
    }
    
    function hideLoading() {
        loadingDiv.style.display = 'none';
        noDataDiv.style.display = 'none';
    }
    
    function showNoData() {
        loadingDiv.style.display = 'none';
        noDataDiv.style.display = 'flex';
    }
    
    function initializeVisualization() {
        // Create SVG
        svg = d3.select('#graph-svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', [0, 0, CONFIG.width, CONFIG.height]);
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });
        
        svg.call(zoom);
        
        // Create main group
        g = svg.append('g');
        
        // Create arrow marker for links
        svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 25)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', CONFIG.linkColor);
        
        // Draw the graph
        drawGraph();
    }
    
    function drawGraph() {
        if (!filteredGraphData) return;
        
        // Clear previous elements
        g.selectAll('*').remove();
        
        // Create links
        linkElements = g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(filteredGraphData.edges)
            .enter()
            .append('line')
            .attr('class', 'link')
            .attr('stroke', CONFIG.linkColor)
            .attr('stroke-width', 1.5)
            .attr('stroke-opacity', 0.6)
            .attr('marker-end', 'url(#arrowhead)');
        
        // Create nodes
        nodeElements = g.append('g')
            .attr('class', 'nodes')
            .selectAll('circle')
            .data(filteredGraphData.nodes)
            .enter()
            .append('circle')
            .attr('class', 'node')
            .attr('r', d => d.size || CONFIG.nodeRadius)
            .attr('fill', d => d.type === 'coach' ? CONFIG.coachColor : CONFIG.schoolColor)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .call(drag(simulation))
            .on('mouseover', handleNodeMouseOver)
            .on('mouseout', handleNodeMouseOut)
            .on('click', handleNodeClick);
        
        // Create node labels
        nodeTextElements = g.append('g')
            .attr('class', 'node-labels')
            .selectAll('text')
            .data(filteredGraphData.nodes)
            .enter()
            .append('text')
            .attr('class', 'node-text')
            .attr('dy', d => -(d.size || CONFIG.nodeRadius) - 5)
            .text(d => d.label)
            .attr('font-size', '12px')
            .attr('font-weight', '600')
            .attr('fill', '#2c3e50')
            .attr('text-anchor', 'middle')
            .attr('pointer-events', 'none');
        
        // Setup simulation
        simulation = d3.forceSimulation(filteredGraphData.nodes)
            .force('link', d3.forceLink(filteredGraphData.edges)
                .id(d => d.id)
                .distance(CONFIG.linkDistance)
                .strength(0.1))
            .force('charge', d3.forceManyBody()
                .strength(CONFIG.chargeStrength))
            .force('center', d3.forceCenter(CONFIG.width / 2, CONFIG.height / 2))
            .force('collision', d3.forceCollide().radius(d => (d.size || CONFIG.nodeRadius) + 5))
            .on('tick', ticked);
        
        // Update positions on tick
        function ticked() {
            linkElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            nodeElements
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            nodeTextElements
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        }
        
        // Update UI
        updateNodeEdgeCounts();
    }
    
    function drag(simulation) {
        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }
        
        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }
        
        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }
        
        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }
    
    function handleNodeMouseOver(event, d) {
        // Highlight connected nodes and links
        const nodeId = d.id;
        
        // Highlight connected links
        linkElements
            .attr('stroke', l => 
                (l.source.id === nodeId || l.target.id === nodeId) 
                    ? CONFIG.highlightColor 
                    : CONFIG.linkColor)
            .attr('stroke-width', l => 
                (l.source.id === nodeId || l.target.id === nodeId) ? 3 : 1.5)
            .attr('stroke-opacity', l => 
                (l.source.id === nodeId || l.target.id === nodeId) ? 1 : 0.6);
        
        // Show tooltip
        const tooltipHtml = `
            <h4>${d.label}</h4>
            <p><strong>Type:</strong> ${d.type}</p>
            <p><strong>Frequency:</strong> ${d.frequency || 1}</p>
            <p><strong>Connections:</strong> ${countConnections(nodeId)}</p>
        `;
        
        showTooltip(event, tooltipHtml);
    }
    
    function handleNodeMouseOut() {
        // Reset link styles
        linkElements
            .attr('stroke', CONFIG.linkColor)
            .attr('stroke-width', 1.5)
            .attr('stroke-opacity', 0.6);
        
        // Hide tooltip
        hideTooltip();
    }
    
    function handleNodeClick(event, d) {
        if (selectedNode === d.id) {
            // Deselect if clicking the same node
            selectedNode = null;
            clearNodeSelection();
        } else {
            selectedNode = d.id;
            highlightNodeConnections(d.id);
            updateNodeDetails(d);
        }
    }
    
    function countConnections(nodeId) {
        if (!filteredGraphData) return 0;
        return filteredGraphData.edges.filter(edge => 
            edge.source.id === nodeId || edge.target.id === nodeId
        ).length;
    }
    
    function highlightNodeConnections(nodeId) {
        // Reset all nodes and links
        nodeElements
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .attr('opacity', 0.3);
        
        linkElements
            .attr('stroke', CONFIG.linkColor)
            .attr('stroke-width', 1.5)
            .attr('stroke-opacity', 0.6);
        
        // Highlight selected node
        nodeElements.filter(d => d.id === nodeId)
            .attr('stroke', '#000')
            .attr('stroke-width', 3)
            .attr('opacity', 1);
        
        // Highlight connected nodes
        const connectedNodeIds = new Set();
        filteredGraphData.edges.forEach(edge => {
            if (edge.source.id === nodeId) {
                connectedNodeIds.add(edge.target.id);
            } else if (edge.target.id === nodeId) {
                connectedNodeIds.add(edge.source.id);
            }
        });
        
        nodeElements.filter(d => connectedNodeIds.has(d.id))
            .attr('stroke', CONFIG.highlightColor)
            .attr('stroke-width', 2.5)
            .attr('opacity', 1);
        
        // Highlight connected links
        linkElements.filter(edge => 
            edge.source.id === nodeId || edge.target.id === nodeId
        )
            .attr('stroke', CONFIG.highlightColor)
            .attr('stroke-width', 3)
            .attr('stroke-opacity', 1);
    }
    
    function clearNodeSelection() {
        nodeElements
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .attr('opacity', 1);
        
        linkElements
            .attr('stroke', CONFIG.linkColor)
            .attr('stroke-width', 1.5)
            .attr('stroke-opacity', 0.6);
        
        nodeDetailsDiv.innerHTML = '<p>Select a node to see details</p>';
        selectionInfoDiv.innerHTML = '<div>Click a node to see details</div>';
    }
    
    function updateNodeDetails(node) {
        // Find connected nodes
        const connections = [];
        filteredGraphData.edges.forEach(edge => {
            if (edge.source.id === node.id) {
                const targetNode = filteredGraphData.nodes.find(n => n.id === edge.target.id);
                if (targetNode) {
                    connections.push({
                        node: targetNode,
                        type: edge.target.type === 'coach' ? 'Coached at' : 'Coached by',
                        date: edge.date || 'Unknown date'
                    });
                }
            } else if (edge.target.id === node.id) {
                const sourceNode = filteredGraphData.nodes.find(n => n.id === edge.source.id);
                if (sourceNode) {
                    connections.push({
                        node: sourceNode,
                        type: sourceNode.type === 'coach' ? 'Coached by' : 'Coached at',
                        date: edge.date || 'Unknown date'
                    });
                }
            }
        });
        
        // Update details panel
        let html = `
            <h4>${node.label}</h4>
            <p><strong>Type:</strong> ${node.type === 'coach' ? 'Coach' : 'School'}</p>
            <p><strong>Frequency in notes:</strong> ${node.frequency || 1}</p>
            <p><strong>Total connections:</strong> ${connections.length}</p>
        `;
        
        if (connections.length > 0) {
            html += `<p><strong>Connections:</strong></p><ul>`;
            connections.forEach(conn => {
                html += `<li><strong>${conn.type}:</strong> ${conn.node.label} (${conn.date})</li>`;
            });
            html += '</ul>';
        }
        
        nodeDetailsDiv.innerHTML = html;
        
        // Update selection info
        selectionInfoDiv.innerHTML = `
            <div><strong>Selected:</strong> ${node.label}</div>
            <div><strong>Type:</strong> ${node.type === 'coach' ? 'Coach' : 'School'}</div>
            <div><strong>Connections:</strong> ${connections.length}</div>
        `;
    }
    
    function filterGraph() {
        if (!graphData) return;
        
        const searchTerm = searchInput.value.toLowerCase();
        const showCoaches = showCoachesCheckbox.checked;
        const showSchools = showSchoolsCheckbox.checked;
        const selectedYear = parseInt(yearRangeInput.value);
        
        // Filter nodes
        const filteredNodes = graphData.nodes.filter(node => {
            // Type filter
            if (node.type === 'coach' && !showCoaches) return false;
            if (node.type === 'school' && !showSchools) return false;
            
            // Search filter
            if (searchTerm && !node.label.toLowerCase().includes(searchTerm)) {
                return false;
            }
            
            return true;
        });
        
        const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
        
        // Filter edges (only include edges where both nodes are in filteredNodes)
        const filteredEdges = graphData.edges.filter(edge => {
            // Check if both nodes are in filtered set
            const sourceInFilter = filteredNodeIds.has(edge.source.id || edge.source);
            const targetInFilter = filteredNodeIds.has(edge.target.id || edge.target);
            
            // Year filter (if edge has date)
            let yearMatch = true;
            if (edge.date) {
                const edgeYear = extractYear(edge.date);
                if (edgeYear && edgeYear <= selectedYear) {
                    // Edge is from before or during selected year
                } else if (edgeYear) {
                    yearMatch = false;
                }
            }
            
            return sourceInFilter && targetInFilter && yearMatch;
        });
        
        // Update filtered graph data
        filteredGraphData = {
            nodes: filteredNodes,
            edges: filteredEdges,
            metadata: graphData.metadata
        };
        
        // Re-draw graph
        drawGraph();
        updateStats();
        
        // Clear selection if selected node is no longer visible
        if (selectedNode && !filteredNodeIds.has(selectedNode)) {
            selectedNode = null;
            clearNodeSelection();
        }
    }
    
    function extractYear(dateString) {
        if (!dateString) return null;
        
        // Try to extract year from various date formats
        const yearMatch = dateString.match(/\b(\d{4})\b/);
        return yearMatch ? parseInt(yearMatch[1]) : null;
    }
    
    function updateYearDisplay(year) {
        selectedYearSpan.textContent = `2000-${year}`;
    }
    
    function updateStats() {
        if (!filteredGraphData) return;
        
        const { nodes, edges } = filteredGraphData;
        const coachCount = nodes.filter(n => n.type === 'coach').length;
        const schoolCount = nodes.filter(n => n.type === 'school').length;
        
        statsDiv.innerHTML = `
            <div><strong>Coaches:</strong> ${coachCount}</div>
            <div><strong>Schools:</strong> ${schoolCount}</div>
            <div><strong>Relationships:</strong> ${edges.length}</div>
            <div><strong>Density:</strong> ${((edges.length / (coachCount + schoolCount)) * 100).toFixed(1)}%</div>
        `;
    }
    
    function updateNodeEdgeCounts() {
        if (!filteredGraphData) return;
        
        nodeCountSpan.textContent = filteredGraphData.nodes.length;
        edgeCountSpan.textContent = filteredGraphData.edges.length;
    }
    
    function updateDateDisplay() {
        if (graphData && graphData.metadata && graphData.metadata.generated_at) {
            const date = new Date(graphData.metadata.generated_at);
            generatedDateSpan.textContent = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        } else {
            generatedDateSpan.textContent = new Date().toLocaleDateString();
        }
    }
    
    function resetView() {
        // Reset zoom and pan
        svg.transition()
            .duration(750)
            .call(d3.zoom().transform, d3.zoomIdentity);
        
        // Reset filters
        searchInput.value = '';
        showCoachesCheckbox.checked = true;
        showSchoolsCheckbox.checked = true;
        yearRangeInput.value = 2026;
        updateYearDisplay(2026);
        
        // Reset to original graph data
        if (graphData) {
            filteredGraphData = JSON.parse(JSON.stringify(graphData));
            drawGraph();
            updateStats();
            clearNodeSelection();
        }
    }
    
    function exportGraphData() {
        if (!filteredGraphData) return;
        
        const dataStr = JSON.stringify(filteredGraphData, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `coach-school-graph-${new Date().toISOString().slice(0, 10)}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
    }
    
    function showTooltip(event, html) {
        // Remove existing tooltip
        d3.select('.tooltip').remove();
        
        // Create new tooltip
        const tooltip = d3.select('body')
            .append('div')
            .attr('class', 'tooltip')
            .html(html)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
    }
    
    function hideTooltip() {
        d3.select('.tooltip').remove();
    }
    
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Initialize year display
    updateYearDisplay(parseInt(yearRangeInput.value));
});