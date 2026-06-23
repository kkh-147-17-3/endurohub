// OpenTelemetry 부트스트랩 — SvelteKit SSR(Node) 서버사이드 계측.
// `node --import ./otel.mjs build` 로 앱보다 먼저 로드되어야 monkey-patching이 동작한다.
//
// 계측 대상(자동):
//   - incoming HTTP 요청 (http instrumentation) — Nginx → SSR 진입 span
//   - outgoing fetch (undici instrumentation) — SSR → Django API 호출 span + traceparent 전파
//   - Node 런타임 메트릭 (event loop lag, heap, GC 등)
//
// OTEL_EXPORTER_OTLP_ENDPOINT 가 없으면 아무것도 하지 않는다(로컬/CI에서 무해).
// service.name 등 리소스 속성은 OTEL_SERVICE_NAME / OTEL_RESOURCE_ATTRIBUTES 환경변수로 주입.

if (process.env.OTEL_EXPORTER_OTLP_ENDPOINT) {
	const { NodeSDK } = await import('@opentelemetry/sdk-node');
	const { getNodeAutoInstrumentations } = await import(
		'@opentelemetry/auto-instrumentations-node'
	);
	const { OTLPTraceExporter } = await import('@opentelemetry/exporter-trace-otlp-http');
	const { OTLPMetricExporter } = await import('@opentelemetry/exporter-metrics-otlp-http');
	const { PeriodicExportingMetricReader } = await import('@opentelemetry/sdk-metrics');

	const sdk = new NodeSDK({
		traceExporter: new OTLPTraceExporter(),
		metricReader: new PeriodicExportingMetricReader({
			exporter: new OTLPMetricExporter()
		}),
		instrumentations: [
			getNodeAutoInstrumentations({
				// 파일시스템 계측은 노이즈가 심해 비활성화(span 폭증 방지).
				'@opentelemetry/instrumentation-fs': { enabled: false }
			})
		]
	});

	sdk.start();

	process.on('SIGTERM', () => {
		sdk.shutdown().finally(() => process.exit(0));
	});
}
