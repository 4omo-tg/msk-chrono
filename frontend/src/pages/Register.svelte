<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { push } from "svelte-spa-router";
    import { onMount, onDestroy } from "svelte";

    let email = "";
    let username = "";
    let password = "";
    let error = "";
    
    // Telegram auth state
    let authStep: 'initial' | 'waiting' | 'code' = 'initial';
    let sessionId = "";
    let botLink = "";
    let telegramCode = "";
    let codeError = "";
    let codeLoading = false;
    let pollInterval: ReturnType<typeof setInterval> | null = null;

    onDestroy(() => {
        if (pollInterval) clearInterval(pollInterval);
    });

    async function initTelegramAuth() {
        try {
            const resp = await fetch(`${API_BASE}/api/v1/telegram/init-auth`, {
                method: 'POST'
            });
            if (resp.ok) {
                const data = await resp.json();
                sessionId = data.session_id;
                botLink = data.bot_link;
                authStep = 'waiting';
                
                // Open bot in new tab
                window.open(botLink, '_blank');
                
                // Start polling for auth status
                startPolling();
            }
        } catch (e) {
            console.error("Failed to init telegram auth", e);
            codeError = "Не удалось создать сессию";
        }
    }

    function startPolling() {
        if (pollInterval) clearInterval(pollInterval);
        
        pollInterval = setInterval(async () => {
            try {
                const resp = await fetch(`${API_BASE}/api/v1/telegram/auth-status/${sessionId}`);
                if (resp.ok) {
                    const data = await resp.json();
                    
                    if (data.status === 'ready' && data.code) {
                        // Auto-fill the code
                        telegramCode = data.code;
                        authStep = 'code';
                        if (pollInterval) clearInterval(pollInterval);
                    } else if (data.status === 'expired') {
                        if (pollInterval) clearInterval(pollInterval);
                        codeError = "Сессия истекла";
                        authStep = 'initial';
                    }
                }
            } catch (e) {
                console.error("Poll error", e);
            }
        }, 2000);
    }

    async function handleCodeSubmit() {
        codeError = "";
        codeLoading = true;
        
        try {
            const response = await fetch(`${API_BASE}/api/v1/telegram/code`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ code: telegramCode.trim() }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Неверный код");
            }

            const data = await response.json();
            localStorage.setItem("token", data.access_token);
            localStorage.removeItem("onboarding_completed");
            push("/dashboard");
        } catch (e: any) {
            codeError = e.message || "Ошибка авторизации";
        } finally {
            codeLoading = false;
        }
    }

    function resetAuth() {
        if (pollInterval) clearInterval(pollInterval);
        authStep = 'initial';
        sessionId = '';
        botLink = '';
        telegramCode = '';
        codeError = '';
    }

    function showCodeInput() {
        if (pollInterval) clearInterval(pollInterval);
        authStep = 'code';
    }

    async function handleRegister() {
        error = "";
        try {
            const response = await fetch(`${API_BASE}/api/v1/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, username, password }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Registration failed");
            }

            // Auto login after register
            const loginResponse = await fetch(`${API_BASE}/api/v1/login/access-token`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: new URLSearchParams({ username, password }),
            });

            if (loginResponse.ok) {
                const data = await loginResponse.json();
                localStorage.setItem("token", data.access_token);
                localStorage.removeItem("onboarding_completed");
                push("/dashboard");
            } else {
                push("/login");
            }
        } catch (e: any) {
            error = e.message || "Ошибка регистрации";
        }
    }
</script>

<div class="min-h-screen bg-neutral-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-neutral-800 p-8 rounded-2xl border border-white/10 shadow-xl">
        <div>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-white">
                Создайте аккаунт
            </h2>
        </div>

        <!-- Telegram Bot Auth -->
        <div class="space-y-4">
            {#if authStep === 'initial'}
                <button
                    on:click={initTelegramAuth}
                    class="w-full flex items-center justify-center gap-3 py-3 px-4 bg-[#2AABEE] hover:bg-[#229ED9] text-white font-medium rounded-lg transition-colors"
                >
                    <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                    </svg>
                    Войти через Telegram
                </button>
                
            {:else if authStep === 'waiting'}
                <div class="text-center space-y-4">
                    <div class="flex justify-center">
                        <div class="animate-pulse">
                            <svg class="w-16 h-16 text-[#2AABEE]" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                            </svg>
                        </div>
                    </div>
                    
                    <p class="text-white font-medium">Ожидание авторизации...</p>
                    <p class="text-gray-400 text-sm">
                        Нажмите <b>Start</b> в боте Telegram
                    </p>
                    
                    <div class="flex flex-col gap-2 pt-2">
                        <a 
                            href={botLink} 
                            target="_blank"
                            class="text-sm text-amber-500 hover:text-amber-400"
                        >
                            Открыть бота снова →
                        </a>
                        <button
                            on:click={showCodeInput}
                            class="text-sm text-gray-500 hover:text-gray-400"
                        >
                            Ввести код вручную
                        </button>
                        <button
                            on:click={resetAuth}
                            class="text-sm text-gray-500 hover:text-gray-400"
                        >
                            Отмена
                        </button>
                    </div>
                </div>
                
            {:else if authStep === 'code'}
                <div class="space-y-4">
                    <p class="text-gray-400 text-sm text-center">
                        Введите код из Telegram:
                    </p>
                    
                    {#if codeError}
                        <div class="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm text-center">
                            {codeError}
                        </div>
                    {/if}
                    
                    <input
                        type="text"
                        bind:value={telegramCode}
                        placeholder="000000"
                        maxlength="6"
                        class="w-full px-4 py-3 text-center text-2xl tracking-[0.5em] font-mono border border-neutral-700 placeholder-gray-600 text-white bg-neutral-900 rounded-lg focus:outline-none focus:ring-amber-500 focus:border-amber-500"
                    />
                    
                    <div class="flex gap-2">
                        <button
                            on:click={resetAuth}
                            class="flex-1 py-2 px-4 border border-neutral-600 text-gray-400 rounded-lg hover:bg-neutral-700 transition-colors"
                        >
                            Назад
                        </button>
                        <button
                            on:click={handleCodeSubmit}
                            disabled={telegramCode.length !== 6 || codeLoading}
                            class="flex-1 py-2 px-4 bg-amber-500 hover:bg-amber-600 disabled:bg-amber-500/50 disabled:cursor-not-allowed text-black font-medium rounded-lg transition-colors"
                        >
                            {codeLoading ? 'Проверка...' : 'Войти'}
                        </button>
                    </div>
                </div>
            {/if}
        </div>

        <!-- Divider -->
        <div class="relative">
            <div class="absolute inset-0 flex items-center">
                <div class="w-full border-t border-neutral-700"></div>
            </div>
            <div class="relative flex justify-center text-sm">
                <span class="px-2 bg-neutral-800 text-gray-400">или с email</span>
            </div>
        </div>

        <form class="space-y-6" on:submit|preventDefault={handleRegister}>
            {#if error}
                <div class="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm text-center">
                    {error}
                </div>
            {/if}
            <div class="rounded-md shadow-sm -space-y-px">
                <div>
                    <input
                        id="email"
                        type="email"
                        required
                        bind:value={email}
                        class="appearance-none rounded-none relative block w-full px-3 py-2 border border-neutral-700 placeholder-gray-500 text-white bg-neutral-900 rounded-t-md focus:outline-none focus:ring-amber-500 focus:border-amber-500 focus:z-10 sm:text-sm"
                        placeholder="Email"
                    />
                </div>
                <div>
                    <input
                        id="username"
                        type="text"
                        required
                        bind:value={username}
                        class="appearance-none rounded-none relative block w-full px-3 py-2 border border-neutral-700 placeholder-gray-500 text-white bg-neutral-900 focus:outline-none focus:ring-amber-500 focus:border-amber-500 focus:z-10 sm:text-sm"
                        placeholder="Имя пользователя"
                    />
                </div>
                <div>
                    <input
                        id="password"
                        type="password"
                        required
                        bind:value={password}
                        class="appearance-none rounded-none relative block w-full px-3 py-2 border border-neutral-700 placeholder-gray-500 text-white bg-neutral-900 rounded-b-md focus:outline-none focus:ring-amber-500 focus:border-amber-500 focus:z-10 sm:text-sm"
                        placeholder="Пароль"
                    />
                </div>
            </div>

            <div>
                <button
                    type="submit"
                    class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-black bg-amber-500 hover:bg-amber-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500"
                >
                    Зарегистрироваться
                </button>
            </div>

            <div class="text-center">
                <a href="#/login" class="text-sm text-amber-500 hover:text-amber-400">
                    Уже есть аккаунт? Войти
                </a>
            </div>
            <div class="text-center">
                <a href="#/" class="text-sm text-gray-500 hover:text-gray-400">
                    На главную
                </a>
            </div>
        </form>
    </div>
</div>
