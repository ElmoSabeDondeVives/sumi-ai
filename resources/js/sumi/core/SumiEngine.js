import * as THREE from 'three';
import { SumiLoader } from './SumiLoader.js';
import { SumiCharacter } from './SumiCharacter.js';
import { sumiConfig } from '../config/sumi.config.js';

export class SumiEngine {
    constructor({ container, model = sumiConfig.modelUrl, onStatus = () => {} }) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        if (!this.container) throw new Error('No se encontró el contenedor de SUMI.');

        this.modelUrl = model;
        this.onStatus = onStatus;
        this.clock = new THREE.Clock();
        this.loader = new SumiLoader();
        this.renderer = null;
        this.scene = null;
        this.camera = null;
        this.character = null;
        this.frameId = null;
        this.resizeObserver = null;
        this.running = false;
    }

    async load() {
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(
            sumiConfig.camera.fov, 1, 0.1, 100
        );
        this.camera.position.set(...sumiConfig.camera.position);

        this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, sumiConfig.pixelRatioLimit));
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.container.appendChild(this.renderer.domElement);

        this.scene.add(new THREE.HemisphereLight(0xffffff, 0x777788, sumiConfig.lighting.ambient));
        const key = new THREE.DirectionalLight(0xffffff, sumiConfig.lighting.key);
        key.position.set(3, 5, 4);
        this.scene.add(key);

        this.character = new SumiCharacter(this.scene);
        this.resizeObserver = new ResizeObserver(() => this.resize());
        this.resizeObserver.observe(this.container);
        this.resize();

        try {
            const gltf = await this.loader.load(this.modelUrl);
            this.character.setModel(gltf);
            this.onStatus({ type: 'model-loaded', placeholder: false });
        } catch (error) {
            this.createPlaceholder();
            this.onStatus({ type: 'placeholder', message: 'Modelo GLB pendiente', error });
        }

        this.start();
        return this;
    }

    createPlaceholder() {
        const group = new THREE.Group();
        const cream = new THREE.MeshStandardMaterial({ color: 0xf2e9df, roughness: 0.72 });
        const violet = new THREE.MeshStandardMaterial({ color: 0x7665e8, emissive: 0x24145c });
        const body = new THREE.Mesh(new THREE.SphereGeometry(0.62, 32, 24), cream);
        body.position.y = 0.65;
        body.scale.set(0.82, 1, 0.72);
        group.add(body);

        const head = new THREE.Mesh(new THREE.SphereGeometry(0.48, 32, 24), cream);
        head.position.y = 1.42;
        group.add(head);

        for (const x of [-0.29, 0.29]) {
            const ear = new THREE.Mesh(new THREE.ConeGeometry(0.16, 0.48, 24), cream);
            ear.position.set(x, 1.91, 0);
            ear.rotation.z = x < 0 ? 0.16 : -0.16;
            group.add(ear);
            const eye = new THREE.Mesh(new THREE.SphereGeometry(0.055, 16, 12), violet);
            eye.position.set(x * 0.72, 1.48, 0.43);
            group.add(eye);
        }

        const gem = new THREE.Mesh(new THREE.OctahedronGeometry(0.09), violet);
        gem.position.set(0, 1.76, 0.43);
        group.add(gem);
        this.character.root.add(group);
    }

    start() {
        if (this.running) return;
        this.running = true;
        const render = () => {
            if (!this.running) return;
            const delta = Math.min(this.clock.getDelta(), 0.05);
            this.character?.update(delta);
            this.renderer.render(this.scene, this.camera);
            this.frameId = requestAnimationFrame(render);
        };
        render();
    }

    stop() {
        this.running = false;
        if (this.frameId) cancelAnimationFrame(this.frameId);
        this.frameId = null;
    }

    resize() {
        if (!this.renderer || !this.camera) return;
        const width = Math.max(this.container.clientWidth, 1);
        const height = Math.max(this.container.clientHeight, 1);
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height, false);
    }

    playAnimation(name, options) {
        return this.character?.playAnimation(name, options) ?? false;
    }

    destroy() {
        this.stop();
        this.resizeObserver?.disconnect();
        this.character?.dispose();
        this.renderer?.dispose();
        this.renderer?.domElement.remove();
    }
}
