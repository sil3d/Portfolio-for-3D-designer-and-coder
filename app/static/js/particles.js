/**
 * Custom Vanilla JS Particle Network
 * Replicates particles.js features:
 * 1. Particles with "cyan" theme.
 * 2. Connected lines (Network effect).
 * 3. Mouse Repulsion ("Hole" effect).
 */

(function() {
    // Setup Canvas
    const container = document.getElementById('particles-js');
    // Ensure container exists
    if (!container) return;

    // Create Canvas Element
    const canvas = document.createElement('canvas');
    canvas.style.display = 'block';
    canvas.style.position = 'absolute';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    
    // Configuration
    const config = {
        amount: 300,              // Number of particles (desktop)
        color: '#fe4800ff',        // Cyan
        lineColor: '0, 142, 255',// Cyan RGB for rgba()
        radius: 3,
        speed: 1,
        linkDistance: 150,
        repulseRadius: 200,      // Size of the "hole"
        repulseStrength: 50      // How hard it pushes
    };

    // Mouse State (Window level detection)
    const mouse = { x: null, y: null };

    // Resize Handling
    function resize() {
        width = canvas.width = container.offsetWidth;
        height = canvas.height = container.offsetHeight;
        initParticles();
    }

    // Particle Class
    class Particle {
        constructor() {
            this.x = Math.random() * width;
            this.y = Math.random() * height;
            this.vx = (Math.random() - 0.5) * config.speed;
            this.vy = (Math.random() - 0.5) * config.speed;
            this.size = Math.random() * 2 + 1;
        }

        update() {
            // Mouse Repulsion Logic
            if (mouse.x != null) {
                let dx = this.x - mouse.x;
                let dy = this.y - mouse.y;
                let distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < config.repulseRadius) {
                    const forceDirectionX = dx / distance;
                    const forceDirectionY = dy / distance;
                    const force = (config.repulseRadius - distance) / config.repulseRadius;
                    const directionX = forceDirectionX * force * config.repulseStrength;
                    const directionY = forceDirectionY * force * config.repulseStrength;

                    this.vx += directionX * 0.1; // Gentle push to velocity
                    this.vy += directionY * 0.1;
                }
            }

            // Move
            this.x += this.vx;
            this.y += this.vy;

            // Friction (to stop them from accelerating forever due to repulsion)
            // But keep a minimum speed
            const speed = Math.sqrt(this.vx*this.vx + this.vy*this.vy);
            if (speed > config.speed * 2) {
                this.vx *= 0.95;
                this.vy *= 0.95;
            }

            // Boundary Check (Bounce)
            if (this.x < 0 || this.x > width) this.vx *= -1;
            if (this.y < 0 || this.y > height) this.vy *= -1;
        }

        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = config.color;
            ctx.fill();
        }
    }

    function initParticles() {
        particles = [];
        let nb = config.amount;
        if (window.innerWidth < 768) nb = Math.floor(nb / 4); // Even less on mobile (1/4 of desktop)

        for (let i = 0; i < nb; i++) {
            particles.push(new Particle());
        }
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);

        for (let i = 0; i < particles.length; i++) {
            let p1 = particles[i];
            p1.update();
            p1.draw();

            // Connections
            for (let j = i + 1; j < particles.length; j++) {
                let p2 = particles[j];
                let dx = p1.x - p2.x;
                let dy = p1.y - p2.y;
                let dist = Math.sqrt(dx*dx + dy*dy);

                if (dist < config.linkDistance) {
                    ctx.beginPath();
                    // Opacity based on distance
                    let opacity = 1 - (dist / config.linkDistance);
                    ctx.strokeStyle = `rgba(${config.lineColor}, ${opacity})`;
                    ctx.lineWidth = 1;
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }

    // Event Listeners
    window.addEventListener('resize', resize);
    
    // Global mouse tracking
    window.addEventListener('mousemove', function(e) {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    window.addEventListener('mouseleave', function() {
        mouse.x = null;
        mouse.y = null;
    });

    // Start
    resize();
    animate();

})();
