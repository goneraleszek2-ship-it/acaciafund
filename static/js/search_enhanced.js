/**
 * Enhanced Search Module
 * Instant search with 0-character minimum, unified across all content types
 */

(function() {
  'use strict';

  const SEARCH_KEY = 'acacia_search_v1';
  const SEARCH_TIMEOUT = 150;
  const MIN_CHARS = 0; // Changed from 2 to 0 for instant search

  let debounceTimer = null;
  let currentResults = null;

  // Initialize search
  function init() {
    const searchTrigger = document.getElementById('search-trigger');
    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    const searchClose = document.getElementById('search-close');

    if (!searchTrigger || !searchInput || !searchResults) return;

    // Load recent searches
    loadRecentSearches();

    // Search trigger click
    searchTrigger.addEventListener('click', () => {
      searchInput.focus();
      showSearch();
    });

    // Input handling
    searchInput.addEventListener('input', handleInput);
    searchInput.addEventListener('keydown', handleKeydown);

    // Close button
    if (searchClose) {
      searchClose.addEventListener('click', hideSearch);
    }

    // ESC to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') hideSearch();
    });

    // Click outside to close
    document.addEventListener('click', (e) => {
      if (searchResults.classList.contains('active') && 
          !searchResults.contains(e.target) && 
          !searchTrigger.contains(e.target)) {
        hideSearch();
      }
    });

    // Show keyboard shortcut hint on focus
    searchInput.addEventListener('focus', () => {
      searchInput.setAttribute('aria-label', 'Search research, lessons, and knowledge');
    });
  }

  function handleInput(e) {
    const query = e.target.value.trim();
    
    if (!query) {
      hideSearch();
      return;
    }

    // Debounce search
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      performSearch(query);
    }, SEARCH_TIMEOUT);
  }

  function handleKeydown(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (currentResults && currentResults.length > 0 && !currentResults.activeItem) {
        currentResults.activeItem = 0;
        highlightResult(0);
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (currentResults && currentResults.activeItem !== undefined && currentResults.activeItem > 0) {
        currentResults.activeItem--;
        highlightResult(currentResults.activeItem);
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (currentResults && currentResults.activeItem !== undefined) {
        navigateToResult(currentResults.activeItem);
      } else if (query) {
        navigateToSearch(query);
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      if (currentResults && currentResults.length > 0) {
        navigateToResult(0);
      }
    }
  }

  function performSearch(query) {
    // In a real implementation, this would call a search API
    // For now, we'll simulate with static data or fetch from search-index.json
    
    // Fetch from search index if available
    fetch('/search/search-index.json')
      .then(res => res.json())
      .then(index => {
        const results = searchIndex(query, index);
        displayResults(results);
      })
      .catch(() => {
        // Fallback to client-side search if index not available
        const results = searchClientSide(query);
        displayResults(results);
      });
  }

  function searchIndex(query, index) {
    if (!query || query.length < MIN_CHARS) return [];
    
    const results = [];
    const queryLower = query.toLowerCase();
    
    // Search through index entries
    for (const [slug, entry] of Object.entries(index)) {
      const title = entry.title || '';
      const description = entry.description || '';
      
      if (title.toLowerCase().includes(queryLower) || 
          description.toLowerCase().includes(queryLower)) {
        
        results.push({
          slug,
          title,
          description,
          type: entry.type || 'research',
          pillar: entry.pillar || 'general',
          sqi: entry.sqi || 0.5,
          date: entry.date || '',
          url: `/${slug}/`
        });
      }
    }
    
    // Sort by relevance
    return results.sort((a, b) => {
      const scoreA = relevanceScore(a.title, a.description, query);
      const scoreB = relevanceScore(b.title, b.description, query);
      return scoreB - scoreA;
    }).slice(0, 10);
  }

  function searchClientSide(query) {
    // Fallback client-side search
    const results = [];
    
    // Get all links from the page
    document.querySelectorAll('a[href^="/"]').forEach(link => {
      const href = link.getAttribute('href');
      if (href.startsWith('/')) {
        results.push({
          slug: href.substring(1),
          title: link.textContent.trim().substring(0, 60),
          description: '',
          type: 'page',
          pillar: 'general',
          sqi: 0.5,
          url: href
        });
      }
    });
    
    return results.filter(r => r.title.toLowerCase().includes(query.toLowerCase())).slice(0, 10);
  }

  function relevanceScore(title, description, query) {
    let score = 0;
    const queryLower = query.toLowerCase();
    const titleLower = title.toLowerCase();
    const descLower = description.toLowerCase();
    
    // Title match is worth more
    if (titleLower.includes(queryLower)) score += 10;
    
    // First word match
    const words = queryLower.split(/\s+/);
    for (const word of words) {
      if (titleLower.startsWith(word)) score += 5;
      if (descLower.startsWith(word)) score += 3;
    }
    
    // Exact match bonus
    if (titleLower === queryLower) score += 20;
    
    return score;
  }

  function displayResults(results) {
    currentResults = { results, activeItem: undefined };
    
    const searchResults = document.getElementById('search-results');
    if (!searchResults) return;
    
    if (results.length === 0) {
      searchResults.innerHTML = `
        <div class="p-4 text-center text-gray-500">
          No results found for "${currentQuery}"
        </div>
      `;
      searchResults.classList.add('active');
      return;
    }
    
    searchResults.innerHTML = results.map((result, index) => `
      <div class="search-result-item" data-slug="${result.slug}" data-type="${result.type}" data-sqi="${result.sqi}">
        <div class="search-result-title">${result.title}</div>
        <div class="search-result-meta">
          ${result.type === 'research' ? 'Research' : result.type}
          ${result.pillar ? ` • ${result.pillar.charAt(0).toUpperCase() + result.pillar.slice(1)}` : ''}
          ${result.sqi ? ` <span class="search-result-sqi">SQI: ${result.sqi.toFixed(2)}</span>` : ''}
        </div>
      </div>
    `).join('');
    
    // Add click handlers
    searchResults.querySelectorAll('.search-result-item').forEach((item, index) => {
      item.addEventListener('click', () => {
        navigateToResult(index);
      });
      
      item.addEventListener('mouseenter', () => {
        searchResults.querySelectorAll('.search-result-item').forEach(i => i.classList.remove('bg-gray-800'));
        item.classList.add('bg-gray-800');
      });
      
      item.addEventListener('mouseleave', () => {
        item.classList.remove('bg-gray-800');
      });
    });
    
    searchResults.classList.add('active');
  }

  function highlightResult(index) {
    if (!currentResults) return;
    
    const items = document.querySelectorAll('.search-result-item');
    items.forEach((item, i) => {
      item.classList.toggle('bg-gray-800', i === index);
    });
    
    currentResults.activeItem = index;
  }

  function navigateToResult(index) {
    if (!currentResults || index === undefined || index >= currentResults.results.length) return;
    
    const result = currentResults.results[index];
    window.location.href = result.url;
    hideSearch();
  }

  function navigateToSearch(query) {
    const searchUrl = `/search/?q=${encodeURIComponent(query)}`;
    window.location.href = searchUrl;
    hideSearch();
  }

  function showSearch() {
    const searchResults = document.getElementById('search-results');
    if (searchResults) {
      searchResults.classList.add('active');
    }
  }

  function hideSearch() {
    const searchResults = document.getElementById('search-results');
    if (searchResults) {
      searchResults.classList.remove('active');
      currentResults = null;
    }
  }

  function loadRecentSearches() {
    const recent = JSON.parse(localStorage.getItem(SEARCH_KEY) || '[]');
    const searchInput = document.getElementById('search-input');
    if (searchInput && recent.length > 0) {
      searchInput.setAttribute('data-recent', JSON.stringify(recent.slice(0, 3)));
    }
  }

  // Save recent searches
  document.addEventListener('click', (e) => {
    if (e.target.closest('.search-result-item')) {
      const slug = e.target.closest('.search-result-item').dataset.slug;
      let recent = JSON.parse(localStorage.getItem(SEARCH_KEY) || '[]');
      recent = recent.filter(s => s !== slug);
      recent.unshift(slug);
      recent = recent.slice(0, 10);
      localStorage.setItem(SEARCH_KEY, JSON.stringify(recent));
    }
  });

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose for external use
  window.AcademiaSearch = {
    hide: hideSearch,
    perform: performSearch
  };

})();
