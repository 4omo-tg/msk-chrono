<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { push } from "svelte-spa-router";
    import { onMount } from "svelte";

    let error = "";
    let loading = true;

    onMount(async () => {
        // Parse Telegram auth data from URL query params
        // Handle both direct query params and params after redirect
        let params = new URLSearchParams(window.location.search);
        
        const authData = {
            id: parseInt(params.get('id') || '0'),
            first_name: params.get('first_name') || '',
            last_name: params.get('last_name') || null,
            username: params.get('username') || null,
            photo_url: params.get('photo_url') || null,
            auth_date: parseInt(params.get('auth_date') || '0'),
            hash: params.get('hash') || '',
        };

        if (!authData.id || !authData.hash) {
            error = "Неверные данные авторизации";
            loading = false;
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/api/v1/telegram/widget`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(authData),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Telegram auth failed");
            }

            const data = await response.json();
            localStorage.setItem("token", data.access_token);
            localStorage.removeItem("onboarding_completed");
            
            // Clear URL params and redirect
            window.history.replaceState({}, '', window.location.pathname + '#/dashboard');
            push("/dashboard");
        } catch (e: any) {
            error = e.message || "Ошибка авторизации через Telegram";
            loading = false;
        }
    });
</script>

<div class="min-h-screen bg-neutral-900 flex items-center justify-center py-12 px-4">
    <div class="max-w-md w-full space-y-8 bg-neutral-800 p-8 rounded-2xl border border-white/10 shadow-xl text-center">
        {#if loading}
            <div class="animate-pulse">
                <div class="text-amber-500 text-xl">Авторизация через Telegram...</div>
            </div>
        {:else if error}
            <div class="text-red-500 text-xl">{error}</div>
            <a href="#/register" class="text-amber-500 hover:text-amber-400 block mt-4">
                Попробовать снова
            </a>
        {/if}
    </div>
</div>
