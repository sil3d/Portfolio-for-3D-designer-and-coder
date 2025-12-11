import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GroundedSkybox } from "three/addons/objects/GroundedSkybox.js";
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { GUI } from "three/addons/libs/lil-gui.module.min.js";
import Stats from 'three/addons/libs/stats.module.js';

const params = {
  height: 15,
  radius: 100,
  hdriVisible: true,
  exposure: 0.15,
  shadowIntensity: 10,
  fov: 50,
  ambientLightIntensity: 5,
  directionalLightIntensity: 30,
  pointLightIntensity:  1,
};

export async function initScene() {
  const gui = new GUI({ container: document.getElementById("gui-container-custom") });

  const camera = new THREE.PerspectiveCamera(
    params.fov,
    window.innerWidth / window.innerHeight,
    1,
    1000
  );
   

  let startCameraPosition = new THREE.Vector3();
  let endCameraPosition = new THREE.Vector3();
  let startCameraFov = 50; // Valeur initiale du FOV
  let endCameraFov = params.fov; // Valeur finale du FOV
  let animationStartTime = null;
  const animationDuration = 9000; // Durée de l'animation en millisecondes
  
 
  function updateCameraDistance() {
    const isMobile = window.innerWidth <= 768; // Ajustez cette valeur selon vos besoins
  
    if (isMobile) {
      endCameraPosition.set(-7, 4, -10);
      endCameraFov = 87;
      
    } else {
      endCameraPosition.set(-7, 4, -8);
      endCameraFov = params.fov;
    }
  
    // Animation de la caméra
    animationStartTime = performance.now();
    startCameraPosition.copy(camera.position);
    startCameraFov = camera.fov;
  
    function animateCamera(time) {
      if (!animationStartTime) animationStartTime = time;
      const elapsedTime = time - animationStartTime;
      const t = Math.min(elapsedTime / animationDuration, 1); // Calcul du progrès de l'animation
  
      // Interpolation des valeurs de la caméra
      camera.position.lerpVectors(startCameraPosition, endCameraPosition, t);
      camera.fov = THREE.MathUtils.lerp(startCameraFov, endCameraFov, t);
      camera.updateProjectionMatrix();
  
      // Mettre à jour le contrôle de la caméra
      controls.update();
  
      // Continue l'animation
      if (t < 1) {
        requestAnimationFrame(animateCamera);
      } else {
        // Finaliser les paramètres de la caméra
        camera.position.copy(endCameraPosition);
        camera.fov = endCameraFov;
        camera.updateProjectionMatrix();
        controls.update();
      }
  
      render();
    }
  
    requestAnimationFrame(animateCamera);
  }
  
  const scene = new THREE.Scene();

  // Load and apply HDRI
  const hdrLoader = new RGBELoader();
  let envMap = null;
  let skybox = null;

  async function loadHDRI(hdriId) {
    const response = await fetch(`/api/hdri/${hdriId}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    envMap = await hdrLoader.loadAsync(url);
    envMap.mapping = THREE.EquirectangularReflectionMapping;

    if (skybox) {
      scene.remove(skybox);
    }

    skybox = new GroundedSkybox(envMap, params.height, params.radius);
    skybox.position.y = params.height - 0.01;
    scene.environment = envMap;
    scene.add(skybox);
    render();
  }

  const renderer = new THREE.WebGLRenderer({ antialias: false });
  renderer.setPixelRatio(window.devicePixelRatio * 0.99); //reduce this value to get more fps or delete or get hd quality
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = params.exposure;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputEncoding = THREE.sRGBEncoding;

  // Create a render pass
  const renderPass = new RenderPass(scene, camera);

  // Create a bloom pass
  const bloomPass = new UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    0.2,
    0.2,
    0.2
  );
  bloomPass.threshold = 0.1;
  bloomPass.strength = 0.05;
  bloomPass.radius = 0;

  // Create an effect composer
  const composer = new EffectComposer(renderer);
  composer.addPass(renderPass);
  composer.addPass(bloomPass);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.addEventListener("change", render);
  controls.target.set(0, 2, 0);
  controls.maxPolarAngle = THREE.MathUtils.degToRad(90);
  controls.maxDistance = 80;
  controls.minDistance = 2;
  controls.enablePan = true;
  controls.update();
  updateCameraDistance(); // Appel de la fonction pour ajuster la distance de la caméra

  document.getElementById("container").appendChild(renderer.domElement);
  // GUI is already appended via constructor container option
  document.getElementById("toggle-hdri").addEventListener("click", function () {
    params.hdriVisible = !params.hdriVisible;
    render();
  });

  window.addEventListener("resize", onWindowResize);

  function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    updateCameraDistance(); // Réajuster la caméra lors du redimensionnement
    render();
  }

  function render() {
    // Update background based on hdriVisible parameter
    if (params.hdriVisible) {
      scene.background = null;
      if (skybox) {
        scene.add(skybox);
      }
    } else {
      scene.background = new THREE.Color(0xbababa); // Set background to white
      if (skybox) {
        scene.remove(skybox);
      }
    }

    // Render the scene using the effect composer
    composer.render();
  }

  const ambientLight = new THREE.AmbientLight(
    0xffffff,
    params.ambientLightIntensity
  );
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(
    0xffffff,
    params.directionalLightIntensity
  );
  directionalLight.position.set(10, 20, 10);
  directionalLight.castShadow = true;
  // Shadow settings for the directional light
  directionalLight.shadow.mapSize.width = 2048;
  directionalLight.shadow.mapSize.height = 2048;
  directionalLight.shadow.camera.near = 0.5;
  directionalLight.shadow.camera.far = 500;
  directionalLight.shadow.camera.left = -50;
  directionalLight.shadow.camera.right = 50;
  directionalLight.shadow.camera.top = 50;
  directionalLight.shadow.camera.bottom = -50;

  scene.add(directionalLight);

  const pointLight = new THREE.PointLight(
    0xffffff,
    params.pointLightIntensity,
    100
  );
  pointLight.position.set(-10, 10, -10);
  scene.add(pointLight);

  const stats = new Stats();
  stats.showPanel(0);
  document.getElementById("stats").appendChild(stats.dom);

  // Load HDRI list and display previews
  async function loadHDRIList() {
    const response = await fetch('/api/hdri');
    const data = await response.json();
    const hdriList = data.hdri_list;
    const defaultHdriId = data.default_hdri_id;

    const hdrPreviewContainer = document.getElementById('hdr-preview-container');
    hdrPreviewContainer.innerHTML = ''; // Clear previous previews

    hdriList.forEach(hdri => {
      const img = document.createElement('img');
      img.src = hdri.preview_path;
      img.alt = `HDRI ${hdri.id}`;
      img.addEventListener('click', () => loadHDRI(hdri.id));
      hdrPreviewContainer.appendChild(img);
    });

    if (defaultHdriId) {
      await loadHDRI(defaultHdriId);
    }
  }

  await loadHDRIList();

  return { scene, camera, renderer, composer, controls, gui, stats, skybox, params, ambientLight, directionalLight, pointLight };
}
