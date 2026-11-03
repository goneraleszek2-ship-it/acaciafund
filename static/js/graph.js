  (function() {
    var cy;
    var rawData = null;
    var currentActiveNode = null;
    var detailTimer = null;

    var RELATION_COLORS = {
      'part_of': '#22c55e',
      'requires': '#3b82f6',
      'related_to': '#f59e0b',
      'detects': '#ef4444',
      'enables': '#a855f7',
      'implements': '#a855f7',
      'regulates': '#a855f7',
      'influences': '#a855f7',
      'measures': '#a855f7',
      'supersedes': '#a855f7',
    };

    var PILLAR_URL_MAP = { aml: 'compliance', stock: 'markets', 'data-engineering': 'data' };

    var PILLAR_COLORS = {
      'compliance': '#f59e0b',
      'markets': '#3b82f6',
      'data': '#22c55e',
    };

    function runLayout(name) {
      if (!cy) return;
      var opts = { animate: true, animationDuration: 600, fit: true, padding: 30 };
      if (name === 'dagre') {
        opts.name = 'dagre';
        opts.rankDir = 'TB';
        opts.nodeSep = 40;
        opts.rankSep = 60;
        opts.edgeSep = 10;
      } else if (name === 'cose-bilkent') {
        opts.name = window.cytoscapeCoseBilkent ? 'cose-bilkent' : 'cose';
        opts.nodeRepulsion = function() { return 204800; };
        opts.idealEdgeLength = function() { return 80; };
        opts.gravity = 0.25;
        opts.numIter = 1000;
      } else if (name === 'concentric') {
        opts.name = 'concentric';
        opts.concentric = function(n) { return n.degree(); };
        opts.levelWidth = function(nodes) { return 2; };
      } else if (name === 'breadthfirst') {
        opts.name = 'breadthfirst';
        opts.directed = true;
      }
      cy.layout(opts).run();
    }

    function applyFilters() {
      if (!cy) return;

      var pillarVal = document.getElementById('graph-filter').value;
      var relVal = document.getElementById('graph-relation-filter').value;

      cy.elements().removeClass('faded');

      var visibleEdges = cy.edges();
      var visibleNodes = cy.nodes();

      // Relation filter
      if (relVal !== 'all') {
        visibleEdges = cy.edges('[relation = "' + relVal + '"]');
        var connectedNodeIds = new Set();
        visibleEdges.forEach(function(e) {
          connectedNodeIds.add(e.data('source'));
          connectedNodeIds.add(e.data('target'));
        });
        visibleNodes = cy.nodes().filter(function(n) {
          return connectedNodeIds.has(n.id());
        });
      }

      // Pillar filter
      if (pillarVal !== 'all') {
        if (pillarVal === 'ontology') {
          visibleNodes = cy.nodes('[type = "concept"]');
          visibleEdges = cy.edges('[id ^= "ont-rel:"]');
        } else {
          var matchedNodes = cy.nodes('[domain = "' + pillarVal + '"]');
          visibleNodes = matchedNodes;
          var connEdgeIds = new Set();
          matchedNodes.forEach(function(n) {
            n.connectedEdges().forEach(function(e) { connEdgeIds.add(e.id()); });
          });
          visibleEdges = cy.edges().filter(function(e) { return connEdgeIds.has(e.id()); });
        }
      }

      // Apply
      cy.elements().addClass('faded');
      visibleNodes.removeClass('faded');
      visibleEdges.removeClass('faded');

      // Re-style edges by relation
      visibleEdges.forEach(function(e) {
        var rel = e.data('relation');
        var color = RELATION_COLORS[rel] || '#a855f7';
        // Cross-pillar edge detection: source and target belong to different pillars
        var srcP = e.data('sourcePillar');
        var tgtP = e.data('targetPillar');
        var isCross = srcP && tgtP && srcP !== tgtP;
        if (isCross) {
          e.style('line-style', 'dashed');
          e.style('width', 0.8);
          e.style('line-color', '#94a3b8');
          e.style('target-arrow-color', '#94a3b8');
          e.style('opacity', 0.6);
        } else {
          e.style('line-style', 'solid');
          e.style('line-color', color);
          e.style('target-arrow-color', color);
          e.style('width', 0.6);
          e.style('opacity', 0.4);
        }
      });

      if (visibleNodes.length && (pillarVal !== 'all' || relVal !== 'all')) {
        cy.animate({ fit: { eles: visibleNodes, padding: 50 }, duration: 400 });
      }
    }

    function showDetail(node) {
      var d = node.data();
      var el = document.getElementById('graph-detail');
      document.getElementById('detail-title').textContent = d.label;

      var html = '';

      if (d.type === 'document') {
        var domain = d.domain || 'unknown';
        var urlDomain = PILLAR_URL_MAP[domain] || domain;
        var pColor = PILLAR_COLORS[urlDomain] || '#888';
        html += '<span class="detail-badge" style="background:' + pColor + '">' + urlDomain + '</span>';
        if (d.slug) {
          var parts = d.slug.replace(/^\/+/, '').split('/');
          var resolved = PILLAR_URL_MAP[parts[0]] || parts[0];
          var url = '/' + [resolved].concat(parts.slice(1)).join('/') + '/';
          html += '<a href="' + url + '" class="detail-link">View page &rarr;</a>';
        }
        html += '<div class="detail-section"><strong>ID:</strong> ' + d.id + '</div>';
      } else {
        html += '<span class="detail-badge" style="background:#14b8a6">Concept</span>';
        html += '<div class="detail-section"><strong>Connections:</strong> ' + node.degree() + ' edges</div>';

        // Show connected nodes
        var nbrs = node.neighborhood().nodes();
        if (nbrs.length) {
          html += '<div class="detail-section"><strong>Connected to:</strong></div>';
          html += '<div class="detail-neighbors">';
          nbrs.forEach(function(n) {
            var nd = n.data();
            var pColor = PILLAR_COLORS[PILLAR_URL_MAP[nd.domain] || nd.domain] || '#888';
            html += '<span class="detail-neighbor" data-id="' + nd.id + '" style="border-left:3px solid ' + pColor + '">' + nd.label + '</span>';
          });
          html += '</div>';
        }
      }

      document.getElementById('detail-body').innerHTML = html;
      el.style.display = 'block';
      currentActiveNode = node;
    }

    function hideDetail() {
      document.getElementById('graph-detail').style.display = 'none';
      currentActiveNode = null;
    }

    function initGraph(data) {
      rawData = data;
      try { if (window.cytoscapeCoseBilkent) cytoscape.use(window.cytoscapeCoseBilkent); } catch (e) {}
      try { if (window.cytoscapeDagre) cytoscape.use(window.cytoscapeDagre); } catch (e) {}

      cy = cytoscape({
        container: document.getElementById('cy'),
        elements: data,
        style: [
          {
            selector: 'node[type = "document"]',
            style: {
              'background-color': 'data(color)',
              'label': 'data(label)',
              'width': 'data(size)',
              'height': 'data(size)',
              'font-size': '4px',
              'text-valign': 'bottom',
              'text-halign': 'center',
              'text-margin-y': 4,
              'color': '#e2e8f0',
              'text-wrap': 'ellipsis',
              'text-max-width': '80px',
            }
          },
          {
            selector: 'node[type = "concept"]',
            style: {
              'background-color': 'data(color)',
              'shape': 'diamond',
              'label': 'data(label)',
              'width': 'data(size)',
              'height': 'data(size)',
              'font-size': '5px',
              'text-valign': 'top',
              'text-halign': 'center',
              'text-margin-y': -4,
              'color': '#94a3b8',
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 0.5,
              'line-color': '#475569',
              'target-arrow-color': '#475569',
              'curve-style': 'haystack',
              'haystack-radius': 0.5,
              'opacity': 0.4,
            }
          },
          {
            selector: 'node:selected',
            style: {
              'border-width': 2,
              'border-color': '#fbbf24',
            }
          },
          {
            selector: 'node.highlighted',
            style: {
              'border-width': 2,
              'border-color': '#fbbf24',
            }
          },
          {
            selector: 'edge.highlighted',
            style: {
              'width': 1.5,
              'line-color': '#fbbf24',
              'opacity': 0.8,
            }
          },
          {
            selector: 'node.faded, edge.faded',
            style: {
              'opacity': 0.15,
            }
          },
        ],
        layout: {
          name: window.cytoscapeCoseBilkent ? 'cose-bilkent' : 'cose',
          animate: false,
          fit: true,
          padding: 30,
          nodeRepulsion: function() { return 204800; },
          idealEdgeLength: function() { return 80; },
          gravity: 0.25,
          numIter: 1000,
        },
        wheelSensitivity: 0.3,
      });

      // Hover — preview
      var previewTimer = null;
      cy.on('mouseover', 'node', function(evt) {
        var n = evt.target;
        var d = n.data();
        var info = d.label;
        if (d.type === 'document') {
          info += ' [' + (d.domain || '') + ']';
        } else {
          info += ' (' + n.degree() + ' connections)';
        }
        n.style({ 'border-width': 1, 'border-color': '#fbbf24', 'border-opacity': 0.6 });
        document.getElementById('cy').title = info;
      });
      cy.on('mouseout', 'node', function(evt) {
        if (evt.target !== currentActiveNode) {
          evt.target.style({ 'border-width': 0 });
        }
        document.getElementById('cy').title = '';
      });

      // Click — highlight neighbourhood + detail panel
      cy.on('tap', 'node', function(evt) {
        var n = evt.target;
        var nbrs = n.neighborhood().add(n);
        cy.elements().addClass('faded');
        nbrs.removeClass('faded');
        nbrs.addClass('highlighted');
        showDetail(n);
      });
      cy.on('tap', function(evt) {
        if (evt.target === cy) {
          cy.elements().removeClass('faded highlighted');
          hideDetail();
        }
      });

      // Search
      document.getElementById('graph-search').addEventListener('input', function() {
        var q = this.value.toLowerCase().trim();
        cy.elements().removeClass('faded highlighted');
        if (!q) return;
        var matched = cy.nodes().filter(function(n) {
          return n.data('label').toLowerCase().indexOf(q) !== -1;
        });
        if (matched.length) {
          var nbrs = matched.add(matched.neighborhood());
          cy.elements().addClass('faded');
          nbrs.removeClass('faded');
          nbrs.addClass('highlighted');
          cy.animate({ fit: { eles: matched, padding: 50 }, duration: 400 });
        }
      });

      // Pillar filter
      document.getElementById('graph-filter').addEventListener('change', applyFilters);

      // Relation filter
      document.getElementById('graph-relation-filter').addEventListener('change', applyFilters);

      // Layout toggle
      document.getElementById('graph-layout').addEventListener('change', function() {
        runLayout(this.value);
        // Re-apply filters after layout
        setTimeout(applyFilters, 600);
      });

      // Detail close
      document.getElementById('detail-close').addEventListener('click', function() {
        cy.elements().removeClass('faded highlighted');
        hideDetail();
      });

      // Neighbor click in detail panel
      document.getElementById('detail-body').addEventListener('click', function(e) {
        var neighbor = e.target.closest('.detail-neighbor');
        if (neighbor) {
          var nid = neighbor.getAttribute('data-id');
          var node = cy.getElementById(nid);
          if (node.length) {
            node.trigger('tap');
          }
        }
      });
    }

    fetch('/graph-data.json')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        initGraph(data);
      })
      .catch(function(err) {
        document.getElementById('cy').innerHTML =
          '<p style="color:#ef4444;padding:2rem">Failed to load graph data: ' + err.message + '</p>';
      });

    document.getElementById('btn-reset').addEventListener('click', function() {
      if (cy) {
        cy.elements().removeClass('faded highlighted');
        hideDetail();
        document.getElementById('graph-filter').value = 'all';
        document.getElementById('graph-relation-filter').value = 'all';
        document.getElementById('graph-layout').value = 'cose-bilkent';
        document.getElementById('graph-search').value = '';
        runLayout('cose-bilkent');
      }
    });

    document.getElementById('btn-download').addEventListener('click', function() {
      if (cy) {
        var png = cy.png({ full: true, scale: 2 });
        var a = document.createElement('a');
        a.download = 'acacia-knowledge-graph.png';
        a.href = png;
        a.click();
      }
    });
  })();
