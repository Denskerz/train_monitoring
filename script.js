/**
 * RailTrack-Monitor: Основная логика управления состоянием и рендерингом
 */

// 1. Mock-данные для имитации API
const MOCK_TRAINS = [
    { id: '042А', from: 'Москва', to: 'Санкт-Петербург', departure: '14:20', arrival: '18:50', duration: '4ч 30м', seats: { coupe: 12, economy: 45 } },
    { id: '116С', from: 'Москва', to: 'Санкт-Петербург', departure: '16:00', arrival: '23:45', duration: '7ч 45м', seats: { coupe: 2, economy: 8 } },
    { id: '754В', from: 'Москва', to: 'Казань', departure: '19:15', arrival: '07:30', duration: '12ч 15м', seats: { coupe: 0, economy: 15 } },
    { id: '002Й', from: 'Москва', to: 'Самара', departure: '21:00', arrival: '10:00', duration: '13ч 00м', seats: { coupe: 25, economy: 110 } }
];

// 2. Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.querySelector('#search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }
});

/**
 * Обработчик формы поиска
 */
async function handleSearch(event) {
    event.preventDefault();
    
    // Constraint Validation API
    if (!event.target.checkValidity()) {
        event.target.reportValidity();
        return;
    }

    const formData = new FormData(event.target);
    const searchParams = Object.fromEntries(formData.entries());

    renderSkeletons(); // Показываем состояние загрузки
    
    try {
        const results = await fetchTrains(searchParams);
        renderTickets(results);
    } catch (error) {
        console.error("Ошибка при получении данных:", error);
    }
}

/**
 * Имитация запроса к API с задержкой
 */
function fetchTrains(params) {
    return new Promise((resolve) => {
        setTimeout(() => {
            const filtered = MOCK_TRAINS.filter(train => 
                train.from.toLowerCase().includes(params.from.toLowerCase()) &&
                train.to.toLowerCase().includes(params.to.toLowerCase())
            );
            resolve(filtered);
        }, 1500); // Задержка 1.5с согласно ТЗ
    });
}

/**
 * Рендеринг Skeleton-элементов
 */
function renderSkeletons() {
    const grid = document.getElementById('results-grid');
    grid.innerHTML = Array(3).fill(0).map(() => `
        <div class="bg-slate-800/50 border border-slate-700 p-6 rounded-2xl animate-pulse">
            <div class="h-6 bg-slate-700 rounded w-1/4 mb-4"></div>
            <div class="h-10 bg-slate-700 rounded mb-4"></div>
            <div class="flex gap-4">
                <div class="h-8 bg-slate-700 rounded w-full"></div>
                <div class="h-8 bg-slate-700 rounded w-full"></div>
            </div>
        </div>
    `).join('');
}

/**
 * Основная функция рендеринга карточек билетов
 */
function renderTickets(tickets) {
    const grid = document.getElementById('results-grid');
    
    if (tickets.length === 0) {
        grid.innerHTML = `<p class="col-span-full text-center text-slate-400 py-10">Поезда не найдены. Попробуйте изменить параметры поиска.</p>`;
        return;
    }

    grid.innerHTML = tickets.map(train => {
        const totalSeats = train.seats.coupe + train.seats.economy;
        
        // Условное форматирование статуса (Emerald/Amber/Rose)
        let statusColor = 'text-emerald-500';
        let statusText = 'Места есть';
        
        if (totalSeats === 0) {
            statusColor = 'text-rose-500';
            statusText = 'Мест нет';
        } else if (totalSeats < 15) {
            statusColor = 'text-amber-400';
            statusText = 'Мало мест';
        }

        return `
            <div class="glass-card bg-slate-800/40 backdrop-blur-xl border border-slate-700/50 p-6 rounded-2xl hover:border-indigo-500/50 transition-all duration-300 group">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <span class="text-xs font-mono text-indigo-400 bg-indigo-500/10 px-2 py-1 rounded">№ ${train.id}</span>
                        <h3 class="text-xl font-bold text-white mt-2">${train.from} → ${train.to}</h3>
                    </div>
                    <div class="flex items-center gap-2 ${statusColor} text-sm font-medium animate-pulse-soft">
                        <span class="w-2 h-2 rounded-full bg-current"></span>
                        ${statusText}
                    </div>
                </div>

                <div class="flex items-center gap-8 mb-6 text-slate-300">
                    <div>
                        <div class="text-2xl font-semibold text-white">${train.departure}</div>
                        <div class="text-xs text-slate-500 uppercase tracking-wider">Отправление</div>
                    </div>
                    <div class="flex-1 border-t border-dashed border-slate-600 relative">
                        <span class="absolute -top-3 left-1/2 -translate-x-1/2 bg-slate-900 px-2 text-[10px] text-slate-500 italic">${train.duration}</span>
                    </div>
                    <div class="text-right">
                        <div class="text-2xl font-semibold text-white">${train.arrival}</div>
                        <div class="text-xs text-slate-500 uppercase tracking-wider">Прибытие</div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <button class="flex flex-col items-center p-3 rounded-xl bg-slate-900/50 border border-slate-700 hover:bg-slate-700/50 transition-colors">
                        <span class="text-xs text-slate-400 uppercase">Купе</span>
                        <span class="font-bold ${train.seats.coupe > 0 ? 'text-white' : 'text-slate-600'}">${train.seats.coupe}</span>
                    </button>
                    <button class="flex flex-col items-center p-3 rounded-xl bg-slate-900/50 border border-slate-700 hover:bg-slate-700/50 transition-colors">
                        <span class="text-xs text-slate-400 uppercase">Плацкарт</span>
                        <span class="font-bold ${train.seats.economy > 0 ? 'text-white' : 'text-slate-600'}">${train.seats.economy}</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');

    // Инициализация иконок (если используется Lucide)
    if (window.lucide) {
        lucide.createIcons();
    }
}
