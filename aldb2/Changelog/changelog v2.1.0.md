```
## Module
**Table Name**
_Change Type_
* Category
  * Action
    [* Specifics for action ]
```

## Overview
The goal of this update was to change the relation structure between Anime series to be more flexible and descriptive.
In order to do so, the current Series-Subseries-Season structure had to be replaced. The pure-sql solution for this would have been to
create a large number of tables- making the database significantly more complex- to handle all of the in-between relations,
which would have resulted in more individual table queries for very little benefit.

Therefore, the module was moved away from the pure-sql setup and much of the data processing is now handled via python. This results
in a much simpler database structure, albeit it may require additional queries to get all of the information.

It may be better to refer to this version as 3.0, but as the difference between v1 and v2 was a 100% complete backend overhaul,
it did not seem quite on the same level.

## Core
**graphdb_edges**
_New Table_
* Description
  * The database Connnection Object is being changed to GraphDB (from `alcustoms.sql`) to help facilitate the new relation-based structure of the database.
  * graphdb_edges maps a relationship between a rowid+tablename and another rowid+tablename (with optional relationship values).

**aliases**
_Restructure and Remove_
* Description
  * All aliases will be combined into one table. This has the benefits of cutting down on the number of aliase tables as well as simplifying title searches.
  * Relations between aliases and their target is maintained by **graphdb_edges**
* Remove
  * All aliases tables 
* Create
  * **aliases**
    * _.aliasid_ Integer Primary Key Autoincrement
    * _.alias_ text Not Null
    * _.official_ boolean Default False
      * New boolean which replaces the default title of series (now franchise), subseries (now series), and season tables
    * _.language_ text

**genrelist**
_Restructure and Remove_
* Description
  * As per the rational behind the changes to relations and aliases, genres are being changed in the same way
  * All genrelists will be combined into one table with similar benefits
* Remove
  * All genrelist tables
* Create
  * Because the **genres** table already exists, relations will simply be made on the **graphdb_table**

**links**
_Restructure and Remove_
* Description
  * As per the rational behind the changes to other composite tables, links are being changed in the same way
  * All links will be combined into one table with similar benefits
* Remove
  * All links tables
* Create
  * **links**
    * _.linkid_ Integer Primary Key Autoincrement
    * _.url_ text Not Null
    * _.identification_ text

**images**
_Restructure and Remove_
* Description
  * As per the rational behind the changes to other composite tables, images are being changed in the same way
  * All images will be combined into one table with similar benefits
  * (Note: there is some consideration to combining links and images into one table, as both handle urls and
    there is not much of a difference between  _links.identification_ and _images.imagetype_)
* Remove
  * All images tables
* Create
  * **images**
    * _.imageid_ Integer Primary Key Autoincrement
    * _.url_ text Not Null
    * _.imagetype_ text

**series**
_Rename and Restructure_
* Change
  * _series_ -> franchise
* Remove
  * subseries.series _(New Series table)_
  * subseries.subseries

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

**season_fulltext**
_Remove_

## Anime
**similar_anime**
_Remove_
* Note- similar animes can now be handled using the graphdb_edges table (assign relationship to "similar")

_(See also the above removed tables)_

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


## Manga
**manga_series**
_Update_
* Change
  * subseriesid
    * _subseriesid_ -> series

_(See also the above removed tables)_