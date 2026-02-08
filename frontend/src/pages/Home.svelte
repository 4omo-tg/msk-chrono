<script lang="ts">
    import { push } from "svelte-spa-router";

    let isMenuOpen = false;

    function toggleMenu() {
        isMenuOpen = !isMenuOpen;
    }

    const features = [
        {
            icon: "🗺️",
            title: "Пешеходные Маршруты",
            description: "Тщательно разработанные маршруты по историческим местам Москвы с аудиогидом и интерактивными точками"
        },
        {
            icon: "📸",
            title: "Тогда и Сейчас",
            description: "Сравнивайте исторические фотографии с современными видами — погрузитесь в машину времени прямо на улицах города"
        },
        {
            icon: "🏆",
            title: "Награды и Достижения",
            description: "Получайте баллы за пройденные маршруты, открывайте уникальные достижения и соревнуйтесь с друзьями"
        },
        {
            icon: "📍",
            title: "Скрытые Места",
            description: "Откройте для себя малоизвестные дворики, переулки и здания с богатой историей"
        }
    ];

    const routes = [
        {
            title: "Бульварное Кольцо",
            duration: "2.5 часа",
            distance: "9 км",
            points: 15,
            image: "https://images.unsplash.com/photo-1513326738677-b964603b136d?w=400&h=300&fit=crop"
        },
        {
            title: "Замоскворечье",
            duration: "1.5 часа",
            distance: "5 км",
            points: 10,
            image: "https://images.unsplash.com/photo-1520106212299-d99c443e4568?w=400&h=300&fit=crop"
        },
        {
            title: "Китай-город",
            duration: "2 часа",
            distance: "4 км",
            points: 12,
            image: "https://images.unsplash.com/photo-1547448415-e9f5b28e570d?w=400&h=300&fit=crop"
        }
    ];
</script>

<div class="min-h-screen bg-neutral-900 text-white font-sans selection:bg-amber-500 selection:text-black">
    <!-- Navbar -->
    <nav class="fixed top-0 w-full z-50 bg-neutral-900/80 backdrop-blur-md border-b border-white/10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex-shrink-0">
                    <span class="text-2xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent">Moscow Chrono</span>
                </div>

                <!-- Desktop Menu -->
                <div class="hidden md:block">
                    <div class="ml-10 flex items-baseline space-x-4">
                        <a href="#/routes" class="hover:text-amber-400 px-3 py-2 rounded-md text-sm font-medium transition-colors">Маршруты</a>
                        <a href="#/login" class="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-full text-sm font-medium transition-all ml-4">Войти</a>
                        <a href="#/register" class="bg-amber-500 hover:bg-amber-600 text-black px-4 py-2 rounded-full text-sm font-medium transition-all">Регистрация</a>
                    </div>
                </div>

                <!-- Mobile menu button -->
                <div class="md:hidden">
                    <button on:click={toggleMenu} class="text-white p-2">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            {#if isMenuOpen}
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            {:else}
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                            {/if}
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Mobile Menu -->
            {#if isMenuOpen}
                <div class="md:hidden pb-4">
                    <a href="#/routes" class="block px-3 py-2 text-base font-medium hover:text-amber-400">Маршруты</a>
                    <a href="#/login" class="block px-3 py-2 text-base font-medium hover:text-amber-400">Войти</a>
                    <a href="#/register" class="block px-3 py-2 text-base font-medium text-amber-400">Регистрация</a>
                </div>
            {/if}
        </div>
    </nav>

    <!-- Hero Section -->
    <main class="pt-16">
        <div class="relative overflow-hidden">
            <!-- Background Elements -->
            <div class="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[600px] bg-gradient-to-b from-amber-500/10 to-transparent pointer-events-none"></div>

            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center">
                <h1 class="text-5xl md:text-7xl font-extrabold tracking-tight mb-6">
                    <span class="block text-white">Исследуйте Историю</span>
                    <span class="block bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent">Шаг за Шагом</span>
                </h1>
                <p class="mt-4 max-w-2xl mx-auto text-xl text-gray-400 mb-10">
                    Откройте для себя скрытые истории Москвы. Сравнивайте исторические фотографии с современными видами, следуйте по тщательно разработанным пешеходным маршрутам и зарабатывайте награды, исследуя.
                </p>
                <div class="flex flex-col sm:flex-row justify-center gap-4">
                    <a href="#/register" class="bg-amber-500 hover:bg-amber-600 text-black font-bold py-3 px-8 rounded-full text-lg transition-transform hover:scale-105 shadow-lg shadow-amber-500/20">
                        Начать Исследование
                    </a>
                    <a href="#/routes" class="bg-white/10 hover:bg-white/20 text-white font-bold py-3 px-8 rounded-full text-lg transition-all border border-white/20">
                        Смотреть Маршруты
                    </a>
                </div>
            </div>
        </div>

        <!-- Features Section -->
        <section class="py-20 bg-neutral-800/50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center mb-16">
                    <h2 class="text-3xl md:text-4xl font-bold mb-4">Как это работает</h2>
                    <p class="text-gray-400 max-w-2xl mx-auto">Превратите обычную прогулку в увлекательное путешествие во времени</p>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {#each features as feature}
                        <div class="bg-neutral-800 rounded-2xl p-6 hover:bg-neutral-700/50 transition-all hover:-translate-y-1 border border-white/5">
                            <div class="text-4xl mb-4">{feature.icon}</div>
                            <h3 class="text-xl font-semibold mb-2">{feature.title}</h3>
                            <p class="text-gray-400 text-sm">{feature.description}</p>
                        </div>
                    {/each}
                </div>
            </div>
        </section>

        <!-- Popular Routes Section -->
        <section class="py-20">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between items-center mb-12">
                    <div>
                        <h2 class="text-3xl md:text-4xl font-bold mb-2">Популярные Маршруты</h2>
                        <p class="text-gray-400">Начните с наших самых любимых маршрутов</p>
                    </div>
                    <a href="#/routes" class="hidden sm:flex items-center gap-2 text-amber-400 hover:text-amber-300 transition-colors">
                        Все маршруты
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path>
                        </svg>
                    </a>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {#each routes as route}
                        <div class="group bg-neutral-800 rounded-2xl overflow-hidden border border-white/5 hover:border-amber-500/30 transition-all">
                            <div class="relative h-48 overflow-hidden">
                                <img src={route.image} alt={route.title} class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500">
                                <div class="absolute inset-0 bg-gradient-to-t from-neutral-900 to-transparent"></div>
                                <div class="absolute bottom-4 left-4">
                                    <span class="bg-amber-500 text-black text-xs font-bold px-2 py-1 rounded-full">{route.points} точек</span>
                                </div>
                            </div>
                            <div class="p-5">
                                <h3 class="text-xl font-semibold mb-2 group-hover:text-amber-400 transition-colors">{route.title}</h3>
                                <div class="flex items-center gap-4 text-gray-400 text-sm">
                                    <span class="flex items-center gap-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        {route.duration}
                                    </span>
                                    <span class="flex items-center gap-1">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                                        </svg>
                                        {route.distance}
                                    </span>
                                </div>
                            </div>
                        </div>
                    {/each}
                </div>

                <div class="mt-8 text-center sm:hidden">
                    <a href="#/routes" class="text-amber-400 hover:text-amber-300 transition-colors">
                        Смотреть все маршруты →
                    </a>
                </div>
            </div>
        </section>


        <!-- CTA Section -->
        <section class="py-20">
            <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <h2 class="text-3xl md:text-4xl font-bold mb-6">Готовы открыть Москву по-новому?</h2>
                <p class="text-gray-400 text-lg mb-8">
                    Присоединяйтесь к сообществу исследователей и начните своё путешествие по истории города уже сегодня.
                </p>
                <a href="#/register" class="inline-block bg-amber-500 hover:bg-amber-600 text-black font-bold py-4 px-10 rounded-full text-lg transition-transform hover:scale-105 shadow-lg shadow-amber-500/20">
                    Создать аккаунт бесплатно
                </a>
            </div>
        </section>
    </main>

    <!-- Footer -->
    <footer class="bg-neutral-800 border-t border-white/10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
                <div class="md:col-span-2">
                    <span class="text-2xl font-bold bg-gradient-to-r from-amber-400 to-amber-600 bg-clip-text text-transparent">Moscow Chrono</span>
                    <p class="text-gray-400 mt-4 max-w-md">
                        Интерактивная платформа для исследования истории Москвы через пешеходные маршруты, архивные фотографии и увлекательные квесты.
                    </p>
                </div>
                
                <div>
                    <h4 class="font-semibold mb-4">Навигация</h4>
                    <ul class="space-y-2 text-gray-400">
                        <li><a href="#/routes" class="hover:text-amber-400 transition-colors">Маршруты</a></li>
                        <li><a href="#/register" class="hover:text-amber-400 transition-colors">Регистрация</a></li>
                        <li><a href="#/login" class="hover:text-amber-400 transition-colors">Вход</a></li>
                    </ul>
                </div>
                
                <div>
                    <h4 class="font-semibold mb-4">Контакты</h4>
                    <ul class="space-y-2 text-gray-400">
                        <li>
                            <a href="https://t.me/killedblessed" target="_blank" class="hover:text-amber-400 transition-colors flex items-center gap-2">
                                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                                </svg>
                                Telegram
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
            
            <div class="border-t border-white/10 mt-10 pt-8">
                <p class="text-gray-500 text-sm text-center">© 2025 Moscow Chrono</p>
            </div>
        </div>
    </footer>
</div>
