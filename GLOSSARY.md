# Dengue data pipeline

The data side of Goberlab's dengue early-warning system for Peru. It turns surveillance, climate and static sources into one table that a separate modeling effort trains and forecasts on.

## Space and time

**District**:
A Peruvian distrito, identified by its 6-digit UBIGEO. It is the panel's spatial unit.
_Avoid_: municipality, locality, distrito code

**Epi-week**:
An epidemiological week in MINSA's calendar, identified by epi-year and week number (1 to 52 or 53). It is the panel's time unit.
_Avoid_: week (unqualified), calendar week, ISO week

## The panel

**Panel**:
The pipeline's single output table, with one row per district per epi-week. It holds the values each source observed for that district and week, with no lags and no targets. It is the contract between the pipeline and the modeler.
_Avoid_: training set, dataset, feature table

**available_at**:
The earliest moment a panel value could have been known to someone running a forecast. It stores publication time, not the time the event happened.
_Avoid_: timestamp, report date, as-of date

**Issue week**:
The epi-week in which a forecast is made, using only values whose available_at falls before it.
_Avoid_: forecast date, origin, reference week

**Horizon**:
How many epi-weeks after the issue week a forecast targets. This effort covers horizons 1 to 4.
_Avoid_: lead time, step

## Surveillance

**Onset week**:
The epi-week in which a case's symptoms began. The historical national case file dates cases this way.
_Avoid_: case week, report week

**Notification week**:
The epi-week in which a health facility reported a case to surveillance. It comes after the onset week, and the gap between them is the reporting delay.
_Avoid_: report week, registration week

**Snapshot**:
A timestamped copy of a source exactly as it was published at one moment. A run of snapshots shows what was known on each past date.
_Avoid_: vintage, version, dump
