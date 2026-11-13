const allowedStates = new Set([
    'idle', 'greeting', 'thinking', 'success', 'warning', 'sleeping', 'curious', 'happy',
]);

export class SumiStateMachine {
    constructor(onChange = () => {}) {
        this.state = 'idle';
        this.onChange = onChange;
    }

    set(nextState) {
        if (!allowedStates.has(nextState)) {
            throw new Error(`Estado SUMI no válido: ${nextState}`);
        }
        if (this.state === nextState) return;
        const previous = this.state;
        this.state = nextState;
        this.onChange({ previous, current: nextState });
    }

    get() {
        return this.state;
    }
}
