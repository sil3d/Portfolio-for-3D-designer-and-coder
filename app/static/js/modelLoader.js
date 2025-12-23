import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

// Model cache for faster subsequent loads
const modelCache = new Map();
const loadingPromises = new Map();

// Initialize loaders once (reuse across loads)
// Initialize loaders once (reuse across loads)
const dracoLoader = new DRACOLoader();
// Use the unpkg path matching the Three.js version (v0.163.0) to ensure compatibility
dracoLoader.setDecoderPath("https://unpkg.com/three@v0.163.0/examples/jsm/libs/draco/");
const loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);

/**
 * Preload a model without adding it to the scene
 * Call this early to start downloading models in the background
 */
export async function preloadModel(modelId) {
  // Add timestamp to force fresh download (bypass corrupted cache)
  const modelUrl = `/api/model/${modelId}?v=${Date.now()}`;
  
  // If already cached or loading, skip
  if (modelCache.has(modelUrl) || loadingPromises.has(modelUrl)) {
    return;
  }
  
  console.log(`Preloading model ${modelId}...`);
  
  const loadPromise = new Promise((resolve, reject) => {
    loader.load(
      modelUrl,
      (gltf) => {
        modelCache.set(modelUrl, gltf);
        loadingPromises.delete(modelUrl);
        console.log(`Model ${modelId} preloaded and cached`);
        resolve(gltf);
      },
      (progress) => {
        if (progress.lengthComputable) {
          const percent = (progress.loaded / progress.total * 100).toFixed(1);
          console.log(`Preloading model ${modelId}: ${percent}%`);
        }
      },
      (error) => {
        loadingPromises.delete(modelUrl);
        console.error(`Failed to preload model ${modelId}:`, error);
        reject(error);
      }
    );
  });
  
  loadingPromises.set(modelUrl, loadPromise);
  return loadPromise;
}

export async function loadModel(scene, composer, skybox, params, modelId) {
  console.log('Loading model with ID:', modelId);

  // Add timestamp to force fresh download (bypass corrupted cache)
  const modelUrl = `/api/model/${modelId}?v=${Date.now()}`;

  // Check if model is in cache
  let gltf = modelCache.get(modelUrl);
  
  if (!gltf) {
    // Check if already loading
    if (loadingPromises.has(modelUrl)) {
      console.log('Waiting for model to finish loading...');
      gltf = await loadingPromises.get(modelUrl);
    } else {
      // Load new model
      gltf = await new Promise((resolve, reject) => {
        // Show loading indicator
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) loadingDiv.style.display = 'block';
        
        loader.load(
          modelUrl,
          (loadedGltf) => {
            modelCache.set(modelUrl, loadedGltf);
            if (loadingDiv) loadingDiv.style.display = 'none';
            resolve(loadedGltf);
          },
          (progress) => {
            if (progress.lengthComputable) {
              const percent = (progress.loaded / progress.total * 100).toFixed(1);
              console.log(`Loading model: ${percent}%`);
              // Update loading indicator if exists
              const progressBar = document.getElementById('loading-progress');
              if (progressBar) progressBar.style.width = `${percent}%`;
            }
          },
          (error) => {
            if (loadingDiv) loadingDiv.style.display = 'none';
            console.error("An error occurred loading the GLTF model:", error);
            reject(error);
          }
        );
      });
    }
  } else {
    console.log('Using cached model');
  }

  // Clone the scene from cache (so we can reuse the cached model)
  const carModel = gltf.scene.clone();

  if (!carModel) {
    console.error("GLTF model failed to load.");
    return;
  }

  const boundingBox = new THREE.Box3().setFromObject(carModel);
  const size = boundingBox.getSize(new THREE.Vector3());
  const maxDimension = Math.max(size.x, size.y, size.z);

  const targetSize = 10;
  const scaleFactor = targetSize / maxDimension;

  carModel.scale.set(scaleFactor, scaleFactor, scaleFactor);
  carModel.rotation.y = Math.PI;
  scene.add(carModel);

  carModel.traverse((child) => {
    if (child.isMesh) {
      // Clone material to avoid sharing state between instances
      child.material = child.material.clone();
      const originalMaterial = child.material;

      // Log material information
      console.log(`%cMesh name: ${child.name}`);

      if (
        originalMaterial.emissive &&
        !originalMaterial.emissive.equals(new THREE.Color(0, 0, 0))
      ) {
        console.log(
          `%cMaterial '${
            child.name
          }' has emissive color: ${originalMaterial.emissive.getHexString()},`,
          "color: green; font-weight: bold;"
        );
      } else {
        console.log(
          `%cMaterial '${child.name}' does not have emissive color.`,
          "color: red; font-weight: bold;"
        );
      }

      // Apply default opacity of 0.9 if material has transparency
      if (originalMaterial.transparent) {
        originalMaterial.opacity = 0.6;
        originalMaterial.needsUpdate = true;
      }

      child.castShadow = true;
      child.receiveShadow = true;
    }
  });

  render();

  function render() {
    if (params.hdriVisible) {
      scene.background = null;

      if (skybox) {
        scene.add(skybox);
      }
    } else {
      scene.background = new THREE.Color(0xbababa);
      if (skybox) {
        scene.remove(skybox);
      }
    }
    composer.render();
  }
}

/**
 * Clear the model cache (useful for memory management)
 */
export function clearModelCache() {
  modelCache.clear();
  console.log('Model cache cleared');
}
