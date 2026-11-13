import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export class SumiLoader {
    constructor() {
        this.loader = new GLTFLoader();
    }

    load(url) {
        return new Promise((resolve, reject) => {
            this.loader.load(url, (gltf) => resolve(gltf), undefined, reject);
        });
    }
}
