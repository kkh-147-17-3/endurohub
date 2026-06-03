// Runtime helpers for the calendar map view.
//
// The province polygons in ./korea-provinces.ts were projected at build time
// with d3.geoMercator(). These functions reproduce that projection in
// closed form (no d3 at runtime) so race latitude/longitude can be placed
// onto the same 800x780 SVG viewBox, and let the map zoom to a province's
// real bounding box.

import { KOREA_PROJECTION, KOREA_VIEWBOX } from './korea-provinces';

const DEG = Math.PI / 180;

/**
 * Project geographic [lng, lat] into the SVG viewBox space the province
 * paths live in. Closed-form equivalent of d3.geoMercator() with the
 * build-time scale/translate.
 *
 * Self-check: 서울시청 [126.9784, 37.5667] must land on the coordinate
 * recorded in the header comment of ./korea-provinces.ts (within <0.5px).
 */
export function projectLngLat(lng: number, lat: number): [number, number] {
	const { scale, translate } = KOREA_PROJECTION;
	// d3 geoMercator raw projection (input in radians):
	//   x = λ ;  y = ln(tan(π/4 + φ/2))
	const x = lng * DEG;
	const y = Math.log(Math.tan(Math.PI / 4 + (lat * DEG) / 2));
	// d3 scales the raw projection and adds translate; the Y axis is flipped.
	return [translate[0] + scale * x, translate[1] - scale * y];
}

export interface BboxFit {
	/** Uniform zoom factor applied to the map group. */
	scale: number;
	/** Horizontal translate applied before scaling, in viewBox units. */
	tx: number;
	/** Vertical translate applied before scaling, in viewBox units. */
	ty: number;
	/** CSS transform string for the zooming SVG group. */
	transform: string;
}

/**
 * Fits `bbox` (in viewBox space) into the viewBox with a uniform scale so
 * the selected province fills the frame, leaving only `margin` as padding.
 * The returned `scale` lets callers counter-scale overlaid labels and pins
 * so they keep a constant on-screen size at any zoom level.
 */
export function fitBbox(
	bbox: [[number, number], [number, number]],
	margin = 0.05,
): BboxFit {
	const [[x0, y0], [x1, y1]] = bbox;
	const bw = Math.max(1, x1 - x0);
	const bh = Math.max(1, y1 - y0);
	const fit = Math.min(
		(KOREA_VIEWBOX.w * (1 - margin)) / bw,
		(KOREA_VIEWBOX.h * (1 - margin)) / bh,
	);
	const scale = Math.max(1, fit);
	const cx = (x0 + x1) / 2;
	const cy = (y0 + y1) / 2;
	const tx = KOREA_VIEWBOX.w / 2 - cx * scale;
	const ty = KOREA_VIEWBOX.h / 2 - cy * scale;
	return { scale, tx, ty, transform: `translate(${tx}px, ${ty}px) scale(${scale})` };
}

/** Identity fit — the overview (no province selected). */
export const IDENTITY_FIT: BboxFit = {
	scale: 1,
	tx: 0,
	ty: 0,
	transform: 'translate(0px, 0px) scale(1)',
};
