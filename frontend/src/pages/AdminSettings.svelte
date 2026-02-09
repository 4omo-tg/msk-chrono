<script lang="ts">
    import { onMount } from "svelte";
    import { push } from "svelte-spa-router";
    import { apiGet, apiPut, isAuthenticated } from "../lib/api";
    import {
        ArrowLeft, Settings, Key, Bot, Clock, Loader2, Save, Check, Eye, EyeOff,
        Sparkles, Server, Zap
    } from "lucide-svelte";

    interface Setting {
        key: string;
        value: string;
        has_value: boolean;
    }

    let settings: Setting[] = [];
    let loading = true;
    let saving: string | null = null;
    let editValues: Record<string, string> = {};
    let showSecrets: Record<string, boolean> = {};
    let successKey: string | null = null;

    // Group settings by category
    const categories = {
        telegram: {
            title: "Telegram Bot",
            icon: Bot,
            keys: ["TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_USERNAME"],
            color: "blue"
        },
        timeMachine: {
            title: "Машина Времени",
            icon: Clock,
            keys: ["TIME_MACHINE_PROVIDER", "TIME_MACHINE_MODE", "GEMINIGEN_API_KEY", "KIE_API_KEY"],
            color: "violet"
        },
        ai: {
            title: "AI / LLM",
            icon: Sparkles,
            keys: ["AI_API_KEY", "AI_API_BASE_URL", "AI_MODEL"],
            color: "emerald"
        }
    };

    const settingLabels: Record<string, { label: string; desc: string; type?: string; options?: {value: string, label: string}[] }> = {
        TELEGRAM_BOT_TOKEN: { label: "Bot Token", desc: "Токен Telegram бота от @BotFather" },
        TELEGRAM_BOT_USERNAME: { label: "Bot Username", desc: "Имя бота без @" },
        GEMINIGEN_API_KEY: { label: "GeminiGen API Key", desc: "Ключ API для GeminiGen.AI" },
        KIE_API_KEY: { label: "KIE API Key", desc: "Ключ API для KIE AI (nano-banana-pro)" },
        TIME_MACHINE_PROVIDER: { 
            label: "Провайдер", 
            desc: "Сервис для генерации изображений",
            type: "select",
            options: [
                { value: "geminigen", label: "GeminiGen.AI" },
                { value: "kie", label: "KIE AI (nano-banana-pro)" }
            ]
        },
        TIME_MACHINE_MODE: { 
            label: "Режим по умолчанию", 
            desc: "Режим трансформации по умолчанию",
            type: "select",
            options: [
                { value: "clothing_only", label: "Только одежда" },
                { value: "full", label: "Полная трансформация" },
                { value: "full_vintage", label: "Полная + винтаж" }
            ]
        },
        AI_API_KEY: { label: "AI API Key", desc: "Ключ API для LLM (OpenAI / совместимый)" },
        AI_API_BASE_URL: { label: "AI Base URL", desc: "URL API (оставить пустым для OpenAI)" },
        AI_MODEL: { label: "AI Model", desc: "Модель (gpt-4, gpt-3.5-turbo, и т.д.)" }
    };

    onMount(async () => {
        if (!isAuthenticated()) {
            push("/register");
            return;
        }

        // Check if superuser
        try {
            const res = await apiGet("/api/v1/users/me");
            if (res.ok) {
                const user = await res.json();
                if (!user.is_superuser) {
                    push("/dashboard");
                    return;
                }
            } else {
                push("/register");
                return;
            }
        } catch {
            push("/register");
            return;
        }

        await loadSettings();
    });

    async function loadSettings() {
        loading = true;
        try {
            const res = await apiGet("/api/v1/site-settings");
            if (res.ok) {
                settings = await res.json();
                // Initialize edit values
                for (const s of settings) {
                    editValues[s.key] = s.has_value ? "" : ""; // Don't pre-fill masked values
                }
            }
        } catch (e) {
            console.error("Failed to load settings", e);
        } finally {
            loading = false;
        }
    }

    async function saveSetting(key: string) {
        const value = editValues[key];
        if (!value && !settings.find(s => s.key === key)?.has_value) return;

        saving = key;
        try {
            const res = await apiPut("/api/v1/site-settings", { key, value });
            if (res.ok) {
                await loadSettings();
                editValues[key] = "";
                successKey = key;
                setTimeout(() => { if (successKey === key) successKey = null; }, 2000);
            }
        } catch (e) {
            console.error("Failed to save setting", e);
        } finally {
            saving = null;
        }
    }

    function isSecret(key: string): boolean {
        return key.includes("TOKEN") || key.includes("KEY");
    }

    function getSettingByKey(key: string): Setting | undefined {
        return settings.find(s => s.key === key);
    }

    function getCategoryColor(color: string): string {
        const colors: Record<string, string> = {
            blue: "from-blue-500/20 to-blue-600/10 border-blue-500/30",
            violet: "from-violet-500/20 to-violet-600/10 border-violet-500/30",
            emerald: "from-emerald-500/20 to-emerald-600/10 border-emerald-500/30"
        };
        return colors[color] || colors.blue;
    }

    function getIconColor(color: string): string {
        const colors: Record<string, string> = {
            blue: "text-blue-400",
            violet: "text-violet-400",
            emerald: "text-emerald-400"
        };
        return colors[color] || colors.blue;
    }
</script>

<div class="min-h-screen bg-neutral-900 text-white">
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-neutral-900/80 backdrop-blur-md border-b border-white/10">
        <div class="max-w-4xl mx-auto px-4 sm:px-6">
            <div class="flex justify-between items-center h-14">
                <div class="flex items-center gap-3">
                    <a href="#/admin" class="p-2 hover:bg-neutral-800 rounded-lg transition-colors">
                        <ArrowLeft size={20} />
                    </a>
                    <h1 class="text-xl font-bold text-amber-500 flex items-center gap-2">
                        <Settings size={22} />
                        Настройки
                    </h1>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-6">
        {#if loading}
            <div class="flex items-center justify-center py-20">
                <Loader2 size={32} class="animate-spin text-amber-500" />
            </div>
        {:else}
            {#each Object.entries(categories) as [catKey, cat]}
                {@const Icon = cat.icon}
                <div class="bg-gradient-to-br {getCategoryColor(cat.color)} rounded-xl border p-5 space-y-4">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-lg bg-black/20 flex items-center justify-center">
                            <Icon size={20} class={getIconColor(cat.color)} />
                        </div>
                        <h2 class="text-lg font-bold text-white">{cat.title}</h2>
                    </div>

                    <div class="space-y-4">
                        {#each cat.keys as key}
                            {@const setting = getSettingByKey(key)}
                            {@const meta = settingLabels[key] || { label: key, desc: "" }}
                            {@const secret = isSecret(key)}
                            
                            <div class="bg-neutral-900/50 rounded-lg p-4 space-y-2">
                                <div class="flex items-center justify-between">
                                    <div>
                                        <label class="text-sm font-medium text-white">{meta.label}</label>
                                        <p class="text-xs text-gray-500">{meta.desc}</p>
                                    </div>
                                    {#if setting?.has_value}
                                        <span class="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded-full flex items-center gap-1">
                                            <Check size={12} />
                                            Настроено
                                        </span>
                                    {/if}
                                </div>

                                <div class="flex gap-2">
                                    {#if meta.type === "select"}
                                        <select
                                            bind:value={editValues[key]}
                                            class="flex-1 bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-amber-500/50"
                                        >
                                            <option value="">— Выберите —</option>
                                            {#each meta.options || [] as opt}
                                                <option value={opt.value}>{opt.label}</option>
                                            {/each}
                                        </select>
                                    {:else}
                                        <div class="flex-1 relative">
                                            <input
                                                type={secret && !showSecrets[key] ? "password" : "text"}
                                                bind:value={editValues[key]}
                                                placeholder={setting?.has_value ? (secret ? "••••••••" : setting.value) : "Не задано"}
                                                class="w-full bg-neutral-800 border border-white/10 rounded-lg px-3 py-2 text-white text-sm placeholder:text-gray-600 focus:outline-none focus:border-amber-500/50 pr-10"
                                            />
                                            {#if secret}
                                                <button
                                                    on:click={() => showSecrets[key] = !showSecrets[key]}
                                                    class="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-white"
                                                >
                                                    {#if showSecrets[key]}
                                                        <EyeOff size={16} />
                                                    {:else}
                                                        <Eye size={16} />
                                                    {/if}
                                                </button>
                                            {/if}
                                        </div>
                                    {/if}
                                    
                                    <button
                                        on:click={() => saveSetting(key)}
                                        disabled={saving === key || !editValues[key]}
                                        class="px-4 py-2 bg-amber-500 hover:bg-amber-400 disabled:bg-neutral-700 disabled:cursor-not-allowed text-black disabled:text-gray-500 rounded-lg font-medium text-sm transition-colors flex items-center gap-2"
                                    >
                                        {#if saving === key}
                                            <Loader2 size={16} class="animate-spin" />
                                        {:else if successKey === key}
                                            <Check size={16} />
                                        {:else}
                                            <Save size={16} />
                                        {/if}
                                        Сохранить
                                    </button>
                                </div>

                                {#if setting?.has_value && !secret}
                                    <p class="text-xs text-gray-500">
                                        Текущее: <span class="text-gray-400">{setting.value}</span>
                                    </p>
                                {/if}
                            </div>
                        {/each}
                    </div>
                </div>
            {/each}

            <!-- Provider Info -->
            <div class="bg-neutral-800/50 rounded-xl border border-white/5 p-5 space-y-3">
                <h3 class="font-medium text-gray-300 flex items-center gap-2">
                    <Server size={18} />
                    О провайдерах Машины Времени
                </h3>
                <div class="grid sm:grid-cols-2 gap-4 text-sm">
                    <div class="bg-neutral-900/50 rounded-lg p-3">
                        <p class="font-medium text-white mb-1">GeminiGen.AI</p>
                        <p class="text-xs text-gray-500">
                            Оригинальный провайдер. Использует nano-banana-pro модель через прямое API.
                        </p>
                    </div>
                    <div class="bg-neutral-900/50 rounded-lg p-3">
                        <p class="font-medium text-white mb-1">KIE AI</p>
                        <p class="text-xs text-gray-500">
                            Альтернативный провайдер с nano-banana-pro. Требует загрузку файла через File Upload API.
                        </p>
                    </div>
                </div>
            </div>
        {/if}
    </div>
</div>
