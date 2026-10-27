# TIC 417732194 (G 249-11): planet candidate vetting report

Prepared 2026-10-23; corrected the same day after an independent adversarial review. Status: **unconfirmed planet
candidate** from TESS photometry. Not submitted anywhere.

> **Corrections after review (read first).**
> 1. Earlier versions gave T0 as BJD 2460912.3151. That is wrong by exactly 1000 d. The correct value is
>    **2459912.3151** (= BTJD 2912.3151 + 2457000).
> 2. **Independence.** S19, S59 and S60 were the search data that selected this candidate. The period that seeded the
>    "2023-only" fit came from a full-baseline fit that already included S19. Only **S73 and S86** were never used
>    for selection. The 2019 alias match is therefore consistency, not an independent confirmation.
> 3. **Post-selection evidence** (full-pipeline null, stress.json): S73 p = 0.09, S86 p = 0.0025. Combined
>    (Fisher) p ~ 0.002, about **3 sigma**. The per-sector look-elsewhere p-values in a/results.json are overstated:
>    overlapping null windows leave only ~11-20 independent trials, and the best of three photometry sources was
>    quoted.
> 4. **Per-transit depths scatter** with reduced chi2 2.2 while the photometric noise is white (beta ~ 1). Allowing
>    for that excess, the combined SNR is ~8, not 12. Delta lnL = 75 was maximised on the search data and is not a
>    significance.
> 5. **False positives NOT excluded.**
>    - A bound eclipsing binary: the free fit prefers a denser host; Gaia astrometric_excess_noise_sig = 8.5.
>    - The G 17.2 neighbour 20" away (~1 TESS pixel; ~1.6 % of the flux in the TESS band, so it would need a ~20 %
>      eclipse). The single-pixel difference image cannot separate it.
>    - Fainter neighbours: G 18.7 at 24" and G 19.0 at 38".
>    - The aperture test has no power. Its weak S59/S60 trend (deeper in larger apertures) points the wrong way for
>      an on-target source.
> 6. **Verdict:** a probably real, recurring ~3 ppt, ~0.8 h dip on or near the target. That justifies a CTOI and
>    follow-up, and nothing stronger.

## Star
G 249-11 = LSPM J0530+6854 = NLTT 15105 = Gaia DR3 484671464331349632, M4.5 dwarf (SIMBAD dM4.5).
Distance 29.1 pc (parallax 34.378 +- 0.017 mas), Teff 3180 +- 157 K, R 0.266 +- 0.008 Rsun, M 0.238 +- 0.020 Msun,
rho 12.7 rho_sun (TIC 8.2), Tmag 12.30, J 10.55, K 9.73. Gaia RUWE 1.20, non_single_star 0, RV 15.4 km/s.
No neighbour brighter than G 15.3 within 60 arcsec. The two nearest are G 17.2 at 20 arcsec and G 15.3 at 42 arcsec,
both distant background stars.

## Signal
P = 5.307425 +- 0.000008 d, T0 = 2459912.3151 BJD_TDB (BTJD 2912.3151 +- 0.0008).

| Parameter | Free fit | With stellar-density prior |
|---|---|---|
| Depth | ~3.1-3.4 ppt | |
| Rp/R* | 0.051 | 0.055 +- 0.003 |
| Rp | 1.47 Re | 1.61 +- 0.09 Re |
| b | | 0.83 +- 0.03 |
| a/R* | | 30 +- 2 |
| T14 | | 0.88 h |

The density prior costs only Delta lnL = 0.6, so the transit is physically consistent with the host star.
a = 0.037 AU, Teq about 410 K (albedo 0), insolation about 4.8 Earth.
Expected RV semi-amplitude about 3-4 m/s for a 4 Earth-mass rocky planet.

## Data (TESS sectors 19, 59, 60, 73, 86)
- SPOC 2-min: S19, S59, S60.
- QLP 200-s: S73, S86.
- Own TESScut aperture photometry: 1, 2 and 3 px apertures.

Transit model vs flat line: Delta lnL = 75 (combined SNR about 12). 17 of 18 individual transits show a dip at the
predicted time. Weighted mean depth 3,089 ppm, reduced chi2 of the event depths 2.2.

## Tests passed
1. **Blind prediction.** The ephemeris was fitted on S59-60 (2023) only.
   - S73: dip found 68 orbits later at 2,500 ppm, SNR 3.7-4.3, look-elsewhere p < 0.003 (QLP, 1-px aperture).
   - S86: dip found 134 orbits later at 3,000-3,700 ppm, SNR 3.4-4.4, p <= 0.02.
   - The timing offsets (-1.2 h, -2.9 h) are linear in orbit number, i.e. one slightly shorter period. The final
     ephemeris absorbs them.
2. **2019 (S19, 2-min).** Among about 12 aliases allowed by 2023-2025, one peak stands out at P = 5.30743 d, with
   SNR 7.3 and depth 3,400 ppm, the same depth as 2023-2025. Four of five 2019 transits are individually positive,
   with timing within 0-10 min.
3. **Odd/even:** 2,748 +- 462 vs 3,490 +- 419 ppm (1.2 sigma). **Secondary at phase 0.5:** -133 +- 300 ppm (none).
4. **Pixel-level difference image (TESScut S59):** the flux deficit peaks on the target pixel (SNR 5, 12 arcsec,
   within a pixel). No significant deficit elsewhere in the 15x15 cutout.
5. **Aperture-size depth (1/2/3 px, S59/60/73/86):** consistent within the errors.
6. **Blend arithmetic (superseded, see correction 5).** The G 15.3 star at 42" is implausible: it would need a deep,
   hours-long eclipse. The G 17.2 star at 20" is NOT excluded: it would need only a ~20 % eclipse, and a single-pixel
   difference image cannot separate it from the target.
7. **Novelty.** Not a TOI or CTOI (ExoFOP lists checked 2026-10-23: 8,152 TOIs, 5,140 CTOIs). No SPOC TCE or DV
   report. Not in the NASA Exoplanet Archive, VSX, Gaia DR3 variability or the TESS EB catalogue. SIMBAD lists it
   only as a high-proper-motion M dwarf.

## Stress tests (2026-10-23, build/stress.py, deep/stress.json)
**Full-pipeline false-alarm test.** 400 null runs. In each, the real transits are masked and each sector's timeline is
circularly scrambled. Each run then goes through the same chain as the candidate: search 2023 (1-15 d,
0.4-1.2 h) for the best peak, blind-check S73 and S86 inside the propagated timing window, and scan the 2019 aliases.

| Statistic | Candidate | Null runs (median / 99th percentile / max) | Null fraction >= candidate |
|---|---|---|---|
| 2023 SNR | 9.2 | 5.9 / 7.0 / 7.1 | 0/400 |
| S86 | 4.3 | | 1/400 |
| S73 | 3.1 | | 36/400 |
| 2019 alias | 8.0 | max 5.4 | 0/400 |
| All jointly | | | 0/400 |

An unrestricted search of the 2023 data alone returns this period (P = 5.30748 d) as its top peak.

**Other tests.**
- **Inversion:** the flipped light curve's best peak is SNR 6.3 at an unrelated period, which is null-like.
- **Detrending:** 7 detrenders (biweight 0.3/0.5/1.0 d, median, cosine) give depth 2,565-2,741 ppm and SNR 12.3-13.1.
- **Red noise:** beta at the transit timescale is 0.90-1.04, so the noise is white and the SNRs are not inflated.
- **Activity:** no significant rotation signal (Lomb-Scargle power <= 0.06). 9 flares in 5 sectors, one within 1 h of a
  transit (clipped). Spots and flares cannot produce the signal.

## TESS coverage
tess-point 0.9.5 gives sectors 19, 59, 60, 73 and 86 (all used here) and next **Sector 125** (camera 1, CCD 3).
S125 is in Cycle 10 (19 Sep 2027 - 13 Sep 2028); its dates are not yet published, roughly Dec 2027 - Jan 2028.
About 5 transits, an expected single-sector SNR of about 7. FFIs will be taken at 200 s regardless of target lists.

## Open issues and what would confirm it
- Each sector is individually low SNR (3.4-7). The case rests on the combination and on the blind predictions.
- The event-depth scatter (reduced chi2 2.2) is larger than the white noise. M-dwarf flares and spots may leak in.
- An unresolved bound companion within about 1 arcsec (a hierarchical eclipsing binary) is not excluded.
  High-resolution imaging (speckle or AO) and the Gaia RUWE of 1.2 bear on this.
- Why SPOC TPS produced no TCE is not known. Likely causes are the short duration (under 1 h) and per-sector
  MES below 7.1.

Confirmation path:
- Ground-based transit photometry at the predicted times (1-2 m telescope, 3.4 ppt, I/z band; e.g. a
  SPECULOOS/MEarth-class facility).
- High-resolution imaging.
- Precise RV (CARMENES / MAROON-X / SPIRou class) for the mass.

Next predicted transits (BJD_TDB) = 2459912.3151 + 5.307425 x N, with uncertainty about 0.0008 + N x 0.000008 d.

Files: deep/star_clean.json, lcs.npz, a/results.json (blind tests, alias, aperture), fit2.json (fits, per-transit),
a/*.png, ../build/pix/pix/417732194_S59_pix.png.
