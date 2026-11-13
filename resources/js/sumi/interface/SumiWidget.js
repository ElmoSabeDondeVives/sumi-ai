import { SumiEngine } from '../core/SumiEngine.js';
import { SumiStateMachine } from '../animation/SumiStateMachine.js';

export class SumiWidget {
    constructor({ container, status = () => {} }) {
        this.engine = new SumiEngine({
            container,
            onStatus: status,
        });
        this.states = new SumiStateMachine(({ current }) => {
            this.engine.playAnimation(current);
        });
    }

    async mount() {
        await this.engine.load();
        return this;
    }

    setState(state) {
        this.states.set(state);
    }

    destroy() {
        this.engine.destroy();
    }
}
