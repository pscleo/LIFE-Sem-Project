Nice — below is a compact, practical **manual transformation plan** you can implement by hand or in a script to convert position/velocity vectors from **ICRF** into a **SEM_L2** frame defined as:

* Origin at the *Sun–Earth L2* point (instantaneous),
* +X axis = **anti-Sun** (points away from the Sun),
* +Z axis = **towards ecliptic north**,
* +Y completes a right-handed system.

I give (A) a high-level overview, (B) exact step-by-step math to compute the origin and axes, (C) how to transform positions and velocities, (D) ways to compute the frame angular rate (needed for velocities), and (E) verification / checks. Use the equations with vectors in ICRF (all vectors and operations in the same coordinate system and units).

---

# A. Overview — the plan in 4 sentences

1. Get Sun and Earth state vectors in ICRF at the epoch (positions and velocities).
2. Compute the L2 position along the Sun–Earth line (iteratively for best accuracy, or approximate using the 3rd-root formula).
3. Build orthonormal basis: ( \hat{x} ) along the anti-Sun direction, ( \hat{z} ) approximately the ecliptic north vector made orthogonal to ( \hat{x} ), and ( \hat{y} = \hat{z}\times\hat{x} ).
4. Translate ICRF coordinates by (\mathbf{r}_{L2}) and rotate into the basis; for velocities include frame motion and the frame angular velocity correction.

---

# B. Compute L2 origin in ICRF

### Inputs (at time (t))

* Sun position (\mathbf{r}_S(t)) and velocity (\mathbf{v}_S(t)) in ICRF (usually Sun wrt solar system barycenter or ICRF origin).
* Earth position (\mathbf{r}_E(t)) and velocity (\mathbf{v}_E(t)) in ICRF (same origin/epoch).

> Note: Make sure Sun and Earth states come from the *same ephemeris / reference frame / epoch* (e.g., JPL DE430 / ICRF).

### Quick approximate L2 location (good first guess)

Let Earth–Sun vector:
[
\mathbf{R}_{ES} = \mathbf{r}*E - \mathbf{r}*S,\quad a = |\mathbf{R}*{ES}| \quad(\text{approx }1,\text{AU}).
]
Mass parameter (Sun vs Earth+Sun): use (\mu = \dfrac{m_E}{m_S+m_E}\approx 3.003\times10^{-6}).
Approximate Earth→L2 distance (d):
[
d \approx a\left(\frac{\mu}{3}\right)^{1/3}
]
Numerical value: (d\approx 0.01,\text{AU}\approx 1.5\times10^{6},\text{km}).
Approximate L2 position in ICRF:
[
\mathbf{r}*{L2}^{(0)} = \mathbf{r}_E + d\cdot\frac{\mathbf{r}_E - \mathbf{r}_S}{|\mathbf{r}_E-\mathbf{r}_S| }.
]
This gives a good starting point.

### Refined L2: solve 1-D collinear equilibrium (Newton–Raphson)

For higher accuracy compute the collinear L2 along the Sun–Earth line by solving for (x) (distance from Earth along Sun→Earth line, beyond Earth) that satisfies the rotating-frame equilibrium (in Sun–Earth two-body + rotating centripetal approx). Using a Sun-centered or Earth-centered scalar equation is standard; a convenient scalar equation (see CR3BP collinear point derivations) is:

Define normalized coordinates where Sun at (x=0), Earth at (x=a). Solve for (x > a) satisfying:
[
\frac{G m_S}{(x)^2} - \frac{G m_E}{(x-a)^2} - \omega^2 x = 0,
]
with (\omega^2 = \dfrac{G(m_S+m_E)}{a^3}). Numerically solve for (x) (Newton–Raphson) starting from (x \approx a + d). Then convert back to vector form along (\mathbf{r}_E - \mathbf{r}_S):

Finally:
[
\mathbf{r}_{L2} = \mathbf{r}_S + \frac{x}{a},(\mathbf{r}_E-\mathbf{r}_S).
]

(If you prefer a simpler iterative vector method: start with (\mathbf{r}_{L2}^{(0)}), compute net force in rotating frame and correct the scalar along the line until accelerations balance — same idea.)

> Practically: for most reporting purposes the simple approximate formula with (d) above is sufficient. If you need sub-km precision use the Newton refinement.

---

# C. Build SEM_L2 orthonormal axes (instantaneous)

We want:

* (+\hat{\mathbf{x}}) = anti-Sun (pointing away from Sun),
* (+\hat{\mathbf{z}}) = ecliptic north (but orthogonalized to (\hat{\mathbf{x}})),
* (+\hat{\mathbf{y}} = \hat{\mathbf{z}} \times \hat{\mathbf{x}}).

Steps:

1. Anti-Sun direction (from L2 toward anti-Sun):
   [
   \mathbf{u}*x = \mathbf{r}*{L2} - \mathbf{r}_S \quad(\text{vector from Sun to L2})\
   \hat{\mathbf{x}} = \dfrac{\mathbf{u}_x}{| \mathbf{u}_x| }.
   ]
   (That points from Sun to L2. Since L2 is on Sun→Earth line beyond Earth, this is the anti-Sun direction.)

2. Ecliptic north estimate: compute instantaneous orbital normal of Earth about Sun:
   [
   \mathbf{n}*{\rm ecl} = \mathbf{r}*E \times \mathbf{v}*E,\quad
   \hat{\mathbf{n}}*{\rm ecl} = \dfrac{\mathbf{n}*{\rm ecl}}{| \mathbf{n}*{\rm ecl}| }.
   ]
   This points toward ecliptic north (ICRF orientation assumed).

3. Make ( \hat{\mathbf{z}} ) orthogonal to ( \hat{\mathbf{x}} ) while pointing as close as possible to ecliptic north:
   [
   \mathbf{z}*\perp = \hat{\mathbf{n}}*{\rm ecl} - (\hat{\mathbf{n}}*{\rm ecl}\cdot\hat{\mathbf{x}}),\hat{\mathbf{x}},
   \quad
   \hat{\mathbf{z}} = \dfrac{\mathbf{z}*\perp}{|\mathbf{z}*\perp| }.
   ]
   (If (\hat{\mathbf{n}}*{\rm ecl}) is nearly parallel to (\hat{\mathbf{x}}) this becomes ill-conditioned — not an issue for Sun–Earth geometry.)

4. Compute (+\hat{\mathbf{y}}) to complete right-handed system:
   [
   \hat{\mathbf{y}} = \hat{\mathbf{z}}\times\hat{\mathbf{x}}.
   ]
   Check orthonormality: (\hat{\mathbf{x}}\cdot\hat{\mathbf{y}}\approx 0), etc.

5. Assemble rotation matrix (R) that maps a vector in ICRF to SEM_L2 coordinates:
   [
   R = \begin{bmatrix} \hat{\mathbf{x}}^\top \ \hat{\mathbf{y}}^\top \ \hat{\mathbf{z}}^\top \end{bmatrix}
   ]
   So for any ICRF vector (\mathbf{a}), the coordinates in SEM_L2 are ( \mathbf{a}' = R(\mathbf{a} - \mathbf{r}_{L2})) (see next).

---

# D. Transform positions and velocities

### Positions

Given an ICRF position (\mathbf{r}) (same origin as (\mathbf{r}_S,\mathbf{r}_E)):

1. Translate to L2 origin:
   [
   \Delta\mathbf{r} = \mathbf{r} - \mathbf{r}_{L2}.
   ]

2. Rotate into SEM_L2:
   [
   \mathbf{r}_{\text{SEM_L2}} = R,\Delta\mathbf{r}
   = \begin{bmatrix} \hat{\mathbf{x}}\cdot\Delta\mathbf{r} \ \hat{\mathbf{y}}\cdot\Delta\mathbf{r} \ \hat{\mathbf{z}}\cdot\Delta\mathbf{r} \end{bmatrix}.
   ]

### Velocities — include origin motion and frame rotation

Let ICRF velocity be (\mathbf{v}), and L2 velocity (derivative of (\mathbf{r}*{L2})) be (\mathbf{v}*{L2}). Compute L2 velocity numerically from Earth & Sun motion, or via linearization after Newton step.

Compute relative velocity:
[
\Delta\mathbf{v} = \mathbf{v} - \mathbf{v}_{L2}.
]

If the SEM_L2 axes were fixed in inertial space then velocity in that frame would be (R,\Delta\mathbf{v}). But axes rotate slowly, so correct by subtracting the frame angular velocity cross product:

[
\boxed{\mathbf{v}_{\text{SEM_L2}} = R\Delta\mathbf{v} - \boldsymbol{\Omega}\times (R\Delta\mathbf{r})}
]

where (\boldsymbol{\Omega}) is the instantaneous angular velocity vector of the SEM_L2 basis expressed in SEM_L2 coordinates (or expressed in ICRF and then rotated in if easier).

### Compute (\boldsymbol{\Omega}) numerically (recommended practical approach)

Analytic (\boldsymbol{\Omega}) is tedious. A robust practical method is finite difference of the rotation matrix:

1. Choose a small time step ( \Delta t ) (e.g., 10–60 s for precise spacecraft work; for coarse reports you can use minutes/hours depending on required accuracy).

2. Compute (R(t)) at time (t) and (R(t+\Delta t)) repeating the axis construction above using state vectors at (t+\Delta t).

3. Compute relative rotation matrix:
   [
   \Delta R = R(t+\Delta t),R(t)^\top.
   ]
   For small (\Delta t), (\Delta R \approx I + [\Omega]*\times \Delta t), where ([\Omega]*\times) is skew matrix of angular velocity in the original frame.

4. Extract skew matrix:
   [
   [\Omega]_\times \approx \frac{\Delta R - I}{\Delta t}.
   ]

5. Recover vector (\boldsymbol{\Omega}) from skew matrix:
   [
   [\Omega]_\times = \begin{bmatrix} 0 & -\Omega_z & \Omega_y \ \Omega_z & 0 & -\Omega_x \ -\Omega_y & \Omega_x & 0 \end{bmatrix}
   ]
   so read off (\Omega_x,\Omega_y,\Omega_z).

6. Express (\boldsymbol{\Omega}) in SEM_L2 coordinates (either extract from (\Delta R) as above because ([\Omega]_\times) will be in the SEM_L2 basis if you formed (\Delta R) that way, or rotate it appropriately).

This numerical approach is simpler and stable for most applications.

---

# E. Implementation checklist & verification

## Implementation checklist

1. Load Sun & Earth states in ICRF at time (t).
2. Compute approximate L2 position (\mathbf{r}_{L2}^{(0)}); optionally refine with Newton iteration for higher accuracy.
3. Compute (\hat{\mathbf{x}},\hat{\mathbf{z}},\hat{\mathbf{y}}) and build (R).
4. Compute (\mathbf{r}*{L2}) velocity (\mathbf{v}*{L2}) (finite diff of (\mathbf{r}_{L2}(t))).
5. For each ICRF state ((\mathbf{r},\mathbf{v})): compute (\Delta\mathbf{r},\Delta\mathbf{v}), compute (R\Delta\mathbf{r}), compute (\boldsymbol{\Omega}) via finite-difference and then (\mathbf{v}_{\text{SEM_L2}} = R\Delta\mathbf{v} - \boldsymbol{\Omega}\times(R\Delta\mathbf{r})).
6. Keep consistent units (e.g., km and km/s, or m and m/s). Use radians/sec for (\boldsymbol{\Omega}).

## Quick checks / sanity tests

* Check ( |\hat{\mathbf{x}}|=|\hat{\mathbf{y}}|=|\hat{\mathbf{z}}|=1) and mutual dot products ≈ 0.
* Check that ( \hat{\mathbf{x}} ) is aligned with Sun→L2: (\hat{\mathbf{x}}\cdot (\mathbf{r}_{L2}-\mathbf{r}_S)\approx 1).
* Check ( \hat{\mathbf{z}} ) has positive dot with ecliptic north: (\hat{\mathbf{z}}\cdot\hat{\mathbf{n}}_{\rm ecl}>0).
* Transform the Sun position (\mathbf{r}_S) into SEM_L2: it should lie roughly at negative X ~ −(distance L2→Sun) and near Y,Z ≈ 0.
* Transform Earth position: it should lie roughly in +/− along the X axis inside between Sun and L2.
* Compare velocities: for an object stationary relative to L2 (co-orbiting), the transformed velocity should be near zero when you include full velocity correction.

---

# F. Pseudocode (concise)

```
# Inputs: r_S, v_S, r_E, v_E, r_obj, v_obj at time t; dt for numerical diffs
# 1. approximate d
a = norm(r_E - r_S)
mu = m_E/(m_S + m_E)
d = a * (mu/3)**(1/3)
r_L2 = r_E + d*(r_E - r_S)/a

# optional: refine r_L2 via NR solver along line

# 2. build axes
ux = (r_L2 - r_S); ux = ux / norm(ux)
n_ecl = cross(r_E, v_E); n_ecl = n_ecl / norm(n_ecl)
z_perp = n_ecl - dot(n_ecl, ux)*ux; uz = z_perp / norm(z_perp)
uy = cross(uz, ux)

R = [ ux'; uy'; uz' ]   # 3x3

# 3. compute r_L2 velocity numerically (use small dt)
r_L2_future = compute_r_L2_at(t+dt)  # repeat steps at t+dt
v_L2 = (r_L2_future - r_L2)/dt

# 4. relative vectors
dr = r_obj - r_L2
dv = v_obj - v_L2
r_sem = R * dr

# 5. compute Omega by finite diff of R
R_future = compute_R_at(t+dt)
DeltaR = R_future * R.T
Omega_skew = (DeltaR - I)/dt
Omega_vec = vee(Omega_skew)   # extract vector
v_sem = R * dv - cross(Omega_vec, r_sem)
```

---

# G. Practical tips & caveats

* Use the *same* ephemerides for Sun/Earth and the object. Inconsistent ephemerides produce errors.
* Choose (\Delta t) small enough to capture rotation rate (10–60 s is safe for spacecraft dynamics; larger dt for coarse reporting).
* If you only need positions (no velocities), skip the (\boldsymbol{\Omega}) correction — just translate & rotate.
* L2 is not a fixed point in inertial space; it slowly moves with Earth–Sun motion — recompute per epoch for time series.
* If you need extremely high precision (m level) use a full CR3BP root-finding on the ephemeris positions and include perturbations; the approximate formula may be insufficient.

