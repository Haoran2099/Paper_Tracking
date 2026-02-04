/**
 * Paper Tracking - Client-side functionality
 */

(function() {
    'use strict';

    // Get base URL from page
    const BASE_URL = window.SITE_BASE_URL || '';

    // Search functionality
    const searchInput = document.getElementById('search-input');
    const searchDropdown = document.getElementById('search-results');
    let searchIndex = null;
    let debounceTimer = null;

    // Load search index
    async function loadSearchIndex() {
        try {
            const response = await fetch(BASE_URL + '/search_index.json');
            if (response.ok) {
                searchIndex = await response.json();
            }
        } catch (e) {
            console.warn('Could not load search index:', e);
        }
    }

    // Search papers
    function searchPapers(query) {
        if (!searchIndex || query.length < 2) {
            return [];
        }

        const queryLower = query.toLowerCase();
        const results = [];

        for (const paper of searchIndex) {
            let score = 0;

            // Title match (highest priority)
            if (paper.title.toLowerCase().includes(queryLower)) {
                score += 10;
            }

            // Summary match
            if (paper.summary.toLowerCase().includes(queryLower)) {
                score += 5;
            }

            // Tag match
            for (const tag of paper.tags) {
                if (tag.toLowerCase().includes(queryLower)) {
                    score += 3;
                    break;
                }
            }

            // Author match
            if (paper.authors.toLowerCase().includes(queryLower)) {
                score += 2;
            }

            if (score > 0) {
                results.push({ ...paper, searchScore: score });
            }
        }

        // Sort by search relevance, then by paper relevance score
        results.sort((a, b) => {
            if (b.searchScore !== a.searchScore) {
                return b.searchScore - a.searchScore;
            }
            return b.score - a.score;
        });

        return results.slice(0, 8);
    }

    // Render search results
    function renderSearchResults(results) {
        if (results.length === 0) {
            searchDropdown.innerHTML = '<div class="search-result"><p class="search-result-meta">无匹配结果</p></div>';
            return;
        }

        searchDropdown.innerHTML = results.map(paper => `
            <a href="${BASE_URL}/paper/${paper.id.split('v')[0]}/" class="search-result">
                <div class="search-result-title">${escapeHtml(paper.title)}</div>
                <div class="search-result-meta">
                    ${paper.date} · ${paper.category} · ${paper.score}/10
                </div>
            </a>
        `).join('');
    }

    // Escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Handle search input
    function handleSearchInput(e) {
        const query = e.target.value.trim();

        clearTimeout(debounceTimer);

        if (query.length < 2) {
            searchDropdown.classList.remove('active');
            return;
        }

        debounceTimer = setTimeout(() => {
            const results = searchPapers(query);
            renderSearchResults(results);
            searchDropdown.classList.add('active');
        }, 150);
    }

    // Handle click outside
    function handleClickOutside(e) {
        if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
            searchDropdown.classList.remove('active');
        }
    }

    // Initialize
    function init() {
        if (searchInput && searchDropdown) {
            loadSearchIndex();
            searchInput.addEventListener('input', handleSearchInput);
            searchInput.addEventListener('focus', (e) => {
                if (e.target.value.trim().length >= 2) {
                    searchDropdown.classList.add('active');
                }
            });
            document.addEventListener('click', handleClickOutside);
        }

        // Handle keyboard navigation in search
        if (searchDropdown) {
            searchInput.addEventListener('keydown', (e) => {
                const results = searchDropdown.querySelectorAll('.search-result');
                const active = searchDropdown.querySelector('.search-result:focus');

                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    if (!active) {
                        results[0]?.focus();
                    } else {
                        const next = active.nextElementSibling;
                        if (next) next.focus();
                    }
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    if (active) {
                        const prev = active.previousElementSibling;
                        if (prev) {
                            prev.focus();
                        } else {
                            searchInput.focus();
                        }
                    }
                } else if (e.key === 'Escape') {
                    searchDropdown.classList.remove('active');
                    searchInput.blur();
                }
            });
        }
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
