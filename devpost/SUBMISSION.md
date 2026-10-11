# Devpost submission copy: Project D.O.T.

Paste each section into the matching Devpost field. The equation is written in plain text and as LaTeX.

## Project story

### Inspiration
As humanity sets its sights on Mars and beyond, the logistical tether to Earth becomes impossible to maintain. We realized that for interplanetary civilization to thrive, we can't just bring our food — we must bring our ecosystems. Project D.O.T. (Dynamic Orbital Terra-synthesis) was inspired by the need for a closed-loop, self-sustaining agriculture system capable of generating and maintaining nutrient-dense soil in microgravity environments.

### What it does
Project D.O.T. is an autonomous, IoT-driven biodome system that synthesizes artificial soil from organic waste and regulates environmental parameters for optimal crop yield in space. It uses a machine-learning backend to constantly monitor soil health, hydration levels, and ambient radiation, dynamically adjusting the biome to ensure plant survivability.

### How we built it
The hardware prototype was built using modular acrylic pods, rigged with Arduino-controlled environmental sensors (humidity, NPK levels, temperature, and pH).

On the software side, we developed a Python-based backend with a predictive model that calculates the rate of nutrient degradation and autonomous replenishment. We used the following decay-replenishment model to balance the soil's nitrogen levels:

`dN/dt = α·I(t) − β·N(t) − γ·U(t)`  ( $\frac{dN}{dt} = \alpha I(t) - \beta N(t) - \gamma U(t)$ )

Where:
- N(t) = current nutrient concentration in the orbital soil
- I(t) = automated nutrient injection rate
- U(t) = biomass uptake rate by the crops
- α, β, γ = conversion, decay and absorption coefficients, calibrated from telemetry (instrumental-variable fit)

The frontend is a React-based dashboard that lets astronauts (or mission control) visualize the biome's health in real time, backed by a Flask API. Source: https://github.com/zainkhan1994/project-dot-orbital-soil

### Challenges we ran into
Simulating microgravity fluid dynamics was incredibly difficult. Watering soil in space often leads to water pooling or floating away, which causes root rot or dehydration. We had to design and 3D-print a custom capillary-action drip system that forces water directly into the root mesh, bypassing the need for gravity. Additionally, calibrating the NPK sensors to avoid false positives from our synthetic fertilizer mix took many hours of troubleshooting.

### What we learned
We learned how to integrate hardware sensors with a predictive algorithm and gained massive respect for astrobotanists. We also learned that handling state management in React is remarkably similar to managing the equilibrium of a delicate biome. On the modelling side, noisy measurements bias a naive least-squares fit, and a closed control loop needs a small probing signal so the coefficients stay identifiable.

### What's next for Project D.O.T.
We plan to scale our single-pod prototype into a multi-pod network, introducing mycelium networks into our artificial soil to better break down complex organic waste. We are also aiming to open-source our telemetry dashboard for other space-agri researchers.

## Built with
`python`, `react`, `node.js`, `arduino`, `flask`, `numpy`, `vite`, `machine-learning`, `iot`, `c++`, `hardware`, `3d-printing`, `github-pages`

> The original draft also listed `tensorflow`, `raspberry-pi`, `pandas`, `fusion360` and `aws`. This repo contains an optional TensorFlow script that was not run, and no pandas, Fusion 360 or AWS code. Keep those tags only if they are true for your full project.

## Try it out links

- GitHub repository (source code): https://github.com/zainkhan1994/project-dot-orbital-soil
- Live telemetry dashboard demo: http://organize-with.me/project-dot-orbital-soil/ (in-browser simulation)
- Interactive 3D hardware model: **TODO: add your Sketchfab link**

## Project media

Image gallery (3:2 ratio, max 5 MB each): hero shot of the assembled pod, the dashboard screenshot (`.github/assets/hero.png`), the team wiring/coding, a close-up of the sensors in the soil.

Video demo link: **TODO: add your YouTube or Vimeo link** (under 3 minutes: the problem, hardware and software working, the code and the math).
