import * as THREE from 'three';
import { initScene } from './sceneSetup.js';
import { loadModel } from './ultraOptimizedLoader.js'; // Ultra-optimized: KTX2 + Multi-threading + 3-stage LOD
import { setupGUI } from './guiControls.js';
import { loadScene } from './sceneLoader.js';

// Scenes will be loaded dynamically
let scenes = [];
let currentSceneIndex = 0;
let mainModelGroup;
let sceneGroup;

// Check if model has been cached before (browser cache or visited before)
function isModelCached(modelId) {
  const cacheKey = `model_cached_${modelId}`;
  return localStorage.getItem(cacheKey) === 'true';
}

// Mark model as cached after successful load
function markModelAsCached(modelId) {
  const cacheKey = `model_cached_${modelId}`;
  localStorage.setItem(cacheKey, 'true');
}

// Show/hide first load warning
function showFirstLoadWarning(show) {
  const warning = document.getElementById('first-load-warning');
  if (warning) {
    warning.style.display = show ? 'flex' : 'none';
  }
}

// Update loading status text
function updateLoadingStatus(text) {
  const status = document.getElementById('loading-status');
  if (status) {
    status.textContent = text;
  }
}

async function loadScenesList() {
  try {
    const response = await fetch('/api/scenes');
    if (response.ok) {
      scenes = await response.json();
      console.log("Loaded scenes:", scenes);
    } else {
      console.error("Failed to load scenes list, falling back to default.");
      scenes = ["/static/scene3D/gallery_art.glb"]; // Fallback
    }
  } catch (error) {
    console.error("Error loading scenes:", error);
    scenes = ["/static/scene3D/gallery_art.glb"]; // Fallback
  }
}

async function init() {
  try {
    // Get model ID early to check cache status
    // Get model ID from injected global variable (reliable)
    const modelId = window.CURRENT_MODEL_ID;

    // Load scenes list dynamically
    await loadScenesList();

    // Show appropriate loading UI based on cache status
    const isCached = modelId ? isModelCached(modelId) : false;
    
    if (modelId && !isCached) {
      // First time loading - show warning
      showFirstLoadWarning(true);
      updateLoadingStatus('Initializing 3D engine...');
    } else {
      // Cached - show simple loader
      const loader = document.getElementById('loading-indicator');
      if (loader) loader.style.display = 'block';
    }

    // Initialize scene
    if (!isCached) updateLoadingStatus('Setting up scene...');
    const { scene, camera, renderer, composer, controls, gui, stats, skybox, params, ambientLight, directionalLight, pointLight, updateCameraDistance } = await initScene();

    if (modelId) {
      // Load main model
      if (!isCached) updateLoadingStatus('Downloading 3D model... This may take a moment.');
      mainModelGroup = new THREE.Group();
      await loadModel(mainModelGroup, composer, skybox, params, modelId);
      scene.add(mainModelGroup);
      
      // Mark as cached for next visit
      markModelAsCached(modelId);
      
      // Hide loading UI
      // Hide loading UI
      showFirstLoadWarning(false);
      const loader = document.getElementById('loading-indicator');
      if (loader) loader.style.display = 'none';
      
      // TRIGGER ENTER ANIMATION NOW
      console.log("Model loaded. Triggering camera enter animation.");
      updateCameraDistance();
    } else {
      console.error('Model ID is not defined in the URL or local storage.');
      showFirstLoadWarning(false);
    }

    // Load first scene
    sceneGroup = new THREE.Group();
    await loadScene(sceneGroup, composer, skybox, params, scenes[currentSceneIndex]);
    scene.add(sceneGroup);

    setupGUI(gui, scene, camera, renderer, composer, controls, stats, skybox, params, ambientLight, directionalLight, pointLight);

    document.getElementById('prevButton').addEventListener('click', async () => {
      currentSceneIndex = (currentSceneIndex - 1 + scenes.length) % scenes.length;
      scene.remove(sceneGroup);
      sceneGroup = new THREE.Group();
      await loadScene(sceneGroup, composer, skybox, params, scenes[currentSceneIndex]);
      scene.add(sceneGroup);
    });

    document.getElementById('nextButton').addEventListener('click', async () => {
      currentSceneIndex = (currentSceneIndex + 1) % scenes.length;
      scene.remove(sceneGroup);
      sceneGroup = new THREE.Group();
      await loadScene(sceneGroup, composer, skybox, params, scenes[currentSceneIndex]);
      scene.add(sceneGroup);
    });

    function animate() {
      stats.begin();
      stats.end();
      requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);
  } catch (error) {
    console.error('Error initializing the scene:', error);
    showFirstLoadWarning(false);
    const loader = document.getElementById('loading-indicator');
    if (loader) loader.style.display = 'none';
  }
}

init();
