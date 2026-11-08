import { page } from './app-state.svelte';

/** Keep filter navigation inside the isolated fixture, without contacting a server. */
export async function goto(url: string | URL) {
    page.url = new URL(url, page.url);
}
export async function invalidate() {}
export async function invalidateAll() {}
export function beforeNavigate() {}
export function afterNavigate() {}
export function disableScrollHandling() {}
export function pushState(url: string | URL) { page.url = new URL(url, page.url); }
export function replaceState(url: string | URL) { page.url = new URL(url, page.url); }
