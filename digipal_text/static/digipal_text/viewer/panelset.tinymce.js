var PanelSetPlugIn = function(editor, url) {
    
    var $ = jQuery;
    
    this.dpmup = {
        'psex': {'tooltip': 'Expansion of abbreviation', 'text': '()', 'cat': 'chars'}, 
    };
    
    function beforeChange() {
        //editor.undoManager.add();
    }
    
    function afterChange(cancel) {
        if (!cancel) {
            editor.undoManager.add();
            //editor.undoManager.redo();
        }
    }
    
    function setContent(content) {
        beforeChange();
        //editor.undoManager.transact(function () { editor.selection.setContent(content); });
        content = content.replace(/<p>\s*(&nbsp;)?\s*<\/p>/g, '');
        editor.selection.setContent(content);
        afterChange();
    }
    
    function getSelectionParents() {
        var parents = [];
        for (var i in [0, 1]) {
            var bm = editor.selection.getBookmark();
            // move to one end of the selection
            editor.selection.collapse(i == 0);
            parents.push(editor.selection.getNode().parentNode);
            editor.selection.moveToBookmark(bm);
        }
        return parents;
    }
    
    // Add a button that opens a window
    editor.addButton('pslinebreak', {
        text: 'Line Break',
        icon: false,
        onclick: function() {
            if (!editor.selection.isCollapsed()) return;
            editor.insertContent('<br/>');
        }
    });

    // Add a button that opens a window
    editor.addButton('psconvert', {
        /*text: '\u267B',*/
        text: '\u27F4',
        tooltip: 'Auto mark-up',
        icon: false,
        onclick: function() {
            $(editor.editorContainer).trigger('psconvert');
        }
    });

    // Add a button that opens a window
    editor.addButton('pssave', {
        /*text: '',*/
        tooltip: 'Save',
        icon: 'save',
        onclick: function() {
            $(editor.editorContainer).trigger('pssave');
        }
    });
    
    function addSpan(options, isDiv) {
        // options
        //  tag: element name
        //  attributes: {'name': 'val'}
        //  conditions: {'collapsed': false, 'overlap': false, 'isparent': false, 'blank': false}
        //  processing: {'keep_spaces': false}
        options.conditions = options.conditions || {};
        options.conditions = $.extend({'collapsed': false, 'overlap': false, 'isparent': false, 'blank': false}, options.conditions);
        var conds = options.conditions;
        if ((conds.collapsed !== null) && (conds.collapsed !== editor.selection.isCollapsed())) return;
        var parents = getSelectionParents();
        if ((conds.overlap !== null) && (conds.overlap !== (parents[0] !== parents[1]))) return;
        var sel_cont = editor.selection.getContent();
        if ((conds.blank !== null) && (conds.blank !== (sel_cont.match(/^\s*$/g) !== null))) return;
        if ((conds.isparent !== null) && (conds.isparent !== (sel_cont.match(/</g) !== null))) return;
        
        // TODO: keep spaces outside the newly created span
        options.attributes = options.attributes || {};
        var attrStr = '';
        for (var k in options.attributes) {
            attrStr += ' data-dpt-'+k+'="'+options.attributes[k]+'"';
        };
        
        var parts = sel_cont.match(/^(\s*)(.*?)(\s*)$/);
        
        var tag = isDiv ? 'div' : 'span';
        setContent(parts[1] + '<'+tag+' data-dpt="' + options.tag + '" ' + attrStr + '">' + parts[2] + '</'+tag+'>' + parts[3]);
    }
    
    // Expansion
    // http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-expan.html
    editor.addButton('psex', {
        text: '()',
        tooltip: 'Expansion of abbreviation',
        icon: false,
        onclick: function() {
            addSpan({'tag': 'ex', 'attributes': {'cat': 'chars'}});
        }
    });

    // Supplied
    editor.addButton('pssupplied', {
        text: '\u271A',
        tooltip: 'Supplied text',
        icon: false,
        onclick: function() {
            addSpan({'tag': 'supplied', 'attributes': {'cat': 'chars'}});
        }
    });

    // Deleted
    // http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-del.html
    editor.addButton('psdel', {
        /* text: '\u271A', */
        tooltip: 'Deleted',
        icon: 'strikethrough',
        onclick: function() {
            addSpan({'tag': 'del', 'attributes': {'cat': 'words'}, 'conditions': {'isparent': null}});
        }
    });

    // Clear the markup
    // Clear digipal elements within or directly above the selection 
    editor.addButton('psclear', {
        text: '\u274C',
        tooltip: 'Clear Markup',
        icon: false,
        onclick: function() {
            // remove parent tags
            // TODO: don't remove non data-dpt?
            var parents = getSelectionParents();
            
            var changed = false;
            
            beforeChange();

            $(parents).each(function (index, parent) {
                // don't remove second parent if same as first
                if ((index == 0) || (parents[0] !== parents[1])) {
                    // make sure we remove only data-dpt parents and not any parent element
                    var $panelset_parent = $(parent).closest('[data-dpt]');
                    $panelset_parent.replaceWith($panelset_parent.html());
                    // TODO: not exact... $panelset_parent can be empty
                    changed = true;
                    afterChange(!changed);
                }
            });
            
            if (!editor.selection.isCollapsed()) {
                // TODO: remove all the data-dpt elements inside the selection
//                var sel_cont = editor.selection.getContent();
//                sel_cont = sel_cont.replace(/<[^>]*>/g, '');
//                editor.selection.setContent(sel_cont);
                var $selection = $('<div>'+editor.selection.getContent()+'</div>');
                $selection.find('[data-dpt]').each(function (i, el) {
                    $(el).replaceWith($(el).html());
                });
                
                setContent($selection.html());
                changed = true;
            }
        }
    });
    
    // Clauses
    editor.addButton('pslocation', function() {
        var items = [{text: 'Locus', value: 'locus'}, {text: 'Entry', value: 'entry'}, {text: 'Section', value: 'section'}];
    
        return {
            type: 'listbox',
            text: 'Location',
            tooltip: 'Location',
            values: items,
            fixedWidth: true,
            onclick: function(e) {
                if (e.target.tagName !== 'BUTTON' && $(e.target).parent()[0].tagName != 'BUTTON') {
                    addSpan({'tag': 'location', 'attributes': {'loctype': e.control.settings.value}});
                }
            }
        };
    });
    
    // Clauses
    editor.addButton('psclause', function() {
        var items = [{text: 'Address', value: 'address'}, {text: 'Disposition', value: 'disposition'}, {text: 'Witnesses', value: 'witnesses'}];
    
        return {
            type: 'listbox',
            text: 'Clause',
            tooltip: 'Clause',
            values: items,
            fixedWidth: true,
            onclick: function(e) {
                if (e.target.tagName !== 'BUTTON' && $(e.target).parent()[0].tagName != 'BUTTON') {
                    addSpan({'tag': 'clause', 'attributes': {'cat': 'words', 'type': e.control.settings.value}});
                }
            }
        };
    });

    // H1
    editor.addButton('psh1', {
        text: 'H1',
        tooltip: 'Heading 1',
        /* icon: 'strikethrough', */
        onclick: function() {
            addSpan({'tag': 'heading', 'attributes': {'cat': 'words', 'level': '1'}});
        }
    });

    // H2
    editor.addButton('psh2', {
        text: 'H2',
        tooltip: 'Heading 2',
        /* icon: 'strikethrough', */
        onclick: function() {
            addSpan({'tag': 'heading', 'attributes': {'cat': 'words', 'level': '2'}});
        }
    });
    
    // Stints
    editor.addButton('psstints', {
        text: 'Stints',
        tooltip: 'Folio range for one or more stints by this hand only. e.g. 350v20-1r13',
        /* icon: 'strikethrough', */
        onclick: function() {
            if (!editor.selection.isCollapsed()) {
                var sel_cont = editor.selection.getContent();
                sel_cont = sel_cont.replace(/(OF\s*)?\b(\d{1,4}(r|v))[^\s;,\]<]*/g, 
                            function($0, $1){
                                return $1 ? $0+$1 : '<span data-dpt="stint" data-dpt-cat="words">'+$0+'</span>';
                            }
                        );

                setContent(sel_cont);
            }
            //addSpan({'tag': 'stint', 'attributes': {'cat': 'words'}});
        }
    });
    
//    editor.addButton('psstints', {
//        text: 'Stints',
//        tooltip: 'A block containing stints ranges.',
//        /* icon: 'strikethrough', */
//        onclick: function() {
//            addSpan({'tag': 'stints', 'attributes': {'cat': 'paragraphs'}, 'conditions': {'isparent': null}}, true);
//        }
//    });
    
    // Heading
//    editor.addButton('psheading', function() {
//        var items = [{text: 'Heading 1', value: 'h1'}, {text: 'Heading 2', value: 'h2'}];
//    
//        return {
//            type: 'listbox',
//            text: 'Heading',
//            tooltip: 'Heading',
//            values: items,
//            fixedWidth: true,
//            onclick: function(e) {
//                if (e.target.tagName !== 'BUTTON' && $(e.target).parent()[0].tagName != 'BUTTON') {
//                    addSpan({'tag': 'heading', 'attributes': {'cat': 'words', 'type': e.control.settings.value}});
//                }
//            }
//        };
//    });
    
    // Paragraph merger
    editor.addButton('psparagraph', {
        text: 'Merge Paragraphs',
        icon: false,
        onclick: function() {
            if (editor.selection.isCollapsed()) return;

            var parents = getSelectionParents();
            
            // get the p above each parent
            // make sure the 

            console.log((parents[0] === parents[1]) ? 'Same parent' : 'Different parents');
            console.log(parents);

            // check that the selection doesn't contain fragmentary elements.
            // e.g. '1</span>2' or '1<span>2'
            var yo = 0;
            
            //editor.insertContent('<br/>');
        }
    });
    
};

tinymce.PluginManager.add('panelset', PanelSetPlugIn);
