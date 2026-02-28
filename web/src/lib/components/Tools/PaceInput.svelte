<script lang="ts">
    let {
        minutes = $bindable(5),
        seconds = $bindable(30),
        label = '페이스',
    }: {
        minutes: number;
        seconds: number;
        label?: string;
    } = $props();

    function clamp(value: number, min: number, max: number): number {
        return Math.max(min, Math.min(max, value));
    }

    function handleMinutes(e: Event) {
        minutes = clamp(Number((e.target as HTMLInputElement).value) || 0, 0, 15);
    }
    function handleSeconds(e: Event) {
        seconds = clamp(Number((e.target as HTMLInputElement).value) || 0, 0, 59);
    }
</script>

<div class="form-control">
    <div class="label">
        <span class="label-text font-medium">{label}</span>
    </div>
    <div class="flex items-center gap-2">
        <div class="flex items-center gap-1">
            <input
                type="number"
                value={minutes}
                oninput={handleMinutes}
                min="0"
                max="15"
                class="input input-bordered input-sm w-16 text-center tabular-nums"
                aria-label="분"
            />
            <span class="text-sm text-base-content/60">분</span>
        </div>
        <div class="flex items-center gap-1">
            <input
                type="number"
                value={seconds}
                oninput={handleSeconds}
                min="0"
                max="59"
                class="input input-bordered input-sm w-16 text-center tabular-nums"
                aria-label="초"
            />
            <span class="text-sm text-base-content/60">초</span>
        </div>
        <span class="text-sm text-base-content/60">/km</span>
    </div>
</div>
