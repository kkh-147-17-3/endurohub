const STORAGE_KEY = 'theme';

export type Theme = 'light' | 'dark';

export function getTheme(): Theme {
	if (typeof window === 'undefined') return 'light';
	const stored = localStorage.getItem(STORAGE_KEY);
	if (stored === 'light' || stored === 'dark') return stored;
	return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function setTheme(theme: Theme) {
	if (typeof document === 'undefined') return;
	document.documentElement.setAttribute('data-theme', theme);
	localStorage.setItem(STORAGE_KEY, theme);
}

export function toggleTheme(): Theme {
	const current = document.documentElement.getAttribute('data-theme') as Theme;
	const next: Theme = current === 'dark' ? 'light' : 'dark';

	document.documentElement.classList.add('theme-transition');
	setTheme(next);

	// Remove class after transition ends to avoid interfering with other animations
	setTimeout(() => {
		document.documentElement.classList.remove('theme-transition');
	}, 300);

	return next;
}
