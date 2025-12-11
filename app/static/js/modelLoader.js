import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

export async function loadModel(scene, composer, skybox, params, modelId) {
  console.log('Loading model with ID:', modelId); // Log ID

  const dracoLoader = new DRACOLoader();
  dracoLoader.setDecoderPath("https://www.gstatic.com/draco/v1/decoders/");

  const loader = new GLTFLoader();
  loader.setDRACOLoader(dracoLoader);

  const modelUrl = `/api/model/${modelId}`;

  loader.load(
    modelUrl,
    function (gltf) {
      const carModel = gltf.scene;

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
            originalMaterial.needsUpdate = true; // Ensure the material updates
          }

          child.castShadow = true;
          child.receiveShadow = true;

          child.material = originalMaterial; // Use the modified original material
        }
      });

      render();
    },
    undefined,
    function (error) {
      console.error("An error occurred loading the GLTF model:", error);
    }
  );

  function render() {
    if (params.hdriVisible) {
      scene.background = null;

      if (skybox) {
        scene.add(skybox);
      }
    } else {
      scene.background = new THREE.Color(0xbababa); // Set background to gray
      if (skybox) {
        scene.remove(skybox);
      }
    }
    composer.render();
  }
}
