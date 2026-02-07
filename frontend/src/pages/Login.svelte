<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";

    let username = "";
    let password = "";
    let error = "";
    let telegramBotUsername = "moscow_chrono_bot";

    onMount(async () => {
        // Get bot username from backend
        try {
            const resp = await fetch(`${API_BASE}/api/v1/telegram/bot-username`);
            if (resp.ok) {
                const data = await resp.json();
                telegramBotUsername = data.bot_username;
            }
        } catch (e) {
            console.log("Could not fetch telegram bot username");
        }

        // Setup Telegram Login Widget callback
        (window as any).onTelegramAuth = async (user: any) => {
            try {
                const response = await fetch(`${API_BASE}/api/v1/telegram`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(user),
                });

                if (!response.ok) {
                    throw new Error("Telegram auth failed");
                }

                const data = await response.json();
                localStorage.setItem("token", data.access_token);
                push("/routes");
            } catch (e) {
                error = "Ошибка входа через Telegram";
            }
        };

        // Load Telegram widget script
        const script = document.createElement("script");
        script.src = "https://telegram.org/js/telegram-widget.js?22";
        script.setAttribute("data-telegram-login", telegramBotUsername);
        script.setAttribute("data-size", "large");
        script.setAttribute("data-onauth", "onTelegramAuth(user)");
        script.setAttribute("data-request-access", "write");
        script.async = true;
        
        const container = document.getElementById("telegram-login-container");
        if (container) {
            container.appendChild(script);
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
            <div class="flex justify-center">
                <div id="telegram-login-container"></div>
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
