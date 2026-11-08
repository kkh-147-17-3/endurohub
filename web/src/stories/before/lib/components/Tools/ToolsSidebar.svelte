<script lang="ts">
    let {
        current = '',
    }: {
        current?: string;
    } = $props();

    const tools = [
        { name: '페이스 계산기', href: '/tools/pace-calculator', key: 'pace-calculator' },
        { name: '훈련 플랜', href: '/tools/training-plan', key: 'training-plan' },
        { name: 'VO₂max 계산기', href: '/tools/vo2max', key: 'vo2max' },
        { name: '대회 기록 예측기', href: '/tools/race-predictor', key: 'race-predictor' },
        { name: '러닝 용어 사전', href: '/running-terms', key: 'glossary' },
    ];

    let otherTools = $derived(tools.filter((t) => t.key !== current));
</script>

<aside class="tools-aside">
    <div class="aside-head">
        <div class="arena-kicker">다른 도구 · {otherTools.length}</div>
    </div>
    <ul class="tool-list">
        {#each otherTools as tool, i (tool.key)}
            <li>
                <a class="tool-link" href={tool.href}>
                    <span class="tool-code">{String(i + 1).padStart(2, '0')}</span>
                    <span class="tool-name">{tool.name}</span>
                    <span class="tool-arrow">→</span>
                </a>
            </li>
        {/each}
    </ul>
</aside>

<style>
    .tools-aside {
        background: var(--arena-paper);
        border: 1px solid var(--arena-line);
    }
    .aside-head {
        padding: 14px 16px;
        border-bottom: 1px solid var(--arena-line);
        background: var(--arena-paper-alt);
    }
    .tool-list {
        margin: 0;
        padding: 0;
        list-style: none;
        display: flex;
        flex-direction: column;
    }
    .tool-link {
        display: grid;
        grid-template-columns: 56px 1fr 24px;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        text-decoration: none;
        color: var(--arena-ink);
        border-bottom: 1px solid var(--arena-line-soft);
        transition: background 0.1s, color 0.1s;
    }
    .tool-list li:last-child .tool-link {
        border-bottom: none;
    }
    .tool-link:hover {
        background: var(--arena-paper-alt);
    }
    .tool-link:hover .tool-arrow {
        color: var(--arena-accent-deep);
    }
    .tool-code {
        font-family: var(--arena-f-mono);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: var(--arena-ink-soft);
    }
    .tool-name {
        font-family: var(--arena-f-body);
        font-size: 14px;
        font-weight: 500;
        letter-spacing: -0.2px;
    }
    .tool-arrow {
        font-family: var(--arena-f-mono);
        font-size: 13px;
        color: var(--arena-ink-mute);
        text-align: right;
        transition: color 0.1s;
    }
</style>
