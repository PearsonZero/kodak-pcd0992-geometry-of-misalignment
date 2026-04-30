# Methodology

## Overview

This document describes the computation pipeline used to generate all per-image geometry of misalignment results in this repository. Every metric is deterministic and reproducible using Python 3, NumPy, and matplotlib. No image-level processing is performed — the analysis operates entirely on the statistical outputs of the prior two papers in this series.

## Source Data

Per-image gap analysis JSON files from Baetzel (2026b), each containing the PCA eigendecomposition (eigenvalues, eigenvectors, variance explained) originally computed in Baetzel (2026a) and the BT.601 YCbCr residual correlations. These JSON files are available in the [Paper 2 repository](https://github.com/PearsonZero/kodak-pcd0992-bt601-decorrelation-gap).

## Pipeline

### 1. BT.601 Reference Vectors

The BT.601 coefficient matrix defines three row vectors in RGB space:

```
Y  = [ 0.299,     0.587,     0.114    ]
Cb = [-0.168736, -0.331264,  0.5      ]
Cr = [ 0.5,      -0.418688, -0.081312 ]
```

Each row is normalized to unit length to produce the BT.601 reference directions:

| Axis | Unit Vector |
|---|---|
| Y | [0.4472, 0.8780, 0.1705] |
| Cb | [-0.2708, -0.5317, 0.8025] |
| Cr | [0.7608, -0.6371, -0.1237] |

### 2. Angular Misalignment Computation

For each of the 24 images, the three KLT eigenvectors from the PCA decomposition are normalized to unit length. The angular distance between each eigenvector and its corresponding BT.601 reference vector is computed as:

```
θᵢ = arccos( | eᵢ · bᵢ | )
```

where eᵢ is the i-th KLT eigenvector and bᵢ is the i-th BT.601 unit vector. The absolute value of the dot product accounts for sign ambiguity in eigenvector direction, which is arbitrary and carries no geometric meaning. This produces three angles per image:

* **θ₁ (PC1↔Y):** misalignment between the dominant principal component and the luminance axis
* **θ₂ (PC2↔Cb):** misalignment between the second principal component and the blue chrominance axis
* **θ₃ (PC3↔Cr):** misalignment between the third principal component and the red chrominance axis

The axis correspondence follows eigenvalue ordering: PC1 (largest variance) pairs with Y, PC2 and PC3 (descending) pair with Cb and Cr respectively.

### 3. Energy-Weighted Composite Angle

A single-scalar summary is computed as the variance-weighted sum of the three angular misalignments:

```
θ_weighted = Σ (λᵢ / Σλ) · θᵢ
```

where λᵢ are the eigenvalues from the PCA decomposition. This assigns importance to each axis in proportion to the variance it carries.

### 4. Decorrelation Efficiency

Efficiency values are carried forward from the Paper 2 JSON files:

```
Efficiency = (RGB avg |r| − YCbCr avg |r|) / RGB avg |r| × 100
```

### 5. Three-Axis Regression

An ordinary least-squares multiple regression is computed using all three angular misalignments as independent variables and decorrelation efficiency as the dependent variable (n = 24). The regression produces:

* **Coefficients** for θ₁, θ₂, θ₃, and intercept
* **R² and R** for the overall model
* **Per-image predicted efficiency** and residual

A separate single-variable regression is computed using the energy-weighted composite angle for comparison.

### 6. Axis-Specific Residual Correlations

Bivariate Pearson correlations are computed between each angular misalignment (θ₁, θ₂, θ₃) and each YCbCr residual correlation pair (|Y–Cb|, |Y–Cr|, |Cb–Cr|), producing a 3×3 correlation matrix. Statistical significance is assessed against the critical value r = 0.404 (p < 0.05, two-tailed, df = 22).

### 7. Diagnostic Tiers

Each image is assigned a diagnostic tier (Aligned / Moderate / Critical) based on its decorrelation efficiency relative to the suite distribution, using tercile boundaries computed from the sorted efficiency values.

## Output Format

Each image produces one JSON file containing:

* Image ID, title, dimensionality tier, condition number
* Variance explained per principal component
* Angular misalignment: θ₁, θ₂, θ₃, and total degrees
* Energy-weighted angle
* Decorrelation efficiency (measured)
* Predicted efficiency (3-axis model) and residual
* Diagnostic tier

Each image produces one two-page PDF containing:

* **Page 1:** Predicted vs. actual efficiency scatter plot (all 24 images, this image highlighted); angular misalignment profile with suite range whiskers
* **Page 2:** Model comparison (measured vs. 3-axis predicted vs. energy-weighted); axis-specific residual correlation table; key findings summary; global model equation

One suite summary JSON aggregates regression parameters, angular range statistics, energy-weighted R², and diagnostic tier boundaries.

## Dependencies

| Package | Role |
|---|---|
| Python 3 | Runtime |
| NumPy | Correlation, eigendecomposition, regression, angular computation |
| matplotlib | PDF generation (per-image data sheets) |

No proprietary tools, no trained models, no parameters to tune. Every value is deterministic from the published per-image JSON outputs of Papers 1 and 2.
