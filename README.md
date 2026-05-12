[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20148259.svg)](https://doi.org/10.5281/zenodo.20148259)
# The Geometry of Misalignment

**Angular Distance Between Image-Specific KLT Axes and BT.601 Fixed Axes Across the Kodak Lossless True Color Image Suite**

Baetzel, J. (2026c)

> **Part 3 of the Kodak Inter-Channel Redundancy Series** — explains the per-image variation in BT.601 decorrelation efficiency documented in [Per-Image Decorrelation Efficiency of the BT.601 Fixed Transform](https://github.com/PearsonZero/kodak-pcd0992-bt601-decorrelation-gap) by measuring the angular distance between each image's KLT-optimal axes and BT.601's fixed axes.

---

This repository contains the first per-image measurement of angular misalignment between the KLT eigenvectors and BT.601 coefficient vectors across all 24 images in the Kodak Lossless True Color Image Suite. Both transforms are rotations of the RGB coordinate system; the angular distance between them explains why BT.601 performs well on some images and poorly on others.

**Key result:** A three-axis angular misalignment model explains 57.6% of the per-image variance in BT.601 decorrelation efficiency (R² = 0.576, p < 0.001, n = 24). An energy-weighted reduction of the same angles to a single scalar — the standard intuition for summarizing multivariate misalignment — produces no predictive power (R² = 0.007). The chrominance axes, which carry less than 5% of total variance, exhibit over 54° of misalignment variation across the suite and drive the majority of the efficiency differences.

## Key Findings

| Metric | Value |
|---|---|
| 3-axis model R² | 0.576 (p < 0.001) |
| Energy-weighted model R² | 0.007 (no predictive power) |
| θ₁ (PC1↔Y) range | 21.89° – 32.93° (narrow) |
| θ₂ (PC2↔Cb) range | 23.89° – 79.75° (>54° spread) |
| θ₃ (PC3↔Cr) range | 21.98° – 76.95° (>54° spread) |
| Cb–Cr residual vs. any single axis | No significant correlation |
| θ₂ and θ₃ coupling (from [6]) | r = 0.9993, slope ≈ 1.004 |

**See the data:** [kodim01](https://github.com/PearsonZero/kodak-pcd0992-geometry-of-misalignment/blob/main/PDF%20and%20JSON/kodim01_geometry.pdf) (strongly one-dimensional — θ₂ = 67.54°, efficiency = 53.0%) · [kodim04](https://github.com/PearsonZero/kodak-pcd0992-geometry-of-misalignment/blob/main/PDF%20and%20JSON/kodim04_geometry.pdf) (peak chrominance misalignment — θ₂ = 79.75°, efficiency = 33.1%) · [kodim22](https://github.com/PearsonZero/kodak-pcd0992-geometry-of-misalignment/blob/main/PDF%20and%20JSON/kodim22_geometry.pdf) (best efficiency — 82.3%)

## What's in This Repo

```
/
├── README.md
├── METHODOLOGY.md
├── baetzel_2026c_geometry_of_misalignment.pdf   ← Full paper
├── kodak_geometry_pdfs.py                        ← PDF + JSON generator script
└── PDF and JSON/
    ├── geometry_suite_summary.json                ← Aggregate metrics + regression
    ├── kodim01_geometry.json                      ← Per-image data (×24)
    ├── kodim01_geometry.pdf                       ← Per-image data sheet (×24)
    ├── ...
    ├── kodim24_geometry.json
    └── kodim24_geometry.pdf
```

Each per-image PDF contains two pages: (1) predicted vs. actual efficiency scatter plot with angular misalignment profile, and (2) model comparison, axis-specific residual correlations, key findings, and global model context. Each per-image JSON contains the angular misalignment measurements, predicted efficiency, residual, and diagnostic tier.

## How to Reproduce

Everything is independently verifiable from publicly available data.

**Requirements:** 24 Kodak PNGs from [r0k.us/graphics/kodak/](http://r0k.us/graphics/kodak/), Python 3, NumPy, matplotlib, Pillow.

**Steps:**

1. Run the Paper 2 gap analysis script to generate the per-image JSON files (or use the published JSONs from the [Paper 2 repository](https://github.com/PearsonZero/kodak-pcd0992-bt601-decorrelation-gap))
2. Run the geometry PDF generator:

```
python kodak_geometry_pdfs.py --input ./results --output ./paper3_output
```

The script reads the per-image gap analysis JSONs, computes angular misalignment between KLT eigenvectors and BT.601 unit vectors, runs the three-axis regression and energy-weighted model, and generates all 24 per-image PDFs, 24 per-image JSONs, and the suite summary JSON.

**No additional image processing is performed.** The script operates entirely on the statistical outputs of Papers 1 and 2. Every value is deterministic.

## Related Work

**Paper 1:** Baetzel, J. (2026a). *Statistical Characterization of Inter-Channel Redundancy Structure in the Kodak Lossless True Color Image Suite.* Establishes per-image KLT ceiling, dimensionality tiers, and eigendecomposition baselines.

**Paper 2:** Baetzel, J. (2026b). *Per-Image Decorrelation Efficiency of the BT.601 Fixed Transform.* Measures BT.601 performance against KLT ceiling and documents the Cb–Cr residual structure.

**Companion:** Baetzel, J. (2026). *The Orthogonal Constraint on Chrominance Axis Misalignment.* Establishes that θ₂ and θ₃ co-vary at r = 0.9993, constraining the misalignment space to two geometric degrees of freedom.

**This paper** explains *why* BT.601 efficiency varies across the suite: the angular distance between each image's optimal axes and BT.601's fixed axes, with chrominance misalignment — not luminance — driving the differences.

## References

1. Wallace, G.K. "The JPEG still picture compression standard." *Communications of the ACM*, vol. 34, no. 4, pp. 30–44, 1991.
2. ITU-R Recommendation BT.601-7, 2011.
3. Watanabe, S. "Karhunen–Loève Expansion and Factor Analysis." pp. 635–660, 1965.
4. Baetzel, J. (2026a). "Statistical Characterization of Inter-Channel Redundancy Structure in the Kodak Lossless True Color Image Suite."
5. Baetzel, J. (2026b). "Per-Image Decorrelation Efficiency of the BT.601 Fixed Transform."
6. Baetzel, J. (2026). "The Orthogonal Constraint on Chrominance Axis Misalignment in the Kodak Lossless True Color Image Suite."

## Citation

```
Baetzel, J. (2026c). The Geometry of Misalignment: Angular Distance
Between Image-Specific KLT Axes and BT.601 Fixed Axes Across the
Kodak Lossless True Color Image Suite.
```

## License

Statistical analysis and data sheets by Jasmine Baetzel (2026). Benchmark images from the Kodak Lossless True Color Image Suite (PCD0992), released by Eastman Kodak Company for unrestricted usage.
