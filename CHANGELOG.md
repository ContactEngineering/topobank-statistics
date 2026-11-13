# Changelog for plugin *topobank-statistics*

<!--
Style for this changelog (keep to it so entries stay uniform):

- Newest version first. Heading `vX.Y.Z (DDMonYY)`, underlined with dashes.
  A version not yet released is headed `vX.Y.Z (not yet released)`.
- One bullet per user-visible change, at most two lines (about 200
  characters). Say what changed for the user and, if useful, why or by how
  much. Omit internals: no function, class, file or variable names, no
  environment variables, no commit or PR references.
- Start every bullet with one of: `ENH:` (new feature), `BUG:` (fix),
  `API:` (interface change), `PERF:` (speed or memory), `MAINT:`, `TST:`,
  `DOC:`, `BUILD:`, `CI:`.
- Small related fixes may share one bullet. No trailing period on bullets.
-->

v1.8.0 (02Aug26)
----------------

- ENH: The slope distribution warns about outliers in the RMS slope and reports
  the RMS slope without them, as does the roughness parameter table
- ENH: Robust histograms for height, slope and curvature distributions; their
  Gaussian fits use the standard deviation about the mean
- ENH: Workflows have descriptions for display in the user interface
- ENH: Renamed the workflow "Power spectrum" to "Power spectral density"
- BUG: Opening the roughness parameter card starts missing analyses instead of
  reporting that there are no results
- BUG: Fixed scale-dependent slope and curvature in y-direction, which repeated
  the x-direction, and masked values distorting the slope histogram
- BUG: Roughness parameters are shown in their dedicated card again instead of
  the default plot card
- BUG: Power spectrum, autocorrelation, variable bandwidth and scale-dependent
  analyses no longer crash; their alerts name the measurement without a link
- MAINT: Workflows record the time taken by each step
- MAINT: Updated for the split of the REST API from topobank, the removal of the
  plugin architecture and plugin permissions, and renamed analysis concepts
- MAINT: Removed usage statistics tracking and the server-side conversion of
  analysis results for download
- BUILD: Changed build system to hatchling

v1.7.0 (11Dec25)
----------------

- MAINT: Updated for topobank 1.65.0

v1.6.2 (19Aug25)
----------------

- MAINT: Removed an unused setting for local media storage

v1.6.1 (17Mar25)
----------------

- MAINT: Moved all frontend code to ce-ui

v1.6.0 (16Mar25)
----------------

- MAINT: Updated for API changes in topobank 1.57.1
- MAINT: Fixed a deprecation warning from pint

v1.5.0 (09Feb25)
----------------

- MAINT: Updated for API changes in topobank 1.55.0

v1.4.0 (13Nov24)
----------------

- MAINT: Updated for API changes in topobank 1.50.0

v1.3.0 (12May24)
----------------

- ENH: Results are shown in the new common analysis card

v1.2.4 (22Mar24)
----------------

- BUG: Fixed detection of the package version

v1.2.3 (21Mar24)
----------------

- BUILD: Changed build system to flit

v1.2.2 (12Mar24)
----------------

- MAINT: Compatibility with topobank 1.7.0

v1.2.1 (20Jan24)
----------------

- MAINT: Code follows PEP 8 style

v1.2.0 (25Nov23)
----------------

- MAINT: Updated to Bootstrap 5

v1.1.2 (21Aug23)
----------------

- MAINT: Further fixes to how the CSRF token is passed to requests

v1.1.1 (04Aug23)
----------------

- MAINT: Unified how the CSRF token is passed to requests

v1.1.0 (11Jun23)
----------------

- ENH: Unified single page application for analyses, including a rewritten
  task status
- ENH: The analysis app is bundled with Webpack
- ENH: Upgraded to Vue 3
- MAINT: Easier to use download format for roughness parameters

v1.0.2 (06Apr23)
----------------

- BUG: Reverted to the old way of choosing the card view for an analysis

v1.0.1 (06Apr23)
----------------

- MAINT: Fixes to the detection of the package version

v1.0.0 (31Jan23)
----------------

- MAINT: The package version is taken from version control

v0.92.1 (07Dec22)
-----------------

- ENH: Made the Tasks button more prominent, as in the main application
- BUG: Fixed wrong template names
- MAINT: The roughness parameter download names the column "digital surface
  twin" instead of "surface"
- MAINT: Reentrant measurements are no longer checked here; SurfaceTopography
  reports analyses that do not support them

v0.92.0 (14Oct22)
-----------------

- MAINT: Initial version of the plugin, based on the statistical functions
  of topobank 0.91.1; requires topobank 0.92.0 or newer
