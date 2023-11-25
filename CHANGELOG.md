# Changelog for plugin *topobank-statistics*

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
