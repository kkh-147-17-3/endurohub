/** Component previews never emit analytics or call the production API. */
export function track(_event: string, _properties: Record<string, unknown> = {}) {}
