import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";

export async function loadScene(scene, composer, skybox, params, scenePath) {
  const dracoLoader = new DRACOLoader();
  dracoLoader.setDecoderPath("https://www.gstatic.com/draco/v1/decoders/");

  const loader = new GLTFLoader();
  loader.setDRACOLoader(dracoLoader);

  loader.load(
    scenePath,
    function (gltf) {
      const sceneModel = gltf.scene;

      if (!sceneModel) {
        console.error("GLTF scene failed to load.");
        return;
      }

      const boundingBox = new THREE.Box3().setFromObject(sceneModel);
      const size = boundingBox.getSize(new THREE.Vector3());
      const maxDimension = Math.max(size.x, size.y, size.z);

      const targetSize = 30;
      const scaleFactor = targetSize / maxDimension;

      sceneModel.scale.set(scaleFactor, scaleFactor, scaleFactor);
      sceneModel.rotation.y = Math.PI;

      // Ajouter la scène 3D à un groupe distinct
      const sceneGroup = new THREE.Group();
      sceneGroup.add(sceneModel);
      scene.add(sceneGroup);

      sceneModel.traverse((child) => {
        if (child.isMesh) {
          const originalMaterial = child.material;

          console.log(`%cMesh name: ${child.name}`);

          if (
            originalMaterial.emissive &&
            !originalMaterial.emissive.equals(new THREE.Color(0, 0, 0))
          ) {
            console.log(
              `%cMaterial '${
                child.name
              }' has emissive color: ${originalMaterial.emissive.getHexString()}`,
              "color: green; font-weight: bold;"
            );
          } else {
            console.log(
              `%cMaterial '${child.name}' does not have emissive color.`,
              "color: red; font-weight: bold;"
            );
          }

          if (originalMaterial.transparent) {
            originalMaterial.opacity = 0.5;
          }
          if (originalMaterial.roughness) {
            originalMaterial.roughness = 0.05;
          }
          if (originalMaterial.metalness) {
            originalMaterial.metalness = 0.8;
          }

          // Si le matériau a une composante émissive
          if (originalMaterial.emissive && !originalMaterial.emissive.equals(new THREE.Color(0, 0, 0))) {
            originalMaterial.emissiveIntensity = 300;
          }

          child.castShadow = true;
          child.receiveShadow = true;

          child.material = originalMaterial;
        }
      });

      render();
    },
    undefined,
    function (error) {
      console.error("An error occurred loading the GLTF scene:", error);
    }
  );

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
