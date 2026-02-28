import type { Sport } from '$lib/types';

export const sportStyles: Record<Sport, {
    hoverBorder: string;
    badge: string;
    hoverText: string;
    btn: string;
    bg: string;
    bgLight: string;
    icon: string;
    text: string;
    border: string;
    gradient: string;
}> = {
    running: {
        hoverBorder: 'hover:border-primary',
        badge: 'badge-primary',
        hoverText: 'hover:text-primary',
        btn: 'btn-primary',
        bg: 'bg-primary',
        bgLight: 'bg-primary/10',
        icon: 'text-primary',
        text: 'text-primary',
        border: 'border-primary',
        gradient: 'from-violet-500/20 via-primary/30 to-blue-500/20',
    },
    swimming: {
        hoverBorder: 'hover:border-info',
        badge: 'badge-info',
        hoverText: 'hover:text-info',
        btn: 'btn-info',
        bg: 'bg-info',
        bgLight: 'bg-info/10',
        icon: 'text-info',
        text: 'text-info',
        border: 'border-info',
        gradient: 'from-cyan-500/20 via-info/30 to-blue-500/20',
    },
    cycling: {
        hoverBorder: 'hover:border-warning',
        badge: 'badge-warning',
        hoverText: 'hover:text-warning',
        btn: 'btn-warning',
        bg: 'bg-warning',
        bgLight: 'bg-warning/10',
        icon: 'text-warning',
        text: 'text-warning',
        border: 'border-warning',
        gradient: 'from-amber-500/20 via-warning/30 to-orange-500/20',
    },
    triathlon: {
        hoverBorder: 'hover:border-secondary',
        badge: 'badge-secondary',
        hoverText: 'hover:text-secondary',
        btn: 'btn-secondary',
        bg: 'bg-secondary',
        bgLight: 'bg-secondary/10',
        icon: 'text-secondary',
        text: 'text-secondary',
        border: 'border-secondary',
        gradient: 'from-pink-500/20 via-secondary/30 to-purple-500/20',
    },
    trail_running: {
        hoverBorder: 'hover:border-success',
        badge: 'badge-success',
        hoverText: 'hover:text-success',
        btn: 'btn-success',
        bg: 'bg-success',
        bgLight: 'bg-success/10',
        icon: 'text-success',
        text: 'text-success',
        border: 'border-success',
        gradient: 'from-emerald-500/20 via-success/30 to-teal-500/20',
    },
};

export const sportEmojis: Record<Sport, string> = {
    running: '🏃',
    swimming: '🏊',
    cycling: '🚴',
    triathlon: '🏅',
    trail_running: '⛰️',
};

export const sportLabels: Record<Sport, string> = {
    running: '마라톤',
    swimming: '수영',
    cycling: '자전거',
    triathlon: '철인3종',
    trail_running: '트레일러닝',
};
