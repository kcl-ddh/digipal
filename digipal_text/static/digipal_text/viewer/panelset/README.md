INTRO

The Text Viewer/Editor client application

PanelSet is a frame made of multiple views on a document (ItemPart). 
Each view is managed by a separate Panel object.
Panel subclasses deal with specific types of contents:
e.g. PanelText for XML, PanelImage for tiled high res image, etc.

CLASS DESIGN

PanelSet: manages multiple Panel objects

Located:  a location aware object (ABSTRACT)
    
    Panel: a visual panel showing one view over a piece of the document (ABSTRACT)
    
        PanelText: XML/HTML content
        PanelImage: Highres Image from image server 
        PanelSearch: Text search & result 
        PanelLocation: master location widget

TODO
----

UI improvements
    [DONE] panels sync'ed across browser windows
    [DONE] too many buttons
        show only essentials, only show the rest when hover
    [DONE] *** change the sync to a master location
        [DONE] add LT and L drop downs to top bar
        ()populate-merge them after all panels are loaded
        ()populate-merge after a panel type change
        [DONE] change in LT
        [DONE] change in L
        [DONE] add sync button to other panels
        [DONE] use cases
            http://localhost:8080/digipal/manuscripts/1/texts/view/locus/8r/
                => must load 8r in master location
                => load 8r in all panels
        ()improve auto-complete
        [DONE] add location on top
        [DONE] when synced, hidden location in panel
    
    ** Master location improvements
        panels can be synced + 1 or  -1
        by default the panels are synced with it
        hide location type if only one option (MOA)
        can then implement the scrolling to next unit
        bi-dir synced

    ** page navigation:
        [DONE] easier navigation to prev/next page
        scrolling
    * TOC
        use TOC to navigate?
        show detailed location (e.g. Count of Mortain, Somerset, Hand)
        
    ** image
        auto frame to page
        can auto frame to <->
        can auto-frame to |
    ** expandable panels
    
    frame ratio preserved when resizing the viewport
    status bar
        hide it x seconds after a successful message has been displayed
    the sync UI is not intuitive: the name of the source can be confused with
        the type of content in the panel
    
    () improve the search
        search in different texts
        search across corpus?

        
// TODO: Create a new class PanelContent that inherit from Panel and has a content,
// status bar, etc. Move all the relevant methods from Panel to PanelContent
// Then PanelImage, PanelText, etc would inherit from that new class
// But PanelLocation would inherit from Panel directly
        