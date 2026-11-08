/** Same clock for both versions; multi-argument Date constructors still work. */
const fixedTime = Date.parse('2026-11-07T03:00:00Z');
const NativeDate = Date;
globalThis.Date = new Proxy(NativeDate, {
    construct(target, argumentsList) {
        return Reflect.construct(target, argumentsList.length ? argumentsList : [fixedTime]);
    },
    apply() { return new NativeDate(fixedTime).toString(); },
    get(target, property, receiver) {
        return property === 'now' ? () => fixedTime : Reflect.get(target, property, receiver);
    },
});
