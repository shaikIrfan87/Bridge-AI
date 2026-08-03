/**
 * Three.js Animated Background
 * Particle system with geometric shapes
 */

(function () {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
        75,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );

    const renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        alpha: true,
        antialias: true
    });

    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);

    camera.position.z = 50;

    // Create particle system
    const particleCount = 1000;
    const particles = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);

    // Color palette (HSL converted to RGB)
    const colorPalette = [
        new THREE.Color(0.694, 0.494, 0.918), // Purple
        new THREE.Color(0.463, 0.290, 0.635), // Dark purple
        new THREE.Color(0.980, 0.341, 0.671), // Pink
        new THREE.Color(0.000, 0.949, 0.996), // Cyan
    ];

    for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;

        // Random positions
        positions[i3] = (Math.random() - 0.5) * 100;
        positions[i3 + 1] = (Math.random() - 0.5) * 100;
        positions[i3 + 2] = (Math.random() - 0.5) * 100;

        // Random colors from palette
        const color = colorPalette[Math.floor(Math.random() * colorPalette.length)];
        colors[i3] = color.r;
        colors[i3 + 1] = color.g;
        colors[i3 + 2] = color.b;

        // Random sizes
        sizes[i] = Math.random() * 2 + 0.5;
    }

    particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particles.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    particles.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    // Particle material
    const particleMaterial = new THREE.PointsMaterial({
        size: 0.5,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending,
        sizeAttenuation: true
    });

    const particleSystem = new THREE.Points(particles, particleMaterial);
    scene.add(particleSystem);

    // Add geometric shapes
    const geometries = [
        new THREE.TorusGeometry(10, 3, 16, 100),
        new THREE.OctahedronGeometry(8),
        new THREE.IcosahedronGeometry(6)
    ];

    const shapes = [];

    geometries.forEach((geometry, index) => {
        const material = new THREE.MeshBasicMaterial({
            color: colorPalette[index],
            wireframe: true,
            transparent: true,
            opacity: 0.1
        });

        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.x = (Math.random() - 0.5) * 60;
        mesh.position.y = (Math.random() - 0.5) * 60;
        mesh.position.z = (Math.random() - 0.5) * 60;

        scene.add(mesh);
        shapes.push(mesh);
    });

    // Mouse interaction
    let mouseX = 0;
    let mouseY = 0;

    document.addEventListener('mousemove', (e) => {
        mouseX = (e.clientX / window.innerWidth) * 2 - 1;
        mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    });

    // Animation loop
    let time = 0;

    function animate() {
        requestAnimationFrame(animate);

        time += 0.001;

        // Rotate particle system
        particleSystem.rotation.y = time * 0.5;
        particleSystem.rotation.x = time * 0.3;

        // Rotate shapes
        shapes.forEach((shape, index) => {
            shape.rotation.x += 0.001 * (index + 1);
            shape.rotation.y += 0.002 * (index + 1);
            shape.rotation.z += 0.001 * (index + 1);
        });

        // Mouse interaction
        camera.position.x += (mouseX * 5 - camera.position.x) * 0.05;
        camera.position.y += (mouseY * 5 - camera.position.y) * 0.05;
        camera.lookAt(scene.position);

        renderer.render(scene, camera);
    }

    animate();

    // Handle window resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        scene.clear();
        renderer.dispose();
    });
})();
