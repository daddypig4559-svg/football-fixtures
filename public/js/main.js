
// 足球賽事數據中心 - JavaScript功能

document.addEventListener('DOMContentLoaded', function() {
    // 初始化功能
    initFilters();
    initSearch();
    initDateNavigation();
    initLeagueNavigation();
    
    // 更新時間
    updateLiveTime();
    setInterval(updateLiveTime, 60000);
    
    // 加載JSON數據（如果可用）
    loadJSONData();
});

// 初始化篩選器
function initFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterValue = this.getAttribute('data-filter');
            
            // 更新按鈕狀態
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // 篩選賽事
            filterFixtures(filterValue);
        });
    });
}

// 篩選賽事
function filterFixtures(filterType) {
    const fixtures = document.querySelectorAll('.fixture-card');
    
    fixtures.forEach(fixture => {
        switch(filterType) {
            case 'all':
                fixture.style.display = 'block';
                break;
            case 'today':
                const fixtureDate = fixture.getAttribute('data-date');
                const today = new Date().toISOString().split('T')[0];
                fixture.style.display = fixtureDate === today ? 'block' : 'none';
                break;
            case 'tomorrow':
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                const tomorrowStr = tomorrow.toISOString().split('T')[0];
                const fixtureDate2 = fixture.getAttribute('data-date');
                fixture.style.display = fixtureDate2 === tomorrowStr ? 'block' : 'none';
                break;
            case 'live':
                const status = fixture.getAttribute('data-status');
                fixture.style.display = status === 'live' ? 'block' : 'none';
                break;
            default:
                fixture.style.display = 'block';
        }
    });
}

// 初始化搜索
function initSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase().trim();
        
        if (searchTerm.length === 0) {
            // 顯示所有賽事
            document.querySelectorAll('.fixture-card').forEach(card => {
                card.style.display = 'block';
            });
            return;
        }
        
        // 搜索賽事
        document.querySelectorAll('.fixture-card').forEach(card => {
            const homeTeam = card.getAttribute('data-home-team').toLowerCase();
            const awayTeam = card.getAttribute('data-away-team').toLowerCase();
            const league = card.getAttribute('data-league').toLowerCase();
            
            if (homeTeam.includes(searchTerm) || 
                awayTeam.includes(searchTerm) || 
                league.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
}

// 初始化日期導航
function initDateNavigation() {
    const dateItems = document.querySelectorAll('.date-item');
    
    dateItems.forEach(item => {
        item.addEventListener('click', function() {
            const date = this.getAttribute('data-date');
            
            // 更新按鈕狀態
            dateItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // 篩選該日期的賽事
            document.querySelectorAll('.fixture-card').forEach(card => {
                const cardDate = card.getAttribute('data-date');
                card.style.display = cardDate === date ? 'block' : 'none';
            });
        });
    });
}

// 初始化聯賽導航
function initLeagueNavigation() {
    const leagueItems = document.querySelectorAll('.league-item');
    
    leagueItems.forEach(item => {
        item.addEventListener('click', function() {
            const leagueId = this.getAttribute('data-league-id');
            
            // 更新按鈕狀態
            leagueItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // 篩選該聯賽的賽事
            document.querySelectorAll('.fixture-card').forEach(card => {
                const cardLeagueId = card.getAttribute('data-league-id');
                card.style.display = cardLeagueId === leagueId ? 'block' : 'none';
            });
        });
    });
}

// 更新實時時間
function updateLiveTime() {
    const timeElements = document.querySelectorAll('.live-time');
    
    timeElements.forEach(element => {
        const timestamp = parseInt(element.getAttribute('data-timestamp'));
        if (timestamp) {
            const now = Math.floor(Date.now() / 1000);
            const diff = now - timestamp;
            
            if (diff < 0) {
                // 比賽尚未開始
                const hours = Math.floor(-diff / 3600);
                const minutes = Math.floor((-diff % 3600) / 60);
                
                if (hours > 0) {
                    element.textContent = `${hours}小時${minutes}分鐘後開始`;
                } else {
                    element.textContent = `${minutes}分鐘後開始`;
                }
                element.className = 'live-time upcoming';
            } else if (diff < 7200) { // 2小時內，認為是比賽中
                const minutes = Math.floor(diff / 60);
                element.textContent = `${minutes}'`;
                element.className = 'live-time live';
            } else {
                element.textContent = '已結束';
                element.className = 'live-time finished';
            }
        }
    });
}

// 加載JSON數據
function loadJSONData() {
    // 嘗試加載API數據
    fetch('/api/fixtures.json')
        .then(response => response.json())
        .then(data => {
            console.log('成功加載賽事數據:', data);
            // 可以在這裡處理動態加載的數據
        })
        .catch(error => {
            console.log('無法加載API數據:', error);
        });
}

// 分享功能
function shareFixture(fixtureId) {
    const fixture = document.querySelector(`[data-fixture-id="${fixtureId}"]`);
    if (!fixture) return;
    
    const homeTeam = fixture.getAttribute('data-home-team');
    const awayTeam = fixture.getAttribute('data-away-team');
    const league = fixture.getAttribute('data-league');
    const time = fixture.getAttribute('data-time');
    
    const shareText = `📅 ${league}: ${homeTeam} vs ${awayTeam} - ${time}`;
    
    // 嘗試使用Web Share API
    if (navigator.share) {
        navigator.share({
            title: '足球賽事',
            text: shareText,
            url: window.location.href
        });
    } else {
        // 降級方案：複製到剪貼板
        navigator.clipboard.writeText(shareText)
            .then(() => alert('賽事信息已複製到剪貼板！'))
            .catch(err => console.error('複製失敗:', err));
    }
}
