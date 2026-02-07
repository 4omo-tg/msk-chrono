<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";

    let username = "";
    let password = "";
    let telegramCode = "";
    let error = "";
    let telegramBotUsername = "moscow_chrono_bot";
    let showTelegramInput = false;
    let telegramLoading = false;

    onMount(async () => {
        try {
            const resp = await fetch(`${API_BASE}/api/v1/telegram/bot-username`);
            if (resp.ok) {
                const data = await resp.json();
                telegramBotUsername = data.bot_username;
            }
        } catch (e) {
            console.log("Could not fetch telegram bot username");
        }
    });

    async function handleLogin() {
        try {
            const response = await fetch(
                `${API_BASE}/api/v1/login/access-token`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: new URLSearchParams({
                        username,
                        password,
                    }),
                },
            );

            if (!response.ok) {
                throw new Error("Invalid credentials");
            }

            const data = await response.json();
            localStorage.setItem("token", data.access_token);
            push("/routes");
        } catch (e) {
            error =
                "Ошибка входа. Пожалуйста, проверьте имя пользователя и пароль.";
        }
    }

    async function handleTelegramLogin() {
        if (!telegramCode.trim()) {
            error = "Введите код из Telegram";
            return;
        }
        
        telegramLoading = true;
        error = "";
        
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
                throw new Error(data.detail || "Telegram auth failed");
            }

            const data = await response.json();
            localStorage.setItem("token", data.access_token);
            push("/routes");
        } catch (e: any) {
            error = e.message || "Ошибка входа через Telegram";
        } finally {
            telegramLoading = false;
        }
    }

    function openTelegramBot() {
        window.open(`https://t.me/${telegramBotUsername}`, '_blank');
        showTelegramInput = true;
    }
</script>

<div
    class="min-h-screen bg-neutral-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8"
>
    <div
        class="max-w-md w-full space-y-8 bg-neutral-800 p-8 rounded-2xl border border-white/10 shadow-xl"
    >
        <div>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-white">
                Войдите в свой аккаунт
            </h2>
        </div>
        <form class="mt-8 space-y-6" on:submit|preventDefault={handleLogin}>
            {#if error}
                <div
                    class="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm text-center"
                >
                    {error}
                </div>
            {/if}
            <div class="rounded-md shadow-sm -space-y-px">
                <div>
                    <label for="username" class="sr-only"
                        >Имя пользователя</label
                    >
                    <input
                        id="username"
                        name="username"
                        type="text"
                        required
                        bind:value={username}
                        class="appearance-none rounded-none relative block w-full px-3 py-2 border border-neutral-700 placeholder-gray-500 text-white bg-neutral-900 rounded-t-md focus:outline-none focus:ring-amber-500 focus:border-amber-500 focus:z-10 sm:text-sm"
                        placeholder="Имя пользователя"
                    />
                </div>
                <div>
                    <label for="password" class="sr-only">Пароль</label>
                    <input
                        id="password"
                        name="password"
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
                    Войти
                </button>
            </div>

            <!-- Divider -->
            <div class="relative">
                <div class="absolute inset-0 flex items-center">
                    <div class="w-full border-t border-neutral-700"></div>
                </div>
                <div class="relative flex justify-center text-sm">
                    <span class="px-2 bg-neutral-800 text-gray-400">или</span>
                </div>
            </div>

            <!-- Telegram Login -->
            <div class="space-y-3">
                {#if !showTelegramInput}
                    <button
                        type="button"
                        on:click={openTelegramBot}
                        class="w-full flex items-center justify-center gap-2 py-2 px-4 border border-[#0088cc] text-sm font-medium rounded-md text-white bg-[#0088cc] hover:bg-[#0077b5] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#0088cc] transition-colors"
                    >
                        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                        </svg>
                        Войти через Telegram
                    </button>
                {:else}
                    <div class="text-center text-sm text-gray-400 mb-2">
                        Получите код в 
                        <a href="https://t.me/{telegramBotUsername}" target="_blank" class="text-[#0088cc] hover:underline">@{telegramBotUsername}</a>
                    </div>
                    <div class="flex gap-2">
                        <input
                            type="text"
                            bind:value={telegramCode}
                            placeholder="Введите код"
                            maxlength="6"
                            class="flex-1 px-3 py-2 border border-neutral-700 placeholder-gray-500 text-white bg-neutral-900 rounded-md focus:outline-none focus:ring-amber-500 focus:border-amber-500 sm:text-sm text-center tracking-widest font-mono text-lg"
                        />
                        <button
                            type="button"
                            on:click={handleTelegramLogin}
                            disabled={telegramLoading}
                            class="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-[#0088cc] hover:bg-[#0077b5] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#0088cc] disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {telegramLoading ? '…' : '→'}
                        </button>
                    </div>
                {/if}
            </div>

            <div class="text-center">
                <a
                    href="#/register"
                    class="text-sm text-amber-500 hover:text-amber-400"
                    >Нет аккаунта? Зарегистрироваться</a
                >
            </div>
            <div class="text-center">
                <a href="#/" class="text-sm text-gray-500 hover:text-gray-400"
                    >На главную</a
                >
            </div>
        </form>
    </div>
</div>
