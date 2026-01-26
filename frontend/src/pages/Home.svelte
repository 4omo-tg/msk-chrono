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

        <!-- Stats Section -->
        <section class="py-16 bg-gradient-to-r from-amber-500/10 via-amber-600/5 to-amber-500/10">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
                    <div>
                        <div class="text-4xl md:text-5xl font-bold text-amber-400 mb-2">50+</div>
                        <div class="text-gray-400">Маршрутов</div>
                    </div>
                    <div>
                        <div class="text-4xl md:text-5xl font-bold text-amber-400 mb-2">500+</div>
                        <div class="text-gray-400">Исторических точек</div>
                    </div>
                    <div>
                        <div class="text-4xl md:text-5xl font-bold text-amber-400 mb-2">10K+</div>
                        <div class="text-gray-400">Исследователей</div>
                    </div>
                    <div>
                        <div class="text-4xl md:text-5xl font-bold text-amber-400 mb-2">1000+</div>
                        <div class="text-gray-400">Архивных фото</div>
                    </div>
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
                        <li>info@moscowchrono.ru</li>
                        <li>Москва, Россия</li>
                    </ul>
                </div>
            </div>
            
            <div class="border-t border-white/10 mt-10 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
                <p class="text-gray-500 text-sm">© 2025 Moscow Chrono. Все права защищены.</p>
                <div class="flex gap-4">
                    <a href="#" class="text-gray-400 hover:text-amber-400 transition-colors">
                        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"></path>
                        </svg>
                    </a>
                    <a href="#" class="text-gray-400 hover:text-amber-400 transition-colors">
                        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"></path>
                        </svg>
                    </a>
                    <a href="#" class="text-gray-400 hover:text-amber-400 transition-colors">
                        <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M19.54 0c1.356 0 2.46 1.104 2.46 2.472v19.056c0 1.368-1.104 2.472-2.46 2.472h-15.08c-1.356 0-2.46-1.104-2.46-2.472v-19.056c0-1.368 1.104-2.472 2.46-2.472h15.08zm-4.632 15.672c2.652-.084 3.312-1.824 3.312-4.316 0-1.332-.468-2.544-1.26-3.456.132-.324.18-.684.18-1.068 0-.612-.168-1.14-.42-1.668-.468 0-.852.108-1.62.468-.384.18-.924.444-1.548.78-.492-.084-1.008-.144-1.536-.144-.54 0-1.068.06-1.572.156-.624-.348-1.164-.612-1.536-.792-.768-.36-1.152-.468-1.62-.468-.252.528-.42 1.056-.42 1.668 0 .384.048.744.18 1.068-.792.912-1.26 2.124-1.26 3.456 0 2.484.672 4.236 3.312 4.32-.312.324-.504.756-.564 1.26-.3.132-.66.216-1.068.216-.612 0-1.188-.324-1.548-.876-.3-.456-.792-.768-1.272-.828l-.336.012c-.228.024-.3.264-.084.42.264.192.516.456.672.756.228.432.54.768.972.924.36.132.756.204 1.14.204.384 0 .804-.06 1.164-.192v2.16c0 .36-.24.78-.852.648-4.908-1.632-8.448-6.264-8.448-11.64 0-6.828 5.532-12.36 12.36-12.36 6.828 0 12.36 5.532 12.36 12.36 0 5.376-3.432 10.008-8.208 11.652-.66.132-.996-.276-.996-.648v-3.048c0-.924-.312-1.524-.66-1.836z"></path>
                        </svg>
                    </a>
                </div>
            </div>
        </div>
    </footer>
</div>
