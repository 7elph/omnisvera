import { useEffect, useRef } from "react";
import type { BufferGeometry, Material, Mesh, Object3D, Texture, Vector3 } from "three";
import type { Body, Quaternion as CannonQuaternion, Shape } from "cannon-es";
import type { DiceRollEvent } from "../api";
import { diceElapsedSeconds, DICE_SETTLE_START, DICE_SETTLE_DURATION } from "./diceTiming";

export type DiceVisualRoll = Pick<DiceRollEvent, "id" | "label" | "formula" | "dice" | "individual_results" | "total"> &
  Partial<Pick<DiceRollEvent, "character_id" | "roll_type" | "modifier" | "created_at">>;

type Props = { roll: DiceVisualRoll; compact?: boolean; onReady?: () => void };

type PhysicsModules = [typeof import("three"), typeof import("cannon-es")];
let physicsModulesPromise: Promise<PhysicsModules> | null = null;

export function preloadDicePhysics() {
  physicsModulesPromise ||= Promise.all([import("three"), import("cannon-es")]);
  return physicsModulesPromise;
}

const CHARACTER_COLORS: Record<string, [number, number]> = {
  sage: [0xb878ec, 0x52286f], vezemir: [0xd08a42, 0x6b301c], raziel: [0xd34969, 0x5d1326],
  varkh: [0x48bfa8, 0x174f48], morthak: [0x8e78dc, 0x342b70], guest: [0xb8bec7, 0x48505b],
};

function sidesFrom(dice: string) {
  const match = String(dice || "").match(/d(\d+)/i);
  return match ? Math.max(2, Number(match[1])) : 20;
}

function colorsFor(roll: DiceVisualRoll): [number, number] {
  const character = String(roll.character_id || "").toLocaleLowerCase("pt-BR");
  if (!character) return [0x111214, 0x050607];
  if (character === "vezemir") return [0x858b92, 0x343a40];
  if (CHARACTER_COLORS[character]) return CHARACTER_COLORS[character];
  if (roll.roll_type === "attack" || roll.roll_type === "damage") return [0xc64343, 0x5a1717];
  if (roll.roll_type === "saving_throw") return [0x5d8fd5, 0x213c70];
  return [0xd0a45f, 0x70451f];
}

function numberColorFor(roll: DiceVisualRoll) {
  return roll.character_id ? (String(roll.character_id).toLocaleLowerCase("pt-BR") === "vezemir" ? "#f1f3f5" : "#f3dfb6") : "#ff4055";
}

function seededRandom(seedText: string) {
  let seed = 2166136261;
  for (let index = 0; index < seedText.length; index += 1) {
    seed ^= seedText.charCodeAt(index);
    seed = Math.imul(seed, 16777619);
  }
  return () => {
    seed += 0x6d2b79f5;
    let value = seed;
    value = Math.imul(value ^ value >>> 15, value | 1);
    value ^= value + Math.imul(value ^ value >>> 7, value | 61);
    return ((value ^ value >>> 14) >>> 0) / 4294967296;
  };
}

export default function DicePhysicsCanvas({ roll, compact = false, onReady }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { onReady?.(); return; }
    let disposed = false;
    let animationFrame = 0;
    let cleanup = () => {};

    void preloadDicePhysics().then(([THREE, CANNON]) => {
      if (disposed) return;
      const deviceMemory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory;
      const mobile = window.matchMedia("(max-width: 760px)").matches;
      const lowPower = mobile || (navigator.hardwareConcurrency || 8) <= 4 || (deviceMemory != null && deviceMemory <= 4);
      const disposables: Array<Material | BufferGeometry | Texture> = [];
      type FaceMark = { normal: Vector3; value: string; setValue: (value: string) => void };
      const objects: Array<{ mesh: Mesh; body: Body; faces: FaceMark[]; wanted: string; target: CannonQuaternion; settled: boolean }> = [];
      const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: !lowPower, powerPreference: mobile ? "low-power" : "high-performance" });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, compact ? 1.15 : mobile ? 1 : lowPower ? 1.1 : 1.35));
      renderer.shadowMap.enabled = !lowPower;
      if (renderer.shadowMap.enabled) renderer.shadowMap.type = THREE.PCFShadowMap;
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.15;

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(compact ? 34 : 38, 1, .1, 100);
      camera.position.set(0, compact ? 5.4 : 4.5, compact ? 16 : 14);
      camera.lookAt(0, -.4, 0);
      scene.add(new THREE.HemisphereLight(0xfff1d0, 0x100d1c, compact ? 2.4 : 2.1));
      const keyLight = new THREE.DirectionalLight(0xffd596, compact ? 5 : 5.8);
      keyLight.position.set(-5, 9, 7); keyLight.castShadow = !lowPower;
      keyLight.shadow.mapSize.set(compact ? 256 : lowPower ? 256 : 512, compact ? 256 : lowPower ? 256 : 512); scene.add(keyLight);
      const rimLight = new THREE.DirectionalLight(0x86a9ff, 2.8); rimLight.position.set(7, 4, -6); scene.add(rimLight);

      const world = new CANNON.World({ gravity: new CANNON.Vec3(0, compact ? -22 : -18, 0) });
      world.allowSleep = true; world.defaultContactMaterial.friction = .38; world.defaultContactMaterial.restitution = .44;
      const floorBody = new CANNON.Body({ mass: 0, shape: new CANNON.Plane() });
      floorBody.quaternion.setFromEuler(-Math.PI / 2, 0, 0); floorBody.position.y = -3.1; world.addBody(floorBody);
      const floorMesh = new THREE.Mesh(new THREE.PlaneGeometry(30, 14), new THREE.ShadowMaterial({ color: 0x000000, opacity: compact ? .28 : .5 }));
      floorMesh.rotation.x = -Math.PI / 2; floorMesh.position.y = -3.08; floorMesh.receiveShadow = true; scene.add(floorMesh);
      disposables.push(floorMesh.geometry, floorMesh.material);

      const sides = sidesFrom(roll.dice);
      const results = roll.individual_results.slice(0, compact ? 8 : mobile ? 4 : 12);
      const [primary, secondary] = colorsFor(roll);
      const critical = results.some((value) => value === sides);
      const fumble = sides === 20 && results.some((value) => value === 1);

      const d10Geometry = (): BufferGeometry => {
        const positions: number[] = [];
        const top = new THREE.Vector3(0, 1.18, 0);
        const bottom = new THREE.Vector3(0, -1.18, 0);
        const ring = Array.from({ length: 5 }, (_, index) => {
          const angle = index * Math.PI * 2 / 5 - Math.PI / 2;
          return new THREE.Vector3(Math.cos(angle) * 1.05, 0, Math.sin(angle) * 1.05);
        });
        const triangle = (a: Vector3, b: Vector3, c: Vector3) => positions.push(a.x, a.y, a.z, b.x, b.y, b.z, c.x, c.y, c.z);
        for (let index = 0; index < ring.length; index += 1) {
          const current = ring[index];
          const next = ring[(index + 1) % ring.length];
          triangle(top, next, current);
          triangle(bottom, current, next);
        }
        const geometry = new THREE.BufferGeometry();
        geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
        geometry.computeVertexNormals();
        return geometry;
      };

      const geometryFor = (die: number): BufferGeometry => {
        if (die === 4) return new THREE.TetrahedronGeometry(1.08);
        if (die === 6) return new THREE.BoxGeometry(1.5, 1.5, 1.5);
        if (die === 8) return new THREE.OctahedronGeometry(1.1);
        if (die === 10) return d10Geometry();
        if (die === 12) return new THREE.DodecahedronGeometry(1.05);
        if (die === 20) return new THREE.IcosahedronGeometry(1.08);
        return new THREE.IcosahedronGeometry(1.05, 1);
      };

      const convexShapeFor = (geometry: BufferGeometry): Shape => {
        const source = geometry.index ? geometry.toNonIndexed() : geometry;
        const position = source.getAttribute("position");
        const vertices: InstanceType<typeof CANNON.Vec3>[] = [];
        const faces: number[][] = [];
        const indexes = new Map<string, number>();
        const vertexIndex = (offset: number) => {
          const x = position.getX(offset), y = position.getY(offset), z = position.getZ(offset);
          const key = `${x.toFixed(5)}:${y.toFixed(5)}:${z.toFixed(5)}`;
          const existing = indexes.get(key);
          if (existing != null) return existing;
          const index = vertices.length; vertices.push(new CANNON.Vec3(x, y, z)); indexes.set(key, index); return index;
        };
        for (let index = 0; index < position.count; index += 3) {
          const face = [vertexIndex(index), vertexIndex(index + 1), vertexIndex(index + 2)];
          if (new Set(face).size === 3) faces.push(face);
        }
        if (source !== geometry) source.dispose();
        try { return new CANNON.ConvexPolyhedron({ vertices, faces }); } catch { return new CANNON.Sphere(1); }
      };

      const faceNumbersFor = (mesh: Mesh, geometry: BufferGeometry, die: number, labels?: string[], numberColor = "#f3dfb6"): FaceMark[] => {
        const source = geometry.index ? geometry.toNonIndexed() : geometry;
        const position = source.getAttribute("position");
        const groups = new Map<string, { normal: Vector3; vertices: Map<string, Vector3> }>();
        for (let index = 0; index < position.count; index += 3) {
          const a = new THREE.Vector3(position.getX(index), position.getY(index), position.getZ(index));
          const b = new THREE.Vector3(position.getX(index + 1), position.getY(index + 1), position.getZ(index + 1));
          const c = new THREE.Vector3(position.getX(index + 2), position.getY(index + 2), position.getZ(index + 2));
          const normal = b.clone().sub(a).cross(c.clone().sub(a)).normalize();
          const plane = normal.dot(a);
          const key = `${normal.x.toFixed(3)}:${normal.y.toFixed(3)}:${normal.z.toFixed(3)}:${plane.toFixed(3)}`;
          const group = groups.get(key) || { normal, vertices: new Map<string, Vector3>() };
          [a, b, c].forEach((vertex) => group.vertices.set(`${vertex.x.toFixed(4)}:${vertex.y.toFixed(4)}:${vertex.z.toFixed(4)}`, vertex));
          groups.set(key, group);
        }
        if (source !== geometry) source.dispose();

        const faces = [...groups.values()].slice(0, die);
        const size = die === 4 ? .74 : die === 6 ? .72 : die === 8 ? .64 : die === 10 ? .5 : die === 12 ? .59 : .58;
        const values = faces.map((_, index) => labels?.[index] ?? String(index + 1));

        return faces.map((face, index) => {
          const center = [...face.vertices.values()].reduce((sum, vertex) => sum.add(vertex), new THREE.Vector3()).divideScalar(face.vertices.size);
          const numberCanvas = document.createElement("canvas"); numberCanvas.width = 256; numberCanvas.height = 256;
          const context = numberCanvas.getContext("2d");
          const texture = new THREE.CanvasTexture(numberCanvas); texture.colorSpace = THREE.SRGBColorSpace;
          const material = new THREE.MeshBasicMaterial({ map: texture, transparent: true, depthWrite: false, side: THREE.DoubleSide, toneMapped: false });
          const plane = new THREE.Mesh(new THREE.PlaneGeometry(size, size), material);
          plane.position.copy(center).addScaledVector(face.normal, .014);
          plane.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), face.normal);
          mesh.add(plane); disposables.push(texture, material, plane.geometry);

          const mark: FaceMark = {
            normal: face.normal.clone(), value: values[index],
            setValue(value: string) {
              mark.value = value;
              if (!context) return;
              context.clearRect(0, 0, 256, 256);
              context.textAlign = "center"; context.textBaseline = "middle";
              context.font = value.length > 2 ? "900 118px Georgia" : "900 150px Georgia";
              context.lineJoin = "round"; context.lineWidth = 12;
              context.strokeStyle = "rgba(25,12,8,.9)";
              context.shadowColor = numberColor === "#ff4055" ? "rgba(255,24,48,.9)" : "rgba(0,0,0,.7)"; context.shadowBlur = numberColor === "#ff4055" ? 16 : 7; context.shadowOffsetY = 4;
              context.strokeText(value, 128, 132);
              context.fillStyle = numberColor; context.fillText(value, 128, 132);
              context.shadowBlur = 0; context.shadowOffsetY = 0;
              texture.needsUpdate = true;
            },
          };
          mark.setValue(mark.value);
          return mark;
        });
      };

      const settleTopFace = (mesh: Mesh, faces: FaceMark[], wanted: string) => {
        if (!faces.length) return;
        const top = faces.reduce((best, face) => face.normal.clone().applyQuaternion(mesh.quaternion).y > best.normal.clone().applyQuaternion(mesh.quaternion).y ? face : best);
        const existing = faces.find((face) => face.value === wanted);
        if (existing && existing !== top) existing.setValue(top.value);
        top.setValue(wanted);
      };

      const visualResults = sides === 100
        ? results.flatMap((result, resultIndex) => {
            const percentile = result === 100 ? 0 : Math.max(0, Math.min(99, result));
            return [
              { die: 10, wanted: String(Math.floor(percentile / 10) * 10).padStart(2, "0"), labels: Array.from({ length: 10 }, (_, index) => String(index * 10).padStart(2, "0")), seed: `${resultIndex}:tens` },
              { die: 10, wanted: String(percentile % 10), labels: Array.from({ length: 10 }, (_, index) => String(index)), seed: `${resultIndex}:units` },
            ];
          })
        : results.map((result, resultIndex) => ({ die: sides, wanted: String(result), labels: undefined, seed: String(resultIndex) }));

      const count = Math.max(1, visualResults.length);
      visualResults.forEach((visual, index) => {
        const random = seededRandom(`${roll.id}:${roll.created_at || ""}:${visual.wanted}:${visual.seed}`);
        const geometry = geometryFor(visual.die);
        const material = mobile
          ? new THREE.MeshStandardMaterial({ color: index % 2 ? secondary : primary, metalness: critical ? .35 : .14, roughness: critical ? .3 : .46,
            emissive: critical ? 0x6b4a10 : fumble ? 0x4c0710 : secondary, emissiveIntensity: critical || fumble ? .3 : .08, flatShading: true })
          : new THREE.MeshPhysicalMaterial({ color: index % 2 ? secondary : primary, metalness: critical ? .48 : .24,
            roughness: critical ? .18 : .3, clearcoat: .72, clearcoatRoughness: .18,
            emissive: critical ? 0x6b4a10 : fumble ? 0x4c0710 : secondary, emissiveIntensity: critical || fumble ? .42 : .12, flatShading: true });
        const mesh = new THREE.Mesh(geometry, material); mesh.castShadow = true; mesh.receiveShadow = true;
        const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), new THREE.LineBasicMaterial({ color: 0xf5dfad, transparent: true, opacity: .48 }));
        mesh.add(edges);
        const faces = faceNumbersFor(mesh, geometry, visual.die, visual.labels, numberColorFor(roll));
        const resultFace = faces.find((face) => face.value === visual.wanted) || faces[Math.floor(random() * Math.max(1, faces.length))];
        if (resultFace && resultFace.value !== visual.wanted) resultFace.setValue(visual.wanted);
        const alignment = new THREE.Quaternion().setFromUnitVectors(resultFace?.normal.clone().normalize() || new THREE.Vector3(0, 1, 0), new THREE.Vector3(0, 1, 0));
        alignment.premultiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), random() * Math.PI * 2));
        const target = new CANNON.Quaternion(alignment.x, alignment.y, alignment.z, alignment.w);
        scene.add(mesh); disposables.push(geometry, material, edges.geometry, edges.material);
        const body = new CANNON.Body({ mass: 1.15, shape: convexShapeFor(geometry), linearDamping: .07, angularDamping: .11 });
        const lane = count === 1 ? 0 : (index / Math.max(1, count - 1) - .5) * Math.min(8.5, count * 1.65);
        body.position.set(lane + (random() - .5) * 3.2, 6.3 + random() * 3.2, (random() - .5) * 3.2);
        body.velocity.set((random() - .5) * 6.5, .7 + random() * 2.4, (random() - .5) * 4.4);
        body.angularVelocity.set((random() - .5) * 22, (random() - .5) * 24, (random() - .5) * 22);
        body.quaternion.setFromEuler(random() * Math.PI * 2, random() * Math.PI * 2, random() * Math.PI * 2);
        world.addBody(body); objects.push({ mesh, body, faces, wanted: visual.wanted, target, settled: false });
      });

      let burst: Object3D | null = null;
      if (critical || fumble) {
        const positions = new Float32Array(180 * 3);
        for (let index = 0; index < positions.length; index += 3) {
          const angle = Math.random() * Math.PI * 2, radius = 2 + Math.random() * 7;
          positions[index] = Math.cos(angle) * radius; positions[index + 1] = -1 + Math.random() * 7; positions[index + 2] = Math.sin(angle) * radius * .35;
        }
        const geometry = new THREE.BufferGeometry(); geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        const material = new THREE.PointsMaterial({ color: critical ? 0xffd76a : 0xff4058, size: compact ? .08 : .12, transparent: true, opacity: .85 });
        burst = new THREE.Points(geometry, material); scene.add(burst); disposables.push(geometry, material);
      }

      const resize = () => {
        const width = Math.max(1, canvas.clientWidth), height = Math.max(1, canvas.clientHeight);
        renderer.setSize(width, height, false); camera.aspect = width / height; camera.updateProjectionMatrix();
        camera.updateMatrixWorld();
      };
      resize(); window.addEventListener("resize", resize);
      const containToViewport = (body: Body) => {
        camera.updateMatrixWorld();
        const point = new THREE.Vector3(body.position.x, body.position.y, body.position.z);
        const projected = point.clone().project(camera);
        if (![projected.x, projected.y, projected.z].every(Number.isFinite)) return;

        // Reserve space for the die radius so its faces never leave the visible panel.
        const marginX = compact ? .78 : .88;
        const marginY = compact ? .68 : .78;
        const targetX = THREE.MathUtils.clamp(projected.x, -marginX, marginX);
        const targetY = THREE.MathUtils.clamp(projected.y, -marginY, marginY);
        const correctionX = targetX - projected.x;
        const correctionY = targetY - projected.y;
        if (Math.abs(correctionX) < .001 && Math.abs(correctionY) < .001) return;

        const viewPoint = point.clone().applyMatrix4(camera.matrixWorldInverse);
        const depth = Math.max(1, -viewPoint.z);
        const halfFov = THREE.MathUtils.degToRad(camera.fov / 2);
        const worldPerNdcX = depth * Math.tan(halfFov) * camera.aspect;
        const worldPerNdcY = depth * Math.tan(halfFov);
        const cameraRight = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion).normalize();
        const cameraUp = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion).normalize();
        body.position.vadd(new CANNON.Vec3(
          cameraRight.x * correctionX * worldPerNdcX + cameraUp.x * correctionY * worldPerNdcY,
          cameraRight.y * correctionX * worldPerNdcX + cameraUp.y * correctionY * worldPerNdcY,
          cameraRight.z * correctionX * worldPerNdcX + cameraUp.z * correctionY * worldPerNdcY,
        ));
        body.velocity.x *= .35; body.velocity.z *= .35;
      };
      const settleStart = DICE_SETTLE_START;
      const settleDuration = DICE_SETTLE_DURATION;
      const settleEnd = settleStart + settleDuration;
      const startedAt = performance.now();
      let previousFrame = startedAt; let elapsed = 0;
      const render = () => {
        if (disposed) return;
        const currentFrame = performance.now();
        const delta = Math.min((currentFrame - previousFrame) / 1000, 1 / 30);
        previousFrame = currentFrame;
        elapsed = diceElapsedSeconds(startedAt, currentFrame);
        world.step(1 / 60, delta, 5);
        objects.forEach((object) => {
          const { mesh, body } = object;
          let finalized = false;
          if (!object.settled && elapsed >= settleStart) {
            const progress = Math.min(1, (elapsed - settleStart) / settleDuration);
            const blend = .025 + progress * .12;
            body.quaternion.slerp(object.target, blend, body.quaternion);
            const damping = 1 - progress * .12;
            body.angularVelocity.set(body.angularVelocity.x * damping, body.angularVelocity.y * damping, body.angularVelocity.z * damping);
            body.velocity.set(body.velocity.x * (1 - progress * .035), body.velocity.y, body.velocity.z * (1 - progress * .035));
          }
          if (!object.settled && elapsed >= settleEnd) {
            body.quaternion.set(object.target.x, object.target.y, object.target.z, object.target.w);
            body.velocity.set(0, 0, 0); body.angularVelocity.set(0, 0, 0); body.sleep();
            object.settled = true;
            finalized = true;
          }
          containToViewport(body);
          mesh.position.set(body.position.x, body.position.y, body.position.z);
          mesh.quaternion.set(body.quaternion.x, body.quaternion.y, body.quaternion.z, body.quaternion.w);
          if (finalized) settleTopFace(mesh, object.faces, object.wanted);
        });
        if (burst) { burst.rotation.z += delta * .18; burst.scale.setScalar(1 + Math.min(.18, elapsed * .025)); }
        renderer.render(scene, camera); animationFrame = window.requestAnimationFrame(render);
      };
      render();
      onReady?.();
      cleanup = () => {
        window.cancelAnimationFrame(animationFrame); window.removeEventListener("resize", resize);
        objects.forEach(({ body }) => world.removeBody(body)); world.removeBody(floorBody);
        disposables.forEach((item) => item.dispose()); renderer.dispose();
      };
    }).catch(() => { onReady?.(); });

    return () => { disposed = true; window.cancelAnimationFrame(animationFrame); cleanup(); };
  }, [compact, roll]);

  return <canvas ref={canvasRef} className={compact ? "dice-physics-canvas compact" : "dice-physics-canvas"} />;
}
