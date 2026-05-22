# Method notes

This project reproduces the core analysis framework of Qu et al. (2016):

- fixed-threshold daily precipitation classification;
- annual precipitation amount and proportion by intensity class;
- Mann-Kendall trend test;
- Theil-Sen slope estimate.

The project uses publicly accessible point-scale daily precipitation from Open-Meteo instead of the original CMA station dataset.

## Categories

- light: 0.1 <= P < 10 mm/day
- moderate: 10 <= P < 25 mm/day
- heavy: 25 <= P < 50 mm/day
- extreme: P >= 50 mm/day

## Important limitation

The results are not intended to reproduce the numerical values in Qu et al. (2016). They reproduce the method and apply it to a new, smaller case study region.
