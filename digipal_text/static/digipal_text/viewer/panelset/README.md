Introduction
============

The Text Viewer/Editor client application

PanelSet is a frame made of multiple views on a document (ItemPart). 
Each view is managed by a separate Panel object.
Panel subclasses deal with specific types of contents:
e.g. PanelText for XML, PanelImage for tiled high res image, etc.

Inner Working
=============

Class Design
------------

* __PanelSet__: manages multiple Panel objects
* __Located__:  a location aware object (ABSTRACT)
    * __Panel__: a visual panel showing one view over a piece of the document (ABSTRACT)
        * __PanelText__: XML/HTML content
        * __PanelImage__: Highres Image from image server 
        * __PanelSearch__: Text search & result 
        * __PanelLocation__: master location widget

This design is easily extensible as a lot of the general logic is 
taken care by the Panel class. So subclasses can concentrate on content
loading & displaying (and perhaps editing and saving as well).

Each Panel SHOULD be unaware of other panels and panel types. Inter-panel
communication and relationships are managed by the PanelSet.

Workflow
--------

* The User selects a different folio number in the drop-down.
* A Panel sends the requested (locationType, location) to the server.
* A content-type specific part of the API returns the relevant content and metadata (in JSON).
* Servers can also correct the location (e.g. ask for 'default', returns '1r').
* The Panel updates its content and the location dropdowns accordingly.
* This change is dispatched to other Panels so they can sync their location/content.

Layout
------

The PanelSet object creates and manages the multi-panel layout. The layout is 
based on jquery layout plugin. It allows up to 5 panels to be displayed like this:

* North
* West | Centre | East
* South

At the moment West and South are hidden, but it is easy to enable in text_viewer.html.

The query string of the URL to the Text Viewer makes use of the panel labels to assign
content types. For instance ?centre=/translation/locus/2r&north=/image/locus/3r/ .

Panel Structure
---------------

The Panel basic HTML structure is cloned from the div id="text-viewer-panel"
in text_viewer.html. It is made of a button bar (for location and content type 
selection), a content area and a status bar at the bottom.

Most of the Panel state is actually left in the value of the HTML controls on the 
button bar. This ensures consistency between the Panel behaviour and its appearance.

When a Panel is instantiated, the object will just keep jQuery handles pointing to 
the individual controls. 

Locations
---------

Every piece of content has a location. It is expressed with at least a pair: 
(locationType, location). E.g. ('locus', '2r') or ('entry', '2a2').

It can also be expressed as a path: 
'/digipal/manuscripts/ITEMPART_ID/texts/CONTENT_TYPE/LOC_TYPE/LOCATION/'
e.g. '/digipal/manuscripts/1/texts/translation/locus/2r/'

You can create your own location types if you wish.

Special location types:
* __whole__: the whole content (e.g. the entire text)
* __default__: let server decide an initial location type and location for the user
* __sync__: a way to sync the panel with another content type. The location of that panel is the content type to sync with. e.g. /image/sync/transcription/ means that the image panel is synced with the transcription.

### Selected and Content locations

It is important to understand the distinction between the __selected location__ and the __content location__.
The selected location is displayed in the location drop downs at the top of a panel.
Say, if you select 'entry', '2a3' in the dropdown of your image panel, it will
request those to the server. Which will return image and 'locus', '2r' because 
entry 2a3 is found on that image. The panel will still show 'entry', '2a3' but,
internally, the panel knows that the content location is actually 'locus', '2r'.

This distinction also applies to sync'ed panels.

Panel.loadedAddress stores the content location, whereas Panel.getLocationType() and Panel.getLocation()
return the selected location. 

### Sub-location

The content returned can be more than the requested location but not less.
A fragment of the content can also be addressed by specifying the __SUBLOCATION__.
For instance a person name in the current text/image.

A Panel can reframe its content to display the desired sublocation 
(e.g. scrolling, highlight, panning and zooming).

State
-----

The state of each Panel is visible in the query string. The state contains
the address, the sublocation and display settings (also called 'presentation options').

When it is instantiated, the PanelSet parses the Query String, extract the
state, create the relevant Panels from it and then dispatch the Panel state
to each panel so they can restore their own state.

TODO
====

UI improvements
---------------

* !! image
    * auto frame to page
    * can auto frame to <->
    * can auto-frame to |

* !! expandable panels

* !! page navigation:
    * [DONE] easier navigation to prev/next page
    * scrolling

* !! Master location improvements
    [DONE] by default the panels are synced with it
    [DONE] panels can be synced + 1 or  -1
    * hide location type if only one option (MOA)
    * ! bi-dir synced: important otherwise the
    * panels can be synced + 1 or -1 across browser windows 

* TOC
    * use TOC to navigate?
    * show detailed location (e.g. Count of Mortain, Somerset, Hand)
    
* frame ratio preserved when resizing the viewport
* status bar
    * hide it x seconds after a successful message has been displayed
* the sync UI is not intuitive: the name of the source can be confused with
    * the type of content in the panel

* () improve the search
    * search in different texts
    * search across corpus?

Focus memory
    any change in the (master) location should return focus to last focused panel

DONE
====
        
* ! [DONE] panels sync'ed across browser windows
* [DONE] too many buttons
    * ! show only essentials, only show the rest when hover
* [DONE] !!! change the sync to a master location
    * ! [DONE] add LT and L drop downs to top bar
    * ()populate-merge them after all panels are loaded
    * ()populate-merge after a panel type change
    * [DONE] change in LT
    * [DONE] change in L
    * [DONE] add sync button to other panels
    * [DONE] use cases
        * http://localhost:8080/digipal/manuscripts/1/texts/view/locus/8r/
            * => must load 8r in master location
            * => load 8r in all panels
    * ()improve auto-complete
    * [DONE] add location on top
    * [DONE] when synced, hidden location in panel
[DONE] location preserved after changing panel type
[DONE] After Text content loaded, sroll back to the top of the content

// TODO: Create a new class PanelContent that inherit from Panel and has a content,
// status bar, etc. Move all the relevant methods from Panel to PanelContent
// Then PanelImage, PanelText, etc would inherit from that new class
// But PanelLocation would inherit from Panel directly
