<script lang="ts">
    import { API_BASE } from "../lib/config";
    import { onMount } from "svelte";
    import { ArrowLeft, MapPin, BookOpen } from "lucide-svelte";

    export let params: { id: string } = { id: '' };

    let article: any = null;
    let loading = true;
    let error = '';

    onMount(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/v1/pois/${params.id}/article`);
            if (!res.ok) throw new Error('Not found');
            article = await res.json();
        } catch (e) {
            error = 'Статья не найдена';
        } finally {
            loading = false;
        }
    });

    // Simple Markdown-to-HTML (headings, bold, italic, paragraphs, links, lists)
    function renderMarkdown(md: string): string {
        if (!md) return '<p class="text-gray-500">Статья ещё не написана.</p>';
        let html = md
            // Escape HTML
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            // Headers
            .replace(/^### (.+)$/gm, '<h3 class="text-lg font-bold text-white mt-6 mb-2">$1</h3>')
            .replace(/^## (.+)$/gm, '<h2 class="text-xl font-bold text-white mt-8 mb-3">$1</h2>')
            .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold text-amber-500 mt-6 mb-4">$1</h1>')
            // Bold & italic
            .replace(/\*\*(.+?)\*\*/g, '<strong class="text-white">$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            // Links
            .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" class="text-amber-400 underline hover:text-amber-300" target="_blank">$1</a>')
            // Unordered lists
            .replace(/^[\-\*] (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
            // Paragraphs (double newline)
            .replace(/\n\n/g, '</p><p class="text-gray-300 leading-relaxed mb-4">')
            // Single newline -> <br>
            .replace(/\n/g, '<br>');
        // Wrap lists
        html = html.replace(/(<li[^>]*>.*?<\/li>(?:<br>)?)+/g, (m) => '<ul class="mb-4 space-y-1">' + m.replace(/<br>/g,'') + '</ul>');
        return '<p class="text-gray-300 leading-relaxed mb-4">' + html + '</p>';
    }
</script>

<div class="min-h-screen bg-neutral-900 text-white">
    <header class="sticky top-0 z-50 bg-neutral-900/80 backdrop-blur-md border-b border-white/10">
        <div class="max-w-3xl mx-auto px-4 sm:px-6">
            <div class="flex items-center h-14 gap-3">
                <a href="#/dashboard" class="p-2 hover:bg-neutral-800 rounded-lg transition-colors">
                    <ArrowLeft size={20} />
                </a>
                <div class="flex items-center gap-2">
                    <BookOpen size={18} class="text-amber-500" />
                    <h1 class="text-lg font-bold">Статья</h1>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-3xl mx-auto px-4 sm:px-6 py-6">
        {#if loading}
            <div class="flex items-center justify-center py-20">
                <div class="animate-spin w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full"></div>
            </div>
        {:else if error}
            <div class="text-center py-20">
                <p class="text-gray-400 text-lg">{error}</p>
                <a href="#/dashboard" class="text-amber-500 mt-4 inline-block">← Назад</a>
            </div>
        {:else if article}
            <div class="bg-neutral-800 rounded-xl border border-white/10 overflow-hidden">
                <!-- Header -->
                <div class="p-6 border-b border-white/10">
                    <h1 class="text-2xl sm:text-3xl font-bold text-white mb-2">{article.title}</h1>
                    {#if article.address}
                        <div class="flex items-center gap-2 text-gray-400">
                            <MapPin size={14} class="text-amber-500/60" />
                            <span class="text-sm">{article.address}</span>
                        </div>
                    {/if}
                    {#if article.description}
                        <p class="mt-3 text-gray-400 italic text-sm border-l-2 border-amber-500/30 pl-3">{article.description}</p>
                    {/if}
                </div>

                <!-- Article body -->
                <div class="p-6 prose-custom">
                    {#if article.full_article}
                        {@html renderMarkdown(article.full_article)}
                    {:else}
                        <div class="text-center py-12">
                            <BookOpen size={48} class="text-gray-700 mx-auto mb-4" />
                            <p class="text-gray-500">Полная статья ещё не написана.</p>
                        </div>
                    {/if}
                </div>
            </div>
        {/if}
    </div>
</div>
