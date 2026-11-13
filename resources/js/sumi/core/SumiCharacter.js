import * as THREE from 'three';

export class SumiCharacter {
    constructor(scene) {
        this.scene = scene;
        this.root = new THREE.Group();
        this.mixer = null;
        this.actions = new Map();
        this.currentAction = null;
        this.scene.add(this.root);
    }

    setModel(gltf) {
        this.root.clear();
        this.root.add(gltf.scene);
        this.mixer = new THREE.AnimationMixer(gltf.scene);
        this.actions.clear();

        for (const clip of gltf.animations ?? []) {
            this.actions.set(clip.name.toLowerCase(), this.mixer.clipAction(clip));
        }
    }

    playAnimation(name, { fade = 0.25, loop = true } = {}) {
        const action = this.actions.get(name.toLowerCase());
        if (!action) return false;

        action.reset();
        action.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce);
        action.clampWhenFinished = !loop;
        if (this.currentAction && this.currentAction !== action) {
            this.currentAction.fadeOut(fade);
        }
        action.fadeIn(fade).play();
        this.currentAction = action;
        return true;
    }

    update(delta) {
        this.mixer?.update(delta);
    }

    dispose() {
        this.scene.remove(this.root);
        this.root.traverse((object) => {
            object.geometry?.dispose?.();
            for (const material of (Array.isArray(object.material) ? object.material : [object.material])) {
                material?.dispose?.();
            }
        });
    }
}
