<script lang="ts">
    type Variant =
        | 'clear'
        | 'mostly-clear'
        | 'partly-cloudy'
        | 'cloudy'
        | 'fog'
        | 'drizzle'
        | 'rain'
        | 'snow'
        | 'heavy-snow'
        | 'thunder'
        | 'unknown';

    interface Props {
        weatherCode?: number | null;
        size?: number;
        label?: string | null;
        title?: string | null;
    }

    let { weatherCode = null, size = 18, label = null, title = null }: Props = $props();

    // WMO weather code → visual variant. Mirrors api/races/management/commands/fetch_weather.py.
    function codeToVariant(code: number | null | undefined): Variant {
        if (code == null) return 'unknown';
        if (code === 0) return 'clear';
        if (code === 1) return 'mostly-clear';
        if (code === 2) return 'partly-cloudy';
        if (code === 3) return 'cloudy';
        if (code === 45 || code === 48) return 'fog';
        if (code === 51 || code === 53 || code === 55) return 'drizzle';
        if (code === 56 || code === 57) return 'drizzle';
        if (code === 61 || code === 63 || code === 65) return 'rain';
        if (code === 66 || code === 67) return 'rain';
        if (code === 71 || code === 73 || code === 77) return 'snow';
        if (code === 75) return 'heavy-snow';
        if (code === 80 || code === 81) return 'drizzle';
        if (code === 82) return 'rain';
        if (code === 85 || code === 86) return 'snow';
        if (code === 95 || code === 96 || code === 99) return 'thunder';
        return 'unknown';
    }

    const variant = $derived(codeToVariant(weatherCode));
    const aria = $derived(title ?? label ?? '날씨 아이콘');
</script>

<svg
    class="wx"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    role="img"
    aria-label={aria}
>
    <title>{aria}</title>
    {#if variant === 'clear'}
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2" />
        <path d="M12 20v2" />
        <path d="m4.93 4.93 1.41 1.41" />
        <path d="m17.66 17.66 1.41 1.41" />
        <path d="M2 12h2" />
        <path d="M20 12h2" />
        <path d="m4.93 19.07 1.41-1.41" />
        <path d="m17.66 6.34 1.41-1.41" />
    {:else if variant === 'mostly-clear'}
        <circle cx="9" cy="9" r="3" />
        <path d="M9 2v1.5" />
        <path d="M2 9h1.5" />
        <path d="m4.05 4.05 1.06 1.06" />
        <path d="m13.95 4.05-1.06 1.06" />
        <path d="M21 16.5a3 3 0 0 1-3 3h-6a3 3 0 0 1-.45-5.97A4 4 0 0 1 19 15a3 3 0 0 1 2 1.5z" />
    {:else if variant === 'partly-cloudy'}
        <circle cx="8" cy="8" r="2.5" />
        <path d="M8 2.2v1" />
        <path d="M2.2 8h1" />
        <path d="m3.8 3.8.7.7" />
        <path d="m12.2 3.8-.7.7" />
        <path d="M21 17a3.5 3.5 0 0 1-3.5 3.5h-7A3.5 3.5 0 0 1 10 13.5a4.5 4.5 0 0 1 8.62 1A3.5 3.5 0 0 1 21 17z" />
    {:else if variant === 'cloudy'}
        <path d="M17.5 19a4.5 4.5 0 0 0-1.41-8.78 6 6 0 0 0-11.84 1.78A4 4 0 0 0 5 19h12.5z" />
    {:else if variant === 'fog'}
        <path d="M17.5 16a4.5 4.5 0 0 0-1.41-8.78 6 6 0 0 0-11.84 1.78A4 4 0 0 0 5 16h12.5z" />
        <path d="M3 19h12" />
        <path d="M7 22h10" />
    {:else if variant === 'drizzle'}
        <path d="M17.5 14a4.5 4.5 0 0 0-1.41-8.78 6 6 0 0 0-11.84 1.78A4 4 0 0 0 5 14h12.5z" />
        <path d="m8 17-1 2" />
        <path d="m12 17-1 2" />
        <path d="m16 17-1 2" />
    {:else if variant === 'rain'}
        <path d="M17.5 14a4.5 4.5 0 0 0-1.41-8.78 6 6 0 0 0-11.84 1.78A4 4 0 0 0 5 14h12.5z" />
        <path d="M8 17v3" />
        <path d="M12 17v3" />
        <path d="M16 17v3" />
    {:else if variant === 'snow'}
        <path d="M17.5 14a4.5 4.5 0 0 0-1.41-8.78 6 6 0 0 0-11.84 1.78A4 4 0 0 0 5 14h12.5z" />
        <path d="M8 18.5h.01" />
        <path d="M8 21.5h.01" />
        <path d="M12 19h.01" />
        <path d="M12 22h.01" />
        <path d="M16 18.5h.01" />
        <path d="M16 21.5h.01" />
    {:else if variant === 'heavy-snow'}
        <path d="M17.5 14a4.5 4.5 0 0 0-1.41-8.78 6 6 0 0 0-11.84 1.78A4 4 0 0 0 5 14h12.5z" />
        <path d="M9 18l1 1.5L9 21" />
        <path d="M8.5 19.5h2" />
        <path d="M13 18l1 1.5L13 21" />
        <path d="M12.5 19.5h2" />
    {:else if variant === 'thunder'}
        <path d="M17.5 13a4.5 4.5 0 0 0-1.41-8.78 6 6 0 0 0-11.84 1.78A4 4 0 0 0 5 13h12.5z" />
        <path d="m12 14-3 5h3l-1 4 4-6h-3l1-3z" />
    {:else}
        <circle cx="12" cy="12" r="9" />
        <path d="M9.5 9.5a3 3 0 1 1 4 2.5c-1 .5-1.5 1.2-1.5 2" />
        <path d="M12 17h.01" />
    {/if}
</svg>

<style>
    .wx {
        display: inline-block;
        vertical-align: -3px;
        flex-shrink: 0;
    }
</style>
