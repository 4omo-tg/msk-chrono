<script lang="ts">
    import { push } from "svelte-spa-router";

    let email = "";
    let username = "";
    let password = "";
    let error = "";

    async function handleRegister() {
        try {
            const response = await fetch(
                "http://localhost:8000/api/v1/register",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        email,
                        username,
                        password,
                    }),
                },
            );

            if (!response.ok) {
                throw new Error("Registration failed");
            }

            // Auto login after register
            const loginResponse = await fetch(
                "http://localhost:8000/api/v1/login/access-token",
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

            if (loginResponse.ok) {
                const data = await loginResponse.json();
                localStorage.setItem("token", data.access_token);
                push("/dashboard");
            } else {
                push("/login");
            }
        } catch (e) {
            error =
                "Ошибка регистрации. Имя пользователя или email могут быть заняты.";
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
                Создайте свой аккаунт
            </h2>
        </div>
        <form class="mt-8 space-y-6" on:submit|preventDefault={handleRegister}>
            {#if error}
                <div
                    class="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm text-center"
                >
                    {error}
                </div>
            {/if}
            <div class="rounded-md shadow-sm -space-y-px">
                <div>
                    <label for="email" class="sr-only">Email</label>
                    <input
                        id="email"
                        name="email"
                        type="email"
                        required
                        bind:value={email}
                        class="appearance-none rounded-none relative block w-full px-3 py-2 border border-neutral-700 placeholder-gray-500 text-white bg-neutral-900 rounded-t-md focus:outline-none focus:ring-amber-500 focus:border-amber-500 focus:z-10 sm:text-sm"
                        placeholder="Email адрес"
                    />
                </div>
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
                        class="appearance-none rounded-none relative block w-full px-3 py-2 border border-neutral-700 placeholder-gray-500 text-white bg-neutral-900 border-t-0 focus:outline-none focus:ring-amber-500 focus:border-amber-500 focus:z-10 sm:text-sm"
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
                    Зарегистрироваться
                </button>
            </div>
            <div class="text-center">
                <a
                    href="#/login"
                    class="text-sm text-amber-500 hover:text-amber-400"
                    >Уже есть аккаунт? Войти</a
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
