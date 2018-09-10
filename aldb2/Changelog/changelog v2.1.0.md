```
## Module
**Table Name**
_Change Type_
* Category
  * Action
    [* Specifics for action ]
```

## All
**All Aliases**
_Update_
* Create
  * _.official_ boolean
  * _.official+.language_ Unique Constraint

## Core
**relationship**
_New Table_
* Description
  * The Relationship Table replaces the explicit, rigid hierarchy of the previous Series-Subseries-Season structure.
  * Relationship Table maps a relationship between two series; when hierarchical, the "parent" series should be used.

**series**
_Rename and Restructure_
* Create  
  * aliases_franchise
* Remove
  * subseries.series _(New Series table)_

**subseries**
_Rename_
* Change
  * subseries
    * _subseries_ -> series
  * season_fulltext _(this may not be necessary)_
  * manga_series
	* _.subseriesid_ -> .series
  * genrelist_subseries
    * _name_ -> genrelist_series
	* _.subseries_ -> .series
  * season
    * _.subseries_ -> .series
* Remove
  * season_fulltext.subseries

## AnimeLife
**al_subseriesranking**
_Rename and Update_
* Change
  * al_subseriesranking
    * _al_subseriesranking_ -> _al_seriesranking_
  * subseries
    * _subseries_ -> series

**al_normalized**
_Update_
* Change
  * subseries
    * _subseries_ -> series

**showweeks**
_Update_
* Change
  * subseries references in join and selection
    * _subseries_ -> series
