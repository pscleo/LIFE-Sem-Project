# Three freely coasting spacecraft near JWST

## Run

1. Extract this folder anywhere on your Windows computer. Do not run from inside the ZIP.
2. Keep `simple_jwst_formation.py` and the supplied `.e` file together.
3. Use the same Python environment in which the previous project's code worked.
4. Run `python simple_jwst_formation.py`, or open the file in VS Code and run its `# %%` sections in order.

Requirements: STK 13 Desktop, its `agi.stk13` Python API, Astrogator, and Analysis Workbench. There are no imports from the previous project's helper files and no additional third-party Python packages to install.

The script opens a new STK application, so it does not close an existing scenario. STK remains open when the script finishes. Each run saves a new scenario folder beside the script. Open the `.sc` file in that folder to return to the saved scenario; keep its companion files together. Save again in STK after changing the view if you want to retain those changes.

## What is being simulated?

The script reads the original JWST ephemeris once, at 6 October 2022, 07:00:00 UTC. This is the Base departure epoch used in the original `octahedron-constellation.py`. It creates three spacecraft with these initial positions relative to Base:

| Spacecraft | X [m] | Y [m] | Z [m] |
| --- | ---: | ---: | ---: |
| X_Minus | -150 | 0 | 0 |
| Base | 0 | 0 | 0 |
| X_Plus | +150 | 0 | 0 |

Thus the two outer spacecraft are 300 m apart, and each is 150 m from Base. Change `separation_m` at the top to change their separation. For +/-300 m from Base, use `separation_m = 600.0`.

The axes match the previous project's `Syst_SEM_L2` system. More precisely, STK's SEM system uses the Sun and Earth-Moon system; it is not an exact Sun-Earth-only circular restricted three-body frame. The X direction points from the Sun towards L2. The axes rotate with this system; they are not Earth-fixed axes or a spacecraft's velocity-aligned frame.

All three start with the same velocity components in this rotating frame. Their initial relative velocities in this frame are therefore zero. This does not mean that their inertial velocity vectors are exactly equal: keeping an offset stationary in a rotating frame requires the corresponding rotation contribution to inertial velocity.

Every spacecraft has only two Astrogator segments:

1. **Initial_State:** assign its initial position and velocity.
2. **Coast:** propagate for 30 days using `Earth Default High Fidelity v13`, the same propagator component named in the previous project.

There are no manoeuvres, Follow segments, target sequences, differential correctors, or station-keeping loops. The temporary JWST reference is removed after its initial state is read, leaving exactly three Satellite objects.

Base starts at JWST's position AND velocity but then coasts independently. It is not forced to follow JWST's later ephemeris or the original project's corrected Base trajectory. This distinction matters: replaying the real JWST ephemeris would also replay the effects of its real manoeuvres. Here, all three spacecraft are uncorrected throughout the simulation.

The script retains Astrogator's default spacecraft physical properties and the installed force-model component. It does not reproduce JWST's actual mass, area, or attitude-dependent radiation pressure. This is a learning scenario for relative motion, not a calibrated JWST prediction. You can inspect the selected propagator through the Coast segment to see its configured forces and integration settings.

## Read the code in this order

- **User configuration:** where the data are, when the experiment starts, the duration, and the separation.
- **Scenario:** open STK and set units and dates. Object Model units and Connect command units are set separately.
- **L2 coordinate system:** choose the origin and axis directions for expressing the state.
- **JWST state:** let STK interpolate the supplied ephemeris at the chosen epoch and express both position and velocity in that system.
- **Spacecraft loop:** repeat the same Initial_State + Coast setup for three different X offsets.
- **Base-centred frame:** move the display origin onto Base while keeping the L2 axis directions.
- **Graphics and saving:** choose colours and markers, centre the camera, and save the scenario. These choices do not change the trajectories.

The fixed-in-L2 attitude setting aligns the displayed spacecraft body axes with the chosen reference axes. It does not hold the spacecraft's orbital position or apply translation manoeuvres. Attitude-control torques and their fuel cost are not modelled here.

## First checks

The terminal should print initial offsets approximately equal to:

```
Base    : x = +0.000,   y = +0.000, z = +0.000
X_Minus : x = -150.000, y = +0.000, z = +0.000
X_Plus  : x = +150.000, y = +0.000, z = +0.000
```

Tiny numerical differences and negative zeros are harmless. The script checks these offsets within 1 cm and checks that each trajectory reaches the requested stop time. These checks validate the setup, not the scientific accuracy of the force model.

In STK, open each spacecraft's **Properties > Basic > Orbit**. Its Mission Control Sequence should contain Initial_State and Coast, followed by the normal end marker, with no manoeuvres or target sequences. Select Initial_State to inspect the six Cartesian state components.

No STK installation is available in the environment used to prepare this script. Its Python syntax and packaging were checked, and the interfaces were checked against STK's API documentation; the actual propagation and graphics still need to run on your Windows installation.

## Viewing the formation

### 1. Start with the close view already configured

The script centres the camera on Base, selects the SEM_L2 camera axes, and requests a viewing distance of 1 km. It displays coloured markers instead of enlarged spacecraft models. Initial separations of hundreds of metres are too small to distinguish in an Earth-scale or halo-orbit-scale view.

Open **View From/To** on the 3D Graphics toolbar. Set both From Position and To Position to Base if the camera is not centred correctly. In this mode, STK places the camera at an offset from Base and points it towards Base; it does not place the camera inside the spacecraft. Use Fixed Distance to set a distance of approximately 0.5-2 km. A fixed distance disables mouse zoom; clear it when you want to zoom freely.

Use the SEM_L2 axes as the camera Reference Frame. If the outer spacecraft overlap on screen, rotate the view: looking along X hides their initial X separation. A view looking roughly along Z makes the X separation clear. Since Base's body axes are fixed to L2 axes, Base's Body frame has the same axis directions.

Documentation: https://help.agi.com/stk/Content/vo/3DViewPosition.htm

### 2. Use the Base-centred orbit system for relative drift

For each spacecraft, open **Properties > 3D Graphics > Orbit System**. The script adds **Sun Syst_Base_L2** and disables **Inertial by Window**. This displays the trajectory relative to the moving Base, expressed along the L2 axes. Base itself stays at the origin. The two outer tracks show their relative drift.

This is a display coordinate transformation, not a constraint on the motion. Centring the camera on Base alone is not sufficient to make orbit trails show relative trajectories; the Orbit System setting controls those trails.

If trails are too long or distracting, adjust **3D Graphics > Pass** and its leading/trailing intervals, or temporarily hide orbit lines while keeping markers visible. Begin by viewing the initial positions and then animate forward. Try an animation step of 1 hour initially; change it to 6 hours to move through the month faster. This changes playback, not the numerical integrator's step size.

Documentation: https://help.agi.com/stk/Content/vo/orbitframe.htm

### 3. Use a separate view for the larger L2 trajectory

For the large-scale view, switch each spacecraft's displayed Orbit System to **Sun Syst_SEM_L2** using **Add VGT System...**, and hide **Sun Syst_Base_L2** in that window. Zoom out substantially. The three paths will initially appear almost identical at this scale.

If using two 3D windows, the Orbit System table lets you choose which window shows each coordinate system. This allows one window for Base-centred formation motion and one for the larger L2 trajectory. Choose the camera reference axes separately in View From/To. The camera frame controls how you look; the Orbit System controls how trajectory lines are drawn.

A 30-day free coast shows only part of the large trajectory. Increase `duration_days` if useful, but do not expect an uncorrected spacecraft to stay on the original project's optimised halo orbit indefinitely.

Documentation: https://help.agi.com/stk/Content/vo/orbitframe.htm

### 4. Keep markers readable

The script uses white for Base, cyan for X_Minus, and yellow for X_Plus, with 8-pixel circular markers. In **Properties > 3D Graphics > Model**, you can change marker size and detail thresholds. If a marker disappears when you change distance, inspect its Show option and detail thresholds. If using 3D spacecraft models later, keep their scale sensible relative to a 150 m spacing so enlarged models do not overlap misleadingly.

Documentation: https://help.agi.com/stk/Content/vo/model.htm

### 5. Check distances numerically

Use **Analysis Workbench > Vector Geometry** to create a **Displacement** vector from Base's Center point to an outer spacecraft's Center point. Display its magnitude through a calculation/report to check the Base-to-spacecraft distance. Repeat between X_Minus and X_Plus for their mutual separation. Initially these should be 150 m, 150 m, and 300 m respectively.

For components, express the displacement in **Sun SEM_L2** axes. A range alone does not tell you whether the drift is in X, Y, or Z. The Base-centred rotating frame used in the script is useful for interpreting those components consistently.

Documentation: https://help.agi.com/stk/Content/training/WorkingWithVectors.htm

## Suggested first experiments

1. Run the default 30-day case and watch how an initially straight formation changes.
2. Change only `duration_days` to 1, then 7, then 30. Compare how quickly the geometry changes.
3. Change only `separation_m` to 600. Compare the relative drift with the 300 m case.
4. Inspect the Initial_State and Coast segments in STK before adding any more automation.

Keep the same date and initial velocity convention while comparing separations. Changing either can change the dynamics being compared.
