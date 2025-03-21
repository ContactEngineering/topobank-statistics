# Changelog for plugin *topobank-statistics*

## 1.6.1 (2025-03-17)

- MAINT: Moved all frontend code to ce-ui

## 1.6.0 (2025-03-16)

- MAINT: Updates for API changes in topobank 1.57.1
- MAINT: Moved rounding function form topobank to utils.py
- MAINT: Fixed pint deprecation, closes #47

## 1.5.0 (2025-02-09)

- MAINT: Updates for API changes in topobank 1.55.0

## 1.4.0 (2024-11-13)

- MAINT: Updates for API changes in topobank 1.50.0

## 1.3.0 (2024-05-12)

- ENH: Use new `AnalysisCard` component

## 1.2.4 (2024-03-22)
 
- BUG: Fixed version discovery

## 1.2.3 (2024-03-21)

- BUILD: Changed build system to flit

## 1.2.2 (2024-03-12)

- MAINT: Compatibility with topobank 1.7.0

## 1.2.1 (2024-01-20)

- MAINT: Enforcing PEP-8 style

## 1.2.0 (2023-11-25)

- MAINT: Update to Bootstrap 5

## 1.1.2 (2023-08-21)

- MAINT: More fixes to CSRF injection

## 1.1.1 (2023-08-04)

- MAINT: Unified CSRF injection

## 1.1.0 (2023-06-11)

- ENH: Unified single page application for analyses, including rewritten
  task status
- ENH: Webpack based bundling (for the analysis app)
- ENH: Upgrade to Vue 3
- MAINT: Easier to use download format for roughness parameters (#4)

## 1.0.2 (2023-04-06)

- BUG: Reverted to old contact mechanics card view

## 1.0.1 (2023-04-06)

- MAINT: Fixes to version discovery

## 1.0.0 (2023-01-31)

- MAINT: Version discovery from VCS

## 0.92.1 (2022-12-07)

- ENH: Made Tasks button more prominent as in
  main application
- BUG: Fixed wrong template names
- MAINT: In roughness parameters downloads, renamed
  column "surface" to "digital surface twin" (#890)
- MAINT: Removed explicit checks for reentrant 
  topographies, now handled by SurfaceTopography

## 0.92.0 (2022-10-14)

This is the initial version of the plugin, based on
the code and the functionality of the statistical
functions in topobank 0.91.1.

Now, as plugin, topobank >= 0.92.0 is needed for usage.
