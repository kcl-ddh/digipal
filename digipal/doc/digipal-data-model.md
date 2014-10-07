# DigiPal Data Model
 
# Introduction

* show simplified diagram
* explain what a data model is why it is useful to know the DigiPal model: general understanding of our conceptualisation, admin interface, API, developers (relational database).
* briefly mention its roots (Legacy database, Blog discussion and FRBR)
* explain that it was originally designed for manuscript and handwriting but more general than that (e.g. coins and decorations)


# The Item and its Parts
The Item is central to the DigiPal database. Essentially, an Item corresponds to a physical object such as a manuscript book. Item here draws on the definition from FRBR:

> The entity defined as _item_ is a concrete entity. It is in many instances a single physical object (e.g., a copy of a one-volume monograph, a single audio cassette, etc.). There are instances, however, where the entity defined as _item_ comprises more than one physical object (e.g., a monograph issued as two separately bound volumes, a recording issued on three separate compact discs, etc.). (FRBR [Section 3.2.4](http://archive.ifla.org/VII/s13/frbr/frbr_current3.htm#3.2))

In a historical context, however, the single physical object is often not stable: a book may have been broken into parts, parts of one book bound with those from another, and so on. For this reason we distinguish between the HistoricalItem and the CurrentItem. The **Current Item** is defined to be the object as it exists today, as defined by the library or archive in which it is preserved. In short, it is what you ask for if you go to the library and want to see it. In contrast, the **Historical Item** corresponds to the object as it was at some point in the past. Often this will correspond to a catalogue entry, and in general the HistoricalItem is the one that we are interested in. The **Item Part** is then the maximum possible unit that allows us to map from HistoricalItem to Current Item. It is similar to the 'codicological unit' as defined in Muzerelle's _[Vocabulaire Codicologique](http://vocabulaire.irht.cnrs.fr/)_ but corresponds more to what was or is bound together now, rather than what may or may not have been produced at the same time.

The simplest example is a book which still today takes essentially the same form that it did when it was first produced. In this case there will be one Current Item record describing its current location, one Historical Item record containing the details of its production, and one Item Part to join them together. An example is Antwerp, Plaintin-Moretus Museum M.16.2 (the Current Item), which contains a copy of Boethius' _De Consolatione_ attributed tentatively to Abingdon (the Historical Item). 

A more complex example is Cambridge, Corpus Christi College MSS 162 and 178. Originally there were three manuscripts: one book of homilies and related material (Gneuss No. 50), a manuscript containing Ælfric's _Hexameron_ and other works (Gneuss no. 54), and a bilingual _Rule_ of St Benedict (Gneuss No. 55). These three are therefore Historical Items. However, the second of the three was split into two parts. One part was bound with the bilingual _Rule_, and the other part was inserted into the middle of the homiletic volume. We therefore have two volumes today, CCCC 162 and CCCC 178. These are both Current Items, insofar as they each form distinct volumes and can be request as such from the library today. There are also four distinct codicological units – the homiletic volume, the _Rule_, and the two parts of the _Hexameron_ – and these in turn correspond to Item Parts. In summary, then, there are:


* Two Current Items: CCCC 162 and CCCC 178
* Three Historical Items: CCCC 162 pp. 1–138 and 161–564; CCCC 178 pp. 1–270 + CCCC 162 pp. 139–60; and CCCC 178, pp. 287–457
* Four Item Parts: CCCC 162, pp. 1–138; CCCC 162, pp. 161–564; CCCC 178, pp. 1–270, and CCCC 178, pp. 287–457

 This is represented in the following diagram:

![](/static/doc/Item ER Diagram.jpg?raw=true)

[_Add complications re. ScandiPal model_]

# The Hand and Scribe
**Hand** in DigiPal essentially refers to a single specimen of writing contained within a single Item Part. It therefore approximately corresponds to a stint but implies no assumptions about whether or not a given specimen was produced in a single campaign. A Hand is also assumed to have been written in a given Script: although it may include allographs from a different script, it is assumed that a single primary script can be identified.

This leads to two important points: first, that if an Item contains writing in two different Scripts, then this writing corresponds to two different Hands, one for each Script. Second, if two different Item Parts contain writing by the same Scribe then these are still counted as two different Hands, even if the two parts were originally written as a single volume.

A **Scribe** represents the person who wrote the Hands, i.e. who produced the specimens of writing. In practice the Scribe links different Hands from different Item Parts or Scripts in the same Historical Item, as well as across different Historical items.

Note that a Hand and a Scribe are both associated with a date and place. This is to accommodate the mobility of scribes (e.g. a scribe can be primarily associated with a given location but may have written a particular Hand somewhere else), and also to allow a chronology of a scribe's work during his or her lifetime. 

# The Graph and the Annotation
simplified diagram of the annotation and graph (and related entities) with definition of the concepts and an illustration

# More complete specification
For people who are interested to know the list of fields, etc.


* Attach a more complete diagram
* Link to the django model source code
* Link to the API documentation

 

_Peter Stokes and Geoffroy Noel_

