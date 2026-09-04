import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

/**
 * HeroScene3D: Minimal & Hollow-Type Architectural CAD/BIM Wireframe Model.
 * Designed with ultra-clean, skeletonized architectural elements:
 * - Hollow translucent glass partition envelopes with razor-sharp 1px wireframe edges.
 * - Open structural elevator cage and hollow shear-wall core.
 * - Floating open-riser cantilevered stair treads with wireframe handrails.
 * - Hollow structural column wireframe cages.
 * - Delicate laser egress escape vector with traveling pulse orb.
 * - Floating minimalist holographic CAD compliance HUD.
 * - Zero solid, bulky, or toy-like blocks.
 */
export default function HeroScene3D() {
  const containerRef = useRef(null);
  const isVisibleRef = useRef(true);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }

    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || 750;

    // 1. Scene & Camera Setup (Clean Axonometric Perspective)
    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(36, width / height, 0.1, 1000);
    camera.position.set(28, 28, 38);
    camera.lookAt(0, -1.0, 0);

    // 2. WebGL Renderer
    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference: 'high-performance',
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(width, height);
      renderer.setClearColor(0x000000, 0);
      container.appendChild(renderer.domElement);
    } catch (e) {
      console.warn('WebGL initialization failed, skipping 3D hero scene:', e);
      return;
    }

    // 3. Crisp Architectural Lighting
    const ambientLight = new THREE.AmbientLight(0xFFFFFF, 1.2);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xFFFFFF, 2.0);
    keyLight.position.set(35, 50, 30);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x94A3B8, 0.8);
    fillLight.position.set(-30, 20, -25);
    scene.add(fillLight);

    const redAccentLight = new THREE.DirectionalLight(0xEF4444, 2.2);
    redAccentLight.position.set(-10, 15, -30);
    scene.add(redAccentLight);

    // 4. Scene Graph Root Group (Lowered to create spacious stage beneath headline)
    const rootGroup = new THREE.Group();
    rootGroup.position.set(0, -4.5, 0);
    scene.add(rootGroup);

    const disposables = [];

    // =========================================================================
    // A. FOUNDATION: MINIMAL DRAFTING GRID & HOLLOW GLASS FLOOR SLAB
    // =========================================================================
    // Minimal, ultra-fine coordinate grid
    const gridHelper = new THREE.GridHelper(52, 26, 0xEF4444, 0x334155);
    gridHelper.position.y = -0.15;
    gridHelper.material.opacity = 0.3;
    gridHelper.material.transparent = true;
    rootGroup.add(gridHelper);
    disposables.push(gridHelper.geometry, gridHelper.material);

    // Hollow floor slab (Sheer tinted dark glass plate with glowing perimeter)
    const slabGeo = new THREE.BoxGeometry(40, 0.2, 24);
    const slabMat = new THREE.MeshStandardMaterial({
      color: 0x0A0F1D,
      transparent: true,
      opacity: 0.45,
      roughness: 0.1,
      metalness: 0.3,
    });
    const slab = new THREE.Mesh(slabGeo, slabMat);
    slab.position.y = -0.1;
    rootGroup.add(slab);
    disposables.push(slabGeo, slabMat);

    // Glowing red perimeter boundary line
    const slabEdges = new THREE.EdgesGeometry(slabGeo);
    const slabEdgesMat = new THREE.LineBasicMaterial({
      color: 0xEF4444,
      transparent: true,
      opacity: 0.8,
    });
    const slabBorder = new THREE.LineSegments(slabEdges, slabEdgesMat);
    slabBorder.position.copy(slab.position);
    rootGroup.add(slabBorder);
    disposables.push(slabEdges, slabEdgesMat);

    // =========================================================================
    // B. HOLLOW-TYPE ARCHITECTURAL MATERIALS
    // =========================================================================
    // 1. Sheer Transparent Wall Glass (Ultra-light translucent acrylic/glass)
    const hollowGlassMat = new THREE.MeshBasicMaterial({
      color: 0x93C5FD,
      transparent: true,
      opacity: 0.07,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    disposables.push(hollowGlassMat);

    // 2. Core Translucent Crimson Glass
    const hollowCoreMat = new THREE.MeshBasicMaterial({
      color: 0xEF4444,
      transparent: true,
      opacity: 0.1,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    disposables.push(hollowCoreMat);

    // 3. Crisp Silver/White Architectural Wireframe Lines
    const wireWhiteMat = new THREE.LineBasicMaterial({
      color: 0xFFFFFF,
      transparent: true,
      opacity: 0.85,
    });
    disposables.push(wireWhiteMat);

    // 4. Hairline Muted Slate Edge Lines
    const wireSlateMat = new THREE.LineBasicMaterial({
      color: 0x64748B,
      transparent: true,
      opacity: 0.65,
    });
    disposables.push(wireSlateMat);

    // 5. Statutory Crimson Wireframe Lines (for structural core & exit bounds)
    const wireCrimsonMat = new THREE.LineBasicMaterial({
      color: 0xEF4444,
      transparent: true,
      opacity: 0.9,
    });
    disposables.push(wireCrimsonMat);

    // 6. Compliant Emerald Wireframe Lines (for exit stair enclosure)
    const wireEmeraldMat = new THREE.LineBasicMaterial({
      color: 0x10B981,
      transparent: true,
      opacity: 0.9,
    });
    disposables.push(wireEmeraldMat);

    // Helper: Create a minimal hollow-type architectural room/wall
    const createHollowVolume = (pos, size, fillMat, lineMat) => {
      const geo = new THREE.BoxGeometry(size[0], size[1], size[2]);
      disposables.push(geo);

      // Translucent inner face
      if (fillMat) {
        const mesh = new THREE.Mesh(geo, fillMat);
        mesh.position.set(pos[0], pos[1], pos[2]);
        rootGroup.add(mesh);
      }

      // Crisp skeleton edge wireframe
      const edges = new THREE.EdgesGeometry(geo);
      disposables.push(edges);
      const wire = new THREE.LineSegments(edges, lineMat);
      wire.position.set(pos[0], pos[1], pos[2]);
      rootGroup.add(wire);

      return wire;
    };

    // =========================================================================
    // C. MINIMAL HOLLOW STRUCTURAL COLUMNS (8m Bay Grid Wireframes)
    // =========================================================================
    const colCoords = [
      [-15, -7], [-7.5, -7], [0, -7], [7.5, -7], [15, -7],
      [-15, 0],  [-7.5, 0],           [7.5, 0],  [15, 0],
      [-15, 7],  [-7.5, 7],  [0, 7],  [7.5, 7],  [15, 7],
    ];

    colCoords.forEach(([cx, cz]) => {
      createHollowVolume([cx, 1.8, cz], [0.45, 3.6, 0.45], hollowGlassMat, wireWhiteMat);
    });

    // =========================================================================
    // D. MINIMAL HOLLOW STRUCTURAL SERVICE CORE (Hollow Elevator Shafts)
    // =========================================================================
    // Outer Core Enclosure (Translucent Crimson Cage)
    createHollowVolume([0, 2.2, -3.5], [10, 4.4, 4.8], hollowCoreMat, wireCrimsonMat);

    // Internal Dual Elevator Shafts (Wireframe dividers)
    createHollowVolume([-2.4, 2.2, -3.5], [4.4, 4.4, 4.4], null, wireSlateMat);
    createHollowVolume([2.4, 2.2, -3.5], [4.4, 4.4, 4.4], null, wireSlateMat);

    // Elevator Door Opening Frames (Minimal wire rectangles)
    createHollowVolume([-2.4, 1.4, -1.2], [1.8, 2.6, 0.05], hollowGlassMat, wireCrimsonMat);
    createHollowVolume([2.4, 1.4, -1.2], [1.8, 2.6, 0.05], hollowGlassMat, wireCrimsonMat);

    // =========================================================================
    // E. MINIMAL HOLLOW EGRESS STAIRWELL (Floating Cantilevered Treads)
    // =========================================================================
    // Compliant Exit Stair Enclosure (East Perimeter: X = 13.5 to 18.5, Z = 2.5 to 8.5)
    createHollowVolume([16, 2.4, 5.5], [5.5, 4.8, 6.2], hollowGlassMat, wireEmeraldMat);

    // 10 Floating Open-Riser Architectural Stair Treads
    const numSteps = 10;
    const stepWidth = 1.6;
    const stepDepth = 0.34;
    const stepRise = 0.22;

    for (let i = 0; i < numSteps; i++) {
      const stepY = stepRise * (i + 1);
      const stepZ = 3.2 + i * stepDepth;
      // Hollow floating tread plate
      createHollowVolume([14.8, stepY, stepZ], [stepWidth, 0.04, stepDepth], hollowGlassMat, wireWhiteMat);
    }

    // Floating Landing Platform
    createHollowVolume([16.0, stepRise * numSteps, 6.8], [3.2, 0.06, 1.8], hollowGlassMat, wireEmeraldMat);

    // Minimal Fire Exit Door Frame (Ajar wireframe door leaf)
    const doorLeafGeo = new THREE.BoxGeometry(0.04, 2.4, 1.1);
    const doorWireGeo = new THREE.EdgesGeometry(doorLeafGeo);
    disposables.push(doorLeafGeo, doorWireGeo);
    const doorLeaf = new THREE.LineSegments(doorWireGeo, wireEmeraldMat);
    doorLeaf.position.set(13.2, 1.2, 3.8);
    doorLeaf.rotation.y = 0.7; // Ajar showing egress clearance
    rootGroup.add(doorLeaf);

    // Floor Clearance Swing Arc (Delicate dashed circle arc)
    const swingCurve = new THREE.EllipseCurve(13.2, 3.3, 1.1, 1.1, 0, Math.PI / 2, false, 0);
    const swingPoints = swingCurve.getPoints(20);
    const swingGeo = new THREE.BufferGeometry().setFromPoints(
      swingPoints.map(p => new THREE.Vector3(p.x, 0.04, p.y))
    );
    const swingMat = new THREE.LineDashedMaterial({
      color: 0x10B981,
      dashSize: 0.2,
      gapSize: 0.15,
    });
    disposables.push(swingGeo, swingMat);
    const swingLine = new THREE.Line(swingGeo, swingMat);
    swingLine.computeLineDistances();
    rootGroup.add(swingLine);

    // Illuminated Minimal Green Exit Badge
    const exitBadgeGeo = new THREE.BoxGeometry(0.06, 0.25, 0.7);
    const exitBadgeEdges = new THREE.EdgesGeometry(exitBadgeGeo);
    disposables.push(exitBadgeGeo, exitBadgeEdges);
    const exitBadge = new THREE.LineSegments(exitBadgeEdges, wireEmeraldMat);
    exitBadge.position.set(13.2, 2.7, 4.2);
    rootGroup.add(exitBadge);

    // =========================================================================
    // F. MINIMAL HOLLOW OFFICE PARTITIONS & GLASS BOUNDARIES
    // =========================================================================
    // Executive Suite (West Corner)
    createHollowVolume([-13.5, 1.5, -6.5], [9.5, 3.0, 0.08], hollowGlassMat, wireWhiteMat);
    createHollowVolume([-8.75, 1.5, -3.5], [0.08, 3.0, 6.0], hollowGlassMat, wireWhiteMat);

    // Meeting Room (West Center)
    createHollowVolume([-13.5, 1.5, 2.0], [9.5, 3.0, 0.08], hollowGlassMat, wireWhiteMat);
    createHollowVolume([-8.75, 1.5, 4.8], [0.08, 3.0, 5.6], hollowGlassMat, wireWhiteMat);

    // Minimal Open-Office Workstation Wireframe Dividers (low 1.2m screen frames)
    const dividerCoords = [
      [-3.5, 3.6], [3.5, 3.6],
      [-3.5, 6.8], [3.5, 6.8],
    ];

    dividerCoords.forEach(([px, pz]) => {
      createHollowVolume([px, 0.6, pz], [4.0, 1.2, 0.04], hollowGlassMat, wireSlateMat);
      // Minimal desk plate outline
      createHollowVolume([px, 0.72, pz], [3.8, 0.02, 1.2], null, wireSlateMat);
    });

    // =========================================================================
    // G. STATUTORY LASER EGRESS TRAVEL VECTOR (Razor-Sharp Spline & Pulse)
    // =========================================================================
    const egressPoints = [
      new THREE.Vector3(-13.5, 0.12, 4.8),  // Point A: Inside meeting room
      new THREE.Vector3(-8.75, 0.12, 2.2),  // Point B: Room exit doorway
      new THREE.Vector3(0, 0.12, 2.2),      // Point C: Main central corridor
      new THREE.Vector3(8.5, 0.12, 2.2),    // Point D: Corridor approach to East core
      new THREE.Vector3(13.2, 0.12, 4.2),   // Point E: Fire stair door threshold
      new THREE.Vector3(14.8, 0.12, 4.2),   // Point F: Inside protected stair flight
    ];

    const egressCurve = new THREE.CatmullRomCurve3(egressPoints);
    const egressCurvePoints = egressCurve.getPoints(140);
    const egressPathGeo = new THREE.BufferGeometry().setFromPoints(egressCurvePoints);

    const egressPathMat = new THREE.LineBasicMaterial({
      color: 0xEF4444,
      transparent: true,
      opacity: 0.95,
    });
    disposables.push(egressPathGeo, egressPathMat);
    const egressPathLine = new THREE.Line(egressPathGeo, egressPathMat);
    rootGroup.add(egressPathLine);

    // Discrete Waypoint Rings along the path
    const waypointRingGeo = new THREE.RingGeometry(0.16, 0.24, 16);
    waypointRingGeo.rotateX(-Math.PI / 2);
    const waypointRingMat = new THREE.MeshBasicMaterial({
      color: 0xEF4444,
      side: THREE.DoubleSide,
    });
    disposables.push(waypointRingGeo, waypointRingMat);

    egressPoints.slice(0, 5).forEach((pt) => {
      const ring = new THREE.Mesh(waypointRingGeo, waypointRingMat);
      ring.position.set(pt.x, 0.14, pt.z);
      rootGroup.add(ring);
    });

    // Traveling Pulsing Laser Node along the egress route
    const pulseGeo = new THREE.SphereGeometry(0.28, 12, 12);
    const pulseMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF });
    disposables.push(pulseGeo, pulseMat);
    const pulseNode = new THREE.Mesh(pulseGeo, pulseMat);
    rootGroup.add(pulseNode);

    // Pulse Wave Halo
    const pulseHaloGeo = new THREE.RingGeometry(0.28, 0.52, 20);
    pulseHaloGeo.rotateX(-Math.PI / 2);
    const pulseHaloMat = new THREE.MeshBasicMaterial({
      color: 0x10B981,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.8,
    });
    disposables.push(pulseHaloGeo, pulseHaloMat);
    const pulseHalo = new THREE.Mesh(pulseHaloGeo, pulseHaloMat);
    rootGroup.add(pulseHalo);

    // =========================================================================
    // H. MINIMAL HOLOGRAPHIC CAD COMPLIANCE HUD
    // =========================================================================
    const hudCanvas = document.createElement('canvas');
    hudCanvas.width = 512;
    hudCanvas.height = 130;
    const ctx = hudCanvas.getContext('2d');
    if (ctx) {
      // Sheer dark glass HUD with crimson hairline border
      ctx.fillStyle = 'rgba(10, 15, 29, 0.88)';
      ctx.roundRect(4, 4, 504, 122, 8);
      ctx.fill();

      ctx.strokeStyle = '#EF4444';
      ctx.lineWidth = 2.5;
      ctx.roundRect(4, 4, 504, 122, 8);
      ctx.stroke();

      ctx.fillStyle = '#94A3B8';
      ctx.font = 'bold 20px monospace';
      ctx.fillText('UAE FLSC 3.16 • TRAVEL DISTANCE', 24, 40);

      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 36px sans-serif';
      ctx.fillText('26.8m', 24, 92);

      ctx.fillStyle = '#10B981';
      ctx.font = 'bold 24px sans-serif';
      ctx.fillText('< 45.0m [PASS ✓]', 165, 92);
    }

    const hudTexture = new THREE.CanvasTexture(hudCanvas);
    hudTexture.minFilter = THREE.LinearFilter;
    disposables.push(hudTexture);

    const hudPlaneGeo = new THREE.PlaneGeometry(5.8, 1.48);
    const hudPlaneMat = new THREE.MeshBasicMaterial({
      map: hudTexture,
      transparent: true,
      side: THREE.DoubleSide,
    });
    disposables.push(hudPlaneGeo, hudPlaneMat);

    const hudMesh = new THREE.Mesh(hudPlaneGeo, hudPlaneMat);
    hudMesh.position.set(13.5, 4.2, 0.8);
    hudMesh.rotation.y = 0.25;
    hudMesh.rotation.x = -0.18;
    rootGroup.add(hudMesh);

    // Thin dashed leader line connecting HUD down to stairwell door
    const leaderPoints = [
      new THREE.Vector3(13.5, 3.4, 0.8),
      new THREE.Vector3(13.2, 0.15, 3.8),
    ];
    const leaderGeo = new THREE.BufferGeometry().setFromPoints(leaderPoints);
    const leaderMat = new THREE.LineDashedMaterial({
      color: 0xEF4444,
      dashSize: 0.18,
      gapSize: 0.12,
    });
    disposables.push(leaderGeo, leaderMat);
    const leaderLine = new THREE.Line(leaderGeo, leaderMat);
    leaderLine.computeLineDistances();
    rootGroup.add(leaderLine);

    // =========================================================================
    // I. MOUSE PARALLAX & ANIMATION LOOP
    // =========================================================================
    let targetRotX = 0;
    let targetRotY = 0;
    let currentRotX = 0;
    let currentRotY = 0;

    const handleMouseMove = (e) => {
      const normX = (e.clientX / window.innerWidth) - 0.5;
      const normY = (e.clientY / window.innerHeight) - 0.5;
      targetRotY = normX * 0.22;
      targetRotX = normY * 0.12;
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });

    const handleResize = () => {
      if (!container || !renderer) return;
      const w = container.clientWidth || window.innerWidth;
      const h = container.clientHeight || 750;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    const observer = new IntersectionObserver(
      ([entry]) => {
        isVisibleRef.current = entry.isIntersecting;
      },
      { threshold: 0.05 }
    );
    observer.observe(container);

    let animId;
    const startTime = performance.now();

    const animate = () => {
      animId = requestAnimationFrame(animate);

      if (!isVisibleRef.current) return;

      const elapsed = (performance.now() - startTime) * 0.001;

      // Subtle, damped axonometric tilt
      currentRotX += (targetRotX - currentRotX) * 0.05;
      currentRotY += (targetRotY - currentRotY) * 0.05;

      rootGroup.rotation.y = currentRotY + Math.sin(elapsed * 0.18) * 0.025;
      rootGroup.rotation.x = currentRotX + Math.cos(elapsed * 0.14) * 0.012;

      // Gentle floating elevation
      rootGroup.position.y = -4.5 + Math.sin(elapsed * 0.5) * 0.14;

      // Pulse along spline
      const t = (elapsed * 0.2) % 1;
      const pt = egressCurve.getPointAt(t);
      pulseNode.position.copy(pt);
      pulseHalo.position.set(pt.x, pt.y + 0.02, pt.z);
      pulseHalo.scale.setScalar(1 + Math.sin(elapsed * 5) * 0.25);

      // Float HUD
      hudMesh.position.y = 4.2 + Math.sin(elapsed * 1.1) * 0.1;

      renderer.render(scene, camera);
    };

    animate();

    // =========================================================================
    // J. CLEANUP
    // =========================================================================
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      observer.disconnect();

      if (renderer.domElement && renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }

      disposables.forEach((item) => {
        if (item && typeof item.dispose === 'function') {
          item.dispose();
        }
      });
      renderer.dispose();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="hero-3d-scene-canvas-wrap"
      aria-hidden="true"
    />
  );
}
