<script lang="ts">
    interface Props {
        rating: number;
        readonly?: boolean;
        size?: 'sm' | 'md' | 'lg';
        onchange?: (rating: number) => void;
    }

    let { rating = $bindable(0), readonly = false, size = 'md', onchange }: Props = $props();

    const sizeClasses = {
        sm: 'w-4 h-4',
        md: 'w-5 h-5',
        lg: 'w-6 h-6',
    };

    function handleClick(value: number) {
        if (!readonly) {
            rating = value;
            onchange?.(value);
        }
    }

    function handleKeydown(event: KeyboardEvent, value: number) {
        if (!readonly && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            rating = value;
            onchange?.(value);
        }
    }
</script>

<div class="flex gap-0.5" role="group" aria-label="별점">
    {#each [1, 2, 3, 4, 5] as star}
        {#if readonly}
            <svg
                xmlns="http://www.w3.org/2000/svg"
                class="{sizeClasses[size]} {star <= rating ? 'text-warning fill-warning' : 'text-base-300 fill-base-300'}"
                viewBox="0 0 24 24"
            >
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
        {:else}
            <button
                type="button"
                onclick={() => handleClick(star)}
                onkeydown={(e) => handleKeydown(e, star)}
                class="cursor-pointer transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1 rounded"
                aria-label="{star}점"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="{sizeClasses[size]} {star <= rating ? 'text-warning fill-warning' : 'text-base-300 fill-base-300'}"
                    viewBox="0 0 24 24"
                >
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                </svg>
            </button>
        {/if}
    {/each}
</div>
