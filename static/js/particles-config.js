/**
 * tsParticles Configuration for Neural Network / Constellation Effect
 * Style: Clean, Minimalist, Tech
 */
const particlesConfig = {
    fullScreen: {
        enable: true,
        zIndex: -1 // Behind everything
    },
    background: {
        color: {
            value: "transparent", // Transparent background
        },
    },
    fpsLimit: 120,
    interactivity: {
        events: {
            onHover: {
                enable: true,
                mode: "grab", // Connect line to mouse
            },
            onClick: {
                enable: true,
                mode: "push", // Add particles on click
            },
            resize: true,
        },
        modes: {
            grab: {
                distance: 140,
                links: {
                    opacity: 0.5,
                },
            },
            push: {
                quantity: 4,
            },
        },
    },
    particles: {
        color: {
            value: "#666666", // Dark gray particles
        },
        links: {
            color: "#aaaaaa", // Light gray links
            distance: 150,
            enable: true,
            opacity: 0.2, // Subtle links
            width: 1,
        },
        move: {
            direction: "none",
            enable: true,
            outModes: {
                default: "bounce",
            },
            random: false,
            speed: 1, // Slow movement
            straight: false,
        },
        number: {
            density: {
                enable: true,
                area: 800,
            },
            value: 80, // Moderate number of particles
        },
        opacity: {
            value: 0.5,
        },
        shape: {
            type: "circle",
        },
        size: {
            value: { min: 1, max: 3 },
        },
    },
    detectRetina: true,
};
