import * as THREE from 'three';
import { initScene } from './sceneSetup.js';
import { loadModel } from './modelLoader.js';
import { setupGUI } from './guiControls.js';
import { loadScene } from './sceneLoader.js';

const scenes = [
  "/static/scene3D/gallery_art.glb",
  "/static/scene3D/open_space.glb",
  "/static/scene3D/premium_space.glb",
  "/static/scene3D/scene1_wood.glb",
];

let currentSceneIndex = 0;
let mainModelGroup;
let sceneGroup;

async function init() {
  try {
    const { scene, camera, renderer, composer, controls, gui, stats, skybox, params, ambientLight, directionalLight, pointLight } = await initScene();

    // Récupérer l'ID du modèle depuis l'URL ou le local storage
    const urlParams = new URLSearchParams(window.location.search);
    let modelId = urlParams.get('model_id');

    if (!modelId) {
      modelId = localStorage.getItem('modelId');
    }

    if (modelId) {
      // Charger le modèle principal
      mainModelGroup = new THREE.Group();
      await loadModel(mainModelGroup, composer, skybox, params, modelId);
      scene.add(mainModelGroup);
    } else {
      console.error('Model ID is not defined in the URL or local storage.');
    }

    // Charger la première scène
    sceneGroup = new THREE.Group();
    await loadScene(sceneGroup, composer, skybox, params, scenes[currentSceneIndex]);
    scene.add(sceneGroup);

    setupGUI(gui, scene, camera, renderer, composer, controls, stats, skybox, params, ambientLight, directionalLight, pointLight);

    document.getElementById('prevButton').addEventListener('click', async () => {
      currentSceneIndex = (currentSceneIndex - 1 + scenes.length) % scenes.length;
      scene.remove(sceneGroup); // Supprimer le groupe de scènes actuel
      sceneGroup = new THREE.Group(); // Créer un nouveau groupe de scènes
      await loadScene(sceneGroup, composer, skybox, params, scenes[currentSceneIndex]);
      scene.add(sceneGroup); // Ajouter le nouveau groupe de scènes à la scène
    });

    document.getElementById('nextButton').addEventListener('click', async () => {
      currentSceneIndex = (currentSceneIndex + 1) % scenes.length;
      scene.remove(sceneGroup); // Supprimer le groupe de scènes actuel
      sceneGroup = new THREE.Group(); // Créer un nouveau groupe de scènes
      await loadScene(sceneGroup, composer, skybox, params, scenes[currentSceneIndex]);
      scene.add(sceneGroup); // Ajouter le nouveau groupe de scènes à la scène
    });

    function animate() {
      stats.begin();
      stats.end();
      requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);
  } catch (error) {
    console.error('Error initializing the scene:', error);
  }
}

init();
