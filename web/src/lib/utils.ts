/**
 * Detect if content contains HTML tags.
 */
function isHtml(content: string): boolean {
	return /<[a-z][\s\S]*>/i.test(content);
}

/**
 * Escape HTML special characters for safe rendering.
 */
export function escapeHtml(text: string): string {
	return text
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#039;');
}

/**
 * Strip all HTML tags from a string.
 */
export function stripHtml(html: string): string {
	return html.replace(/<[^>]*>/g, '');
}

/**
 * Format post content for rendering.
 * - HTML content: render as-is (already sanitized server-side)
 * - Plain text (legacy): escape HTML entities and convert newlines to <br>
 */
export function formatPostContent(content: string): string {
	if (!content) return '';
	if (isHtml(content)) {
		return content;
	}
	return escapeHtml(content).replace(/\n/g, '<br>');
}
