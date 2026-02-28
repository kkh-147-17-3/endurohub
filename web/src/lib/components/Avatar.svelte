<script lang="ts">
    interface Props {
        nickname: string;
        size?: 'xs' | 'sm' | 'md';
    }

    let { nickname, size = 'sm' }: Props = $props();

    const COLORS = [
        'bg-primary text-primary-content',
        'bg-secondary text-secondary-content',
        'bg-accent text-accent-content',
        'bg-info text-info-content',
        'bg-success text-success-content',
        'bg-warning text-warning-content',
        'bg-error text-error-content',
    ];

    function hashCode(str: string): number {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash |= 0;
        }
        return Math.abs(hash);
    }

    const initial = $derived(nickname ? nickname.charAt(0).toUpperCase() : '?');
    const colorClass = $derived(COLORS[hashCode(nickname || '') % COLORS.length]);

    const sizeClasses: Record<string, string> = {
        xs: 'w-5 h-5 text-[10px]',
        sm: 'w-6 h-6 text-xs',
        md: 'w-8 h-8 text-sm',
    };

    const sizeClass = $derived(sizeClasses[size] || sizeClasses.sm);
</script>

<span class="inline-flex items-center justify-center rounded-full font-semibold shrink-0 {colorClass} {sizeClass}" title={nickname}>
    {initial}
</span>
