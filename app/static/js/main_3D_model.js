import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';

// Création du renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setClearColor(0xB1B0B0);
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

// Création de la scène
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xB1B0B0);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(-8, 3, 6);

const orbit = new OrbitControls(camera, renderer.domElement);
orbit.enableDamping = true;
orbit.dampingFactor = 0.25;
orbit.enableZoom = true;

// Création du sol
const groundGeometry = new THREE.PlaneGeometry(100, 100);
const groundMaterial = new THREE.ShadowMaterial({ opacity: 0.5 });
const ground = new THREE.Mesh(groundGeometry, groundMaterial);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.01;
ground.receiveShadow = true;
scene.add(ground);

// Lumières
const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
directionalLight.position.set(5, 10, 7);
directionalLight.castShadow = true;
scene.add(directionalLight);

const ambientLight = new THREE.AmbientLight(0x404040);
scene.add(ambientLight);

// Variables globales pour HDRI
const hdriUrls = [];
const hdriPreviews = [];
let defaultHdriIndex = 0;

function createHdriPreviews() {
    const container = document.getElementById('hdr-preview-container');
    hdriPreviews.forEach((previewUrl, index) => {
        const preview = document.createElement('div');
        preview.className = 'hdr-preview';

        const img = document.createElement('img');
        img.src = previewUrl;
        img.alt = `Preview ${index + 1}`;
        preview.appendChild(img);
        container.appendChild(preview);

        preview.addEventListener('click', () => loadHdri(index));
    });

    loadHdri(defaultHdriIndex);
}

function loadHdri(index) {
    const url = hdriUrls[index];
    console.log(`Chargement HDRI depuis URL: ${url}`);
    new RGBELoader().load(
        url,
        (hdrTexture) => {
            hdrTexture.mapping = THREE.EquirectangularReflectionMapping;
            scene.environment = hdrTexture;
        },
        undefined,
        (error) => {
            console.error('Erreur de chargement HDRI:', error);
        }
    );
}

function preloadModel(url) {
    return new Promise((resolve, reject) => {
        const dracoLoader = new DRACOLoader();
        dracoLoader.setDecoderPath('https://www.gstatic.com/draco/v1/decoders/');
        const gltfLoader = new GLTFLoader();
        gltfLoader.setDRACOLoader(dracoLoader);

        console.log(`Loading model from URL: ${url}`);
        
        gltfLoader.load(
            url, 
            (gltf) => {
                console.log('Model loaded successfully');
                resolve(gltf.scene);
            }, 
            undefined, 
            (error) => {
                console.error('Error loading model:', error);
                reject(error);
            }
        );
    });
}

function loadModel(modelId) {
    const modelUrl = `/api/model/${modelId}`;
    preloadModel(modelUrl)
        .then((model) => {
            const existingModel = scene.getObjectByName('model');
            if (existingModel) {
                scene.remove(existingModel);
            }
            model.name = 'model';
            model.traverse((child) => {
                if (child.isMesh) {
                    child.castShadow = true;
                    child.receiveShadow = false;
                    child.material.metalness = 0.4;
                    child.material.roughness = 0.1;
                }
            });

            // Calculate the bounding box
            const boundingBox = new THREE.Box3().setFromObject(model);
            const size = boundingBox.getSize(new THREE.Vector3());
            const maxDimension = Math.max(size.x, size.y, size.z);

            // Define the target size for the bounding box
            const targetSize = 10; // Adjust this value as needed

            // Compute the scale factor
            const scaleFactor = targetSize / maxDimension;

            // Apply the scale
            model.scale.set(scaleFactor, scaleFactor, scaleFactor);

            scene.add(model);

            // Camera and animation setup
            camera.position.set(0, 4, 8);
            new TWEEN.Tween({ angle: 0 })
                .to({ angle: Math.PI * 2 }, 4000)
                .onUpdate(({ angle }) => {
                    const radius = 12;
                    camera.position.x = radius * Math.sin(angle);
                    camera.position.z = radius * Math.cos(angle);
                    camera.lookAt(0, 0, 0);
                })
                .start();

            document.getElementById('progress-container').style.display = 'none';
        })
        .catch((error) => console.error('Erreur de chargement du modèle:', error));
}


function getModelIdFromLocalStorage() {
    const modelId = localStorage.getItem('modelId');
    return modelId;
}



function animate() {
    requestAnimationFrame(animate);
    orbit.update();
    TWEEN.update();
    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

fetch('/api/hdri')
    .then(response => response.json())
    .then(data => {
        data.forEach(hdri => {
            hdriUrls.push(`/api/hdri/${hdri.id}`);
            hdriPreviews.push(hdri.preview_path);
        });
        defaultHdriIndex = 0; // Assignez l'index de l'HDRI par défaut ici
        createHdriPreviews();
    })
    .catch(error => console.error('Erreur lors de la récupération de la liste des HDRIs:', error));

    function loadModelFromLocalStorage() {
        const modelId = getModelIdFromLocalStorage();
        if (modelId) {
            loadModel(scene, composer, skybox, params, modelId);
        } else {
            console.error('Aucun ID de modèle trouvé dans le localStorage');
        }
      }
      
      // Appel de la fonction pour charger le modèle depuis le localStorage
      loadModelFromLocalStorage();
animate();
