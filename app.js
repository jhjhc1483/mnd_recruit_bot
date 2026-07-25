document.addEventListener('DOMContentLoaded', () => {
    // State management
    let state = {
        posts: [],
        filteredPosts: [],
        activeCategory: 'all', // 'all', 'mnd', 'army'
        searchQuery: '',
        updatedAt: '',
        mndCount: 0,
        armyCount: 0,
        totalCount: 0
    };

    // DOM Elements
    const postsList = document.getElementById('postsList');
    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const resultCount = document.getElementById('resultCount');
    const lastUpdatedBadge = document.getElementById('lastUpdatedBadge');
    const themeToggle = document.getElementById('themeToggle');

    // Stat Elements
    const statAllCount = document.getElementById('statAllCount');
    const statMndCount = document.getElementById('statMndCount');
    const statArmyCount = document.getElementById('statArmyCount');
    const statCards = document.querySelectorAll('.stat-card');
    const tabBtns = document.querySelectorAll('.tab-btn');

    // Init Theme (Default: Light Mode)
    initTheme();

    // Fetch Posts Data
    fetchPosts();

    // Event Listeners
    tabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const category = e.currentTarget.getAttribute('data-tab');
            setCategory(category);
        });
    });

    statCards.forEach(card => {
        card.addEventListener('click', (e) => {
            const category = e.currentTarget.getAttribute('data-category');
            setCategory(category);
        });
    });

    searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value.trim().toLowerCase();
        if (state.searchQuery.length > 0) {
            clearSearchBtn.style.display = 'block';
        } else {
            clearSearchBtn.style.display = 'none';
        }
        applyFilters();
    });

    clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        state.searchQuery = '';
        clearSearchBtn.style.display = 'none';
        applyFilters();
        searchInput.focus();
    });

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.body.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(newTheme);
    });

    // Functions
    async function fetchPosts() {
        try {
            loadingState.style.display = 'flex';
            emptyState.style.display = 'none';
            postsList.innerHTML = '';

            let data;
            try {
                const response = await fetch('data/posts.json?v=' + Date.now());
                if (response.ok) {
                    data = await response.json();
                } else {
                    throw new Error('Static file not found');
                }
            } catch (err) {
                console.warn('Fallback to Vercel Seoul Serverless API (/api/cron)...');
                const apiRes = await fetch('/api/cron');
                data = await apiRes.json();
            }

            state.posts = data.posts || [];
            state.updatedAt = data.updated_at || '';
            state.totalCount = data.total_count || state.posts.length;
            state.mndCount = data.mnd_count || 0;
            state.armyCount = data.army_count || 0;

            updateHeaderStats();
            applyFilters();
        } catch (error) {
            console.error('Error fetching posts:', error);
            loadingState.style.display = 'none';
            emptyState.style.display = 'flex';
            emptyState.querySelector('h3').textContent = '데이터를 불러오지 못했습니다.';
            emptyState.querySelector('p').textContent = '네트워크 연결을 확인하거나 잠시 후 다시 시도해 주세요.';
        }
    }

    function updateHeaderStats() {
        statAllCount.textContent = state.totalCount;
        statMndCount.textContent = state.mndCount;
        statArmyCount.textContent = state.armyCount;

        if (state.updatedAt) {
            lastUpdatedBadge.innerHTML = `
                <i class="fa-solid fa-clock"></i>
                <span>최종 갱신: ${state.updatedAt}</span>
            `;
        }
    }

    function setCategory(category) {
        state.activeCategory = category;

        // Update Tab UI
        tabBtns.forEach(btn => {
            if (btn.getAttribute('data-tab') === category) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Update Stat Cards UI
        statCards.forEach(card => {
            if (card.getAttribute('data-category') === category) {
                card.classList.add('active');
            } else {
                card.classList.remove('active');
            }
        });

        applyFilters();
    }

    function applyFilters() {
        let list = [...state.posts];

        // Category Filter
        if (state.activeCategory !== 'all') {
            list = list.filter(post => post.category_code === state.activeCategory);
        }

        // Search Filter
        if (state.searchQuery) {
            list = list.filter(post => {
                const titleMatch = post.title && post.title.toLowerCase().includes(state.searchQuery);
                const authorMatch = post.author && post.author.toLowerCase().includes(state.searchQuery);
                const categoryMatch = post.category && post.category.toLowerCase().includes(state.searchQuery);
                return titleMatch || authorMatch || categoryMatch;
            });
        }

        state.filteredPosts = list;
        renderPosts();
    }

    function renderPosts() {
        loadingState.style.display = 'none';

        if (state.filteredPosts.length === 0) {
            emptyState.style.display = 'flex';
            postsList.style.display = 'none';
            resultCount.textContent = '검색 조건에 맞는 게시물이 없습니다.';
            return;
        }

        emptyState.style.display = 'none';
        postsList.style.display = 'flex';
        resultCount.textContent = `총 ${state.filteredPosts.length}개의 게시물이 검색되었습니다.`;

        const html = state.filteredPosts.map(post => {
            const isMnd = post.category_code === 'mnd';
            const catBadgeClass = isMnd ? 'mnd' : 'army';
            const authorIcon = isMnd ? 'fa-building-columns' : 'fa-person-military-rifle';

            return `
                <a href="${post.link}" target="_blank" rel="noopener noreferrer" class="post-card" id="post-${post.id}">
                    <div class="post-main">
                        <div class="post-meta-top">
                            <span class="category-tag ${catBadgeClass}">${post.category}</span>
                            ${post.author ? `
                                <span class="author-tag">
                                    <i class="fa-solid ${authorIcon}"></i> ${escapeHtml(post.author)}
                                </span>
                            ` : ''}
                        </div>
                        <h2 class="post-title">${escapeHtml(post.title)}</h2>
                        <div class="post-meta-bottom">
                            <span class="post-date">
                                <i class="fa-regular fa-calendar"></i> ${post.date || '날짜 미상'}
                            </span>
                            ${post.views ? `
                                <span class="post-views">
                                    <i class="fa-regular fa-eye"></i> ${post.views}
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    <div class="post-action" title="원문 보기">
                        <i class="fa-solid fa-arrow-right"></i>
                    </div>
                </a>
            `;
        }).join('');

        postsList.innerHTML = html;
    }

    function initTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        setTheme(savedTheme);
    }

    function setTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        const icon = themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.className = 'fa-solid fa-sun';
            themeToggle.title = '라이트 모드로 변경';
        } else {
            icon.className = 'fa-solid fa-moon';
            themeToggle.title = '다크 모드로 변경';
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
