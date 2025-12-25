/**
 * WEB WORKER - MODEL LOADER
 * 
 * Loads 3D models in a separate thread to prevent UI blocking
 * Uses transferable objects for zero-copy data passing
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

// Initialize loaders in worker context
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("https://unpkg.com/three@v0.163.0/examples/jsm/libs/draco/");

const loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);
loader.setMeshoptDecoder(MeshoptDecoder);

// Message handler
self.onmessage = async function(e) {
  const { type, url, modelId } = e.data;
  
  if (type === 'LOAD_MODEL') {
    console.log(`[Worker] Loading model ${modelId} on background thread...`);
    
    try {
      const gltf = await new Promise((resolve, reject) => {
        loader.load(
          url,
          (loadedGltf) => {
            console.log(`[Worker] ✓ Model ${modelId} loaded in worker`);
            resolve(loadedGltf);
          },
          (progress) => {
            if (progress.lengthComputable) {
              const percent = (progress.loaded / progress.total * 100).toFixed(1);
              
              // Send progress updates to main thread
              self.postMessage({
                type: 'PROGRESS',
                modelId,
                percent,
                loaded: progress.loaded,
                total: progress.total
              });
            }
          },
          reject
        );
      });
      
      // Serialize GLTF data (can't transfer Three.js objects directly)
      const serializedData = serializeGLTF(gltf);
      
      // Send back to main thread
      self.postMessage({
        type: 'MODEL_LOADED',
        modelId,
        data: serializedData
      });
      
    } catch (error) {
      self.postMessage({
        type: 'ERROR',
        modelId,
        error: error.message
      });
    }
  }
};

/**
 * Serialize GLTF for transfer between threads
 */
function serializeGLTF(gltf) {
  const serialized = {
    geometries: [],
    materials: [],
    meshes: [],
    scene: serializeObject(gltf.scene)
  };
  
  return serialized;
}

function serializeObject(obj) {
  const data = {
    type: obj.type,
    name: obj.name,
    position: obj.position.toArray(),
    rotation: obj.rotation.toArray(),
    scale: obj.scale.toArray(),
    children: []
  };
  
  if (obj.isMesh) {
    // Store geometry and material indices
    data.geometryData = serializeGeometry(obj.geometry);
    data.materialData = serializeMaterial(obj.material);
  }
  
  obj.children.forEach(child => {
    data.children.push(serializeObject(child));
  });
  
  return data;
}

function serializeGeometry(geometry) {
  const attributes = {};
  
  for (const key in geometry.attributes) {
    attributes[key] = {
      array: geometry.attributes[key].array,
      itemSize: geometry.attributes[key].itemSize,
      normalized: geometry.attributes[key].normalized
    };
  }
  
  return {
    attributes,
    index: geometry.index ? geometry.index.array : null
  };
}

function serializeMaterial(material) {
  return {
    type: material.type,
    color: material.color?.getHex(),
    metalness: material.metalness,
    roughness: material.roughness,
    transparent: material.transparent,
    opacity: material.opacity
  };
}

console.log('[Worker] Model loader worker initialized');
