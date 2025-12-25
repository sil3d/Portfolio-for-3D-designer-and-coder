// gui control

import * as THREE from "three";
import { GUI } from "three/addons/libs/lil-gui.module.min.js";

export function setupGUI(gui, scene, camera, renderer, composer, controls, stats, skybox, params, ambientLight, directionalLight, pointLight) {

  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();

  // Toggle Controls Logic
  const toggleBtn = document.getElementById("toggle-controls");
  const guiContainer = document.getElementById("gui-container-custom");
  
  if (toggleBtn && guiContainer) {
    toggleBtn.addEventListener("click", () => {
        guiContainer.classList.toggle("open");
    });
  }

  document.addEventListener("click", onClick);

  // Add shadow-receiving ground plane
  const groundGeometry = new THREE.PlaneGeometry(200, 200);
  const groundMaterial = new THREE.ShadowMaterial({ opacity: 0.5 });
  const groundPlane = new THREE.Mesh(groundGeometry, groundMaterial);
  groundPlane.rotation.x = -Math.PI / 2;
  groundPlane.position.y = -0.01; // Position slightly below 0
  groundPlane.receiveShadow = true;
  scene.add(groundPlane);

  // Track hidden objects
  const hiddenObjects = [];

  function onClick(event) {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);

    // Filter out hidden objects
    const visibleObjects = getVisibleObjects(scene.children);

    const intersects = raycaster.intersectObjects(visibleObjects, true);

    if (intersects.length > 0) {
      const clickedObject = intersects[0].object;

      // Ignore the HDRI or background
      if (
        clickedObject === skybox ||
        clickedObject.parent === skybox ||
        clickedObject.material instanceof THREE.ShadowMaterial
      ) {
        console.warn("Clicked on HDRI or background. No GUI controls applied.");
        return;
      }

      // Supprimer la GUI précédente s'il y en a une
      if (gui) {
        gui.destroy();
        gui = new GUI({ container: document.getElementById("gui-container-custom") }); // Créer une nouvelle instance de GUI dans le conteneur
      }

      if (clickedObject.name === undefined) {
        console.warn("Clicked object has no name:", clickedObject);
        return; // Sortir si le nom est indéfini
      }

      console.log(`Clicked on ${clickedObject.name}`);

      // Ajouter les contrôles GUI pour l'objet sélectionné
      const objectGui = gui.addFolder(clickedObject.name);

      // Check if material exists and has required properties
      if (!clickedObject.material) {
        console.warn("Clicked object has no material");
        return;
      }

      const mat = clickedObject.material;

      // Color control (available on all material types)
      if (mat.color !== undefined) {
        objectGui
          .addColor(mat, "color")
          .name("Couleur")
          .onChange(() => render());
      }

      // Metalness/Roughness only exist on MeshStandardMaterial and MeshPhysicalMaterial
      if (mat.metalness !== undefined) {
        objectGui
          .add(mat, "metalness", 0, 1)
          .name("Métal")
          .onChange(() => render());
      } else {
        console.log(`Material type "${mat.type}" doesn't have metalness property`);
      }

      if (mat.roughness !== undefined) {
        objectGui
          .add(mat, "roughness", 0, 1)
          .name("Rugosité")
          .onChange(() => render());
      } else {
        console.log(`Material type "${mat.type}" doesn't have roughness property`);
      }

      // Opacity (available on materials with transparency)
      if (mat.opacity !== undefined) {
        objectGui
          .add(mat, "opacity", 0, 1)
          .name("Opacité")
          .onChange((value) => {
            mat.transparent = value < 1;
            mat.needsUpdate = true;
            render();
          });
      }

      // Ajouter la possibilité de cacher ou montrer l'objet
      objectGui
        .add({ visible: clickedObject.visible }, "visible")
        .name("Visible")
        .onChange((value) => {
          clickedObject.visible = value;
          if (value === false) {
            hiddenObjects.push(clickedObject);
          } else {
            const index = hiddenObjects.indexOf(clickedObject);
            if (index > -1) {
              hiddenObjects.splice(index, 1);
            }
          }
          updateHiddenObjectsGUI();
          render();
        });

      // Add rotation controls
      objectGui
        .add(clickedObject.rotation, "x", 0, Math.PI * 2)
        .name("Rotation X")
        .onChange(() => {
          clickedObject.updateMatrixWorld();
          render();
        });

      objectGui
        .add(clickedObject.rotation, "y", 0, Math.PI * 2)
        .name("Rotation Y")
        .onChange(() => {
          clickedObject.updateMatrixWorld();
          render();
        });

      objectGui
        .add(clickedObject.rotation, "z", 0, Math.PI * 2)
        .name("Rotation Z")
        .onChange(() => {
          clickedObject.updateMatrixWorld();
          render();
        });

      // Créer une fenêtre GUI pour les objets cachés
      updateHiddenObjectsGUI();

      // GUI Controls
      gui
        .add(params, "hdriVisible")
        .name("HDRI Visible")
        .onChange(() => render());
      gui
        .add(params, "exposure", 0.1, 3.0)
        .name("Exposure")
        .onChange((value) => {
          renderer.toneMappingExposure = value;
          render();
        });
      gui
        .add(params, "shadowIntensity", 0, 40)
        .name("Shadow Intensity")
        .onChange((value) => {
          scene.traverse((object) => {
            if (object.isMesh) {
              object.receiveShadow = value > 0;
            }
          });
          render();
        });

      gui
        .add(params, "fov", 10, 100)
        .name("Field of View")
        .onChange((value) => {
          camera.fov = value;
          camera.updateProjectionMatrix();
          render();
        });
      gui
        .add(params, "ambientLightIntensity", 0, 40)
        .name("Ambient Light Intensity")
        .onChange((value) => {
          ambientLight.intensity = value;
          render();
        });
        gui.domElement.addEventListener('click', function(event) {
          event.stopPropagation();
        });
        

      // Controls for Directional Light Position
      const directionalLightFolder = gui.addFolder("Directional Light Position");
      directionalLightFolder
        .add(directionalLight.position, "x", -100, 150)
        .name("Position X")
        .onChange(() => render());
      directionalLightFolder
        .add(directionalLight.position, "y", -100, 150)
        .name("Position Y")
        .onChange(() => render());
      directionalLightFolder
        .add(directionalLight.position, "z", -100, 150)
        .name("Position Z")
        .onChange(() => render());

      gui
        .add(params, "pointLightIntensity", 0, 20)
        .name("Point Light Intensity")
        .onChange((value) => {
          pointLight.intensity = value;
          render();
        });
        gui
        .add(params, "directionalLightIntensity", 0, 90)
        .name("Directional Light Intensity")
        .onChange((value) => {
          directionalLight.intensity = value;
          render();
        });

      // Add controls for light color if needed
      gui
        .addColor(directionalLight, "color")
        .name("Directional Light Color")
        .onChange(() => render());
    }
  }

  function getVisibleObjects(objects) {
    const visibleObjects = [];
    objects.forEach((object) => {
      if (object.visible) {
        visibleObjects.push(object);
      }
      if (object.children.length > 0) {
        visibleObjects.push(...getVisibleObjects(object.children));
      }
    });
    return visibleObjects;
  }

  function updateHiddenObjectsGUI() {
    // Supprimer le dossier "Objets Cachés" s'il existe déjà
    const hiddenObjectsGui = gui.folders.find(
      (folder) => folder.title === "Objets Cachés"
    );
    if (hiddenObjectsGui) {
      gui.removeFolder(hiddenObjectsGui);
    }

    // Créer un nouveau dossier "Objets Cachés"
    const newHiddenObjectsGui = gui.addFolder("Objets Cachés");

    // Ajouter une case à cocher pour chaque objet caché
    hiddenObjects.forEach((obj) => {
      newHiddenObjectsGui
        .add({ visible: false }, "visible")
        .name(obj.name)
        .onChange((value) => {
          if (value) {
            obj.visible = true;
            const index = hiddenObjects.indexOf(obj);
            if (index > -1) {
              hiddenObjects.splice(index, 1);
            }
            updateHiddenObjectsGUI();
          }
          render();
        });
    });
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
}
