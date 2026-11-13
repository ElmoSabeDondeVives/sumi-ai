# Producción del avatar 3D SUMI — Dirección de arte y especificación técnica

Documento de producción del avatar interactivo en tiempo real. Cubre las seis etapas del pipeline: concepto, modelado, texturizado PBR, rigging/blendshapes, animación y exportación. **Alcance actual: solo diseño visual**, sin lógica de IA conectada.

---

## 1. Diseño conceptual y estilo

- **Estética:** estilizado 3D tipo Pixar, proporciones chibi (cabeza grande, cuerpo pequeño), acabado premium y amable. Coherente con la identidad oficial ([identity.md](./identity.md)).
- **Paleta de marca:**

| Uso | Color | Hex |
|---|---|---|
| Pelaje base | Blanco crema | `#F2E9DF` |
| Interior de orejas / nariz | Rosa suave | `#E8B4B8` |
| Acento mágico (gema, ojos, cola) | Violeta | `#7665E8` |
| Violeta profundo (emisivo) | Índigo | `#24145C` |
| Fondo de escena | Azul noche | `#11101B` |

- **Vistas ortográficas de referencia:** [concept/sumi-model-sheet.png](./concept/sumi-model-sheet.png) — frontal, perfil y 3/4, expresión neutra, A-pose relajada.
- **Rasgos no negociables:** gema octaédrica violeta en la frente, ojos grandes luminosos violeta/azul, orejas de zorro expresivas con interior rosa, cola esponjosa con punta violeta.

## 2. Modelado 3D y topología

- **Malla limpia** con flujo de polígonos (edge loops) concéntrico alrededor de ojos y boca, y loops de soporte en cuello, hombros y base de orejas/cola para deformación correcta.
- **Presupuesto de polígonos:** 15 000 – 35 000 triángulos totales (low/mid-poly tiempo real).

| Parte | Presupuesto aprox. (tris) |
|---|---|
| Cabeza + cara | 8 000 – 12 000 |
| Cuerpo + extremidades | 5 000 – 10 000 |
| Orejas | 1 500 – 3 000 |
| Cola | 2 000 – 4 000 |
| Ojos + gema | 1 000 – 2 000 |

- Normales suavizadas (shade smooth); sin n-gons en zonas deformables; simetría X durante el modelado.

## 3. Texturizado y materiales (PBR)

- **UV:** mapeo limpio sin solapamientos (islas separadas para cabeza, cuerpo, orejas, cola); margen de 8–16 px entre islas.
- **Mapas PBR (metallic/roughness, glTF 2.0):** Albedo/BaseColor, Roughness y Normal Map, a **1K (1024²)** por defecto y 2K máximo para la cabeza si hiciera falta detalle.
- **Materiales:**

| Material | BaseColor | Roughness | Emisión |
|---|---|---|---|
| Pelaje | `#F2E9DF` | 0.70 – 0.80 | — |
| Interior orejas | `#E8B4B8` | 0.65 | — |
| Ojos | `#7665E8` | 0.15 (brillo húmedo) | leve `#24145C` |
| Gema | `#7665E8` | 0.10 | `#7665E8` intensidad media |
| Nariz / almohadillas | `#D9A0A8` | 0.40 | — |

- **Iluminación de referencia:** setup de estudio suave de 3 puntos — key direccional cálida, fill hemisférico y rim sutil violeta — que resalte rasgos faciales y lectura de materiales (ya reflejado en `sumi.config.js`).

## 4. Rigging y expresiones faciales (blendshapes)

### Esqueleto básico funcional

```
root
└── spine
    └── chest
        ├── shoulder.L → arm.L → hand.L
        ├── shoulder.R → arm.R → hand.R
        └── neck
            └── head
                ├── ear.L
                └── ear.R
└── tail.01 → tail.02 → tail.03
```

- Skinning por pesos automáticos + limpieza manual en cuello y hombros. Máximo 4 influencias por vértice (límite glTF).

### Shape keys / blendshapes

**Parpadeo y cejas:**
`blink_L`, `blink_R`, `browUp` (atención), `browDown` (duda), `browHappy` (alegría).

**Visemas estándar (Oculus Lipsync, 15):**
`viseme_sil`, `viseme_PP`, `viseme_FF`, `viseme_TH`, `viseme_DD`, `viseme_kk`, `viseme_CH`, `viseme_SS`, `viseme_nn`, `viseme_RR`, `viseme_aa`, `viseme_E`, `viseme_ih`, `viseme_oh`, `viseme_ou`.

Los nombres son **estables** y en ese formato exacto para futura sincronización labial (ARKit/Oculus compatible).

## 5. Animación y estados base

Clips en bucle, suaves, nombrados igual que los estados del motor ([states.md](../animation/states.md)) para que `SumiStateMachine` los dispare sin mapeos:

| Clip | Estado del brief | Contenido |
|---|---|---|
| `idle` | Reposo/respiración | Respiración sutil (escala/posición de pecho), balanceo leve de cola y orejas |
| `curious` | Escucha activa | Asentir con la cabeza, orejas hacia adelante |
| `thinking` | Procesamiento | Cabeza ladeada, mirada arriba, cola lenta |

- 24–30 fps, duración 2–4 s por ciclo, primer y último frame idénticos (loop perfecto).
- Los demás estados (`greeting`, `success`, `warning`, `sleeping`, `happy`) se producirán en una fase posterior.

## 6. Exportación y optimización

- **Formato:** `.GLB` (glTF 2.0 binario) con materiales, texturas y animaciones embebidas.
- **Destino:** `public/models/sumi/base/sumi.glb` (ruta que ya consume `sumi.config.js`).
- +Y arriba, escala en metros (~1.2 m de alto), transformaciones aplicadas.
- Verificación de carga en la preview (`index.html`): debe emitir `{ type: 'model-loaded', placeholder: false }`.

## Pipeline reproducible

La construcción del avatar está automatizada con Blender headless:

```bash
blender -b -P tools/blender/build_sumi.py
```

El script genera malla, materiales, UVs, rig, shape keys y clips, exporta el GLB al destino final y guarda `tools/blender/sumi_base.blend` como **archivo fuente editable** para refinar a mano en Blender GUI. Al editar manualmente: conservar los nombres de clips y shape keys, y re-exportar a `public/models/sumi/base/sumi.glb` (glTF 2.0 binario, animaciones en pistas NLA).
