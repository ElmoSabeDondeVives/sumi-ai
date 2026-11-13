export const sumiConfig = {
    modelUrl: '/models/sumi/base/sumi.glb',
    background: 'transparent',
    pixelRatioLimit: 2,
    camera: { fov: 35, position: [0, 1.15, 4.2] },
    lighting: { ambient: 1.8, key: 2.4 },
    states: ['idle', 'greeting', 'thinking', 'success', 'warning', 'sleeping', 'curious', 'happy'],
    expressions: ['neutral', 'happy', 'curious', 'concerned', 'sleepy'],
};
