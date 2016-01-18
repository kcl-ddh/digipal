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
        return [0, 1].map(function(i) {
            var bm = editor.selection.getBookmark();
            // move to one end of the selection
            editor.selection.collapse(i === 1);
            var ret = editor.selection.getNode().parentNode;
            editor.selection.moveToBookmark(bm);
            return ret;
        });
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
        }
        
        var parts = sel_cont.match(/^(\s*)(.*?)(\s*)$/);
        
        var tag = isDiv ? 'div' : 'span';
        var newContent = parts[1] + '<'+tag+' data-dpt="' + options.tag + '" ' + attrStr + '>' + parts[2] + '</'+tag+'>' + parts[3];
        setContent(newContent);
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
                if ((index === 0) || (parents[0] !== parents[1])) {
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
    
    function insertClauseOnSelectedDropdownOption(selectedValue) {
        return insertSpanOnSelectedDropdownOption(selectedValue, 'clause', 'words');
    }

    function insertPersonOnSelectedDropdownOption(selectedValue) {
        return insertSpanOnSelectedDropdownOption(selectedValue, 'person', 'chars');
    }

    function insertSpanOnSelectedDropdownOption(selectedValue, tag, cat) {
        addSpan({'tag': tag, 'attributes': {'cat': cat, 'type': selectedValue}, 'conditions': {'isparent': null}});
    }

    /*
    * Adds a drop down to the editor toolbar
    *
    *   buttonid: dropdown identifier/key
    *   items: [{text: 'my first option', value: 'first_option'}, ...]
    *       (if value ommitted, it is derived from the text)
    *       also accepts a comma separated list of labels
    *       also accepts an aray of labels
    *   label: a label for the drop down
    *   tooltip: (optional, default = label)
    *   onSelectFunction(selected_option_value): select option event handler
    */
    function addDropDown(buttonid, items, label, tooltip, onSelectFunction) {
        editor.addButton(buttonid, function() {
            tooltip = tooltip || label;
            
            // 'a,b,c' => 'a', 'b', 'c'
            if (items.split) {
                items = items.split(',');
            }
    
            // [] => {}
            if (items.map) {
                items = items.map(function(obj) {return {'text': obj};});
            }

            // add missing .value
            for (var i in items) {
                items[i].value = items[i].value || items[i].text.toLowerCase();
            }
            
            return {
                type: 'listbox',
                text: label,
                tooltip: tooltip,
                values: items,
                fixedWidth: true,
                onclick: function(e) {
                    if (e.target.tagName !== 'BUTTON' && $(e.target).parent()[0].tagName != 'BUTTON') {
                        onSelectFunction(e.control.settings.value);
                    }
                }
            };
        });
    }
    
    // Locations
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
    addDropDown('psclause', 'Address,Disposition,Witnesses', 'Main Clauses', null, insertClauseOnSelectedDropdownOption);

    // Other Clauses
    addDropDown('psClauseSecondary', 'Arenga,Boundaries,Holding,Injunction,Malediction,Narration,Notification,Prohibition,Salutation,Sealing,Subscription,Title,Warrandice', 'Other Clauses', null, insertClauseOnSelectedDropdownOption);

    // Person
    addDropDown('psperson', 'Title,Name', 'Person', null, insertPersonOnSelectedDropdownOption);

    // Place
    //addDropDown('psplace', 'Name', null, insertClauseOnSelectedDropdownOption);

    // H1
    editor.addButton('psh1', {
        text: 'H1',
        tooltip: 'Heading 1',
        /* icon: 'strikethrough', */
        onclick: function() {
            var sel_cont = editor.selection.getContent();
            if (sel_cont.indexOf('</p>') > -1) {
                sel_cont = sel_cont.replace(/>(\d+\.?\s+[^<]{3,65})<\/p/gi, '><span data-dpt="heading" data-dpt-cat="words" data-dpt-level="1">$1</span></p');
                setContent(sel_cont);
            } else {
                addSpan({'tag': 'heading', 'attributes': {'cat': 'words', 'level': '1'}});
            }
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
    
    // Hand
    // http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-del.html
    editor.addButton('pshand', {
        text: 'Hand',
        tooltip: 'The name of a hand. e.g. alpha',
        onclick: function() {
            addSpan({'tag': 'record', 'attributes': {'model': 'hand'}});
        }
    });
    
    // -------------------------------------------------------------------
    // CODICOLOGY
    
    editor.addButton('pspgside', {
        text: 'Side',
        tooltip: 'Page side (Hair, Flesh)',
        onclick: function() {
            addSpan({'tag': 'page_side', 'attributes': {'cat': 'chars'}});
        }
    });
    
    editor.addButton('pspgdimensions', {
        text: 'Dims',
        tooltip: 'The dimensions of the page (e.g. 25.1 cm x 15.6 cm)',
        onclick: function() {
            addSpan({'tag': 'page_dimensions', 'attributes': {'cat': 'chars'}});
        }
    });

    editor.addButton('pspgcolour', {
        text: 'Colour',
        tooltip: 'The colour of the page',
        onclick: function() {
            addSpan({'tag': 'page_colour', 'attributes': {'cat': 'chars'}});
        }
    });

    // -------------------------------------------------------------------
    // Codicology
    /*
            object="perforation" property="count"
            object="perforation" property="shape"
            object="perforation" property="location"
            object="column" property="count"
            object="written-block" property="size"
            object="ruling" property="size"
            object="ruling" property="count"
            object="ruling" property="distance"
            object="ruling" property="method"
            object="page" property="color"
            
            object="quire|folio|line|page-area|side" property="location"
    */
    

    var cods = [
                {text: 'Perforations count', value: '1', attrs: {'object':'perforation', 'property':'count'}, },
                {text: 'Perforation shape', value: '2', attrs: {'object':'perforation', 'property':'shape'}, },
                {text: 'Perforation location', value: '3', attrs: {'object':'perforation', 'property':'location'}, },

                {text: 'Size of ruled area', value: '7', attrs: {'object':'ruling', 'property':'count'}, },
                {text: 'Number of ruled lines', value: '7', attrs: {'object':'ruling', 'property':'count'}, },
                {text: 'Distance between ruled lines', value: '8', attrs: {'object':'ruling', 'property':'distance'}, },
                {text: 'Ruling method', value: '9', attrs: {'object':'ruling', 'property':'method'}, },

                {text: 'Signature location', value: '7', attrs: {'object':'signature', 'property':'location'}, },
                {text: 'Signature label', value: '7', attrs: {'object':'signature', 'property':'label'}, },
                {text: 'Signature appearance', value: '8', attrs: {'object':'signature', 'property':'appearance'}, },

                {text: 'Foliation location', value: '7', attrs: {'object':'foliation', 'property':'location'}, },
                {text: 'Foliation label', value: '7', attrs: {'object':'foliation', 'property':'label'}, },
                {text: 'Foliation appearance', value: '8', attrs: {'object':'foliation', 'property':'appearance'}, },

                {text: 'Bifolium conjoint', value: '4', attrs: {'object':'bifolium', 'property':'conjoint'}, },
                {text: 'Quire number', value: '5', attrs: {'object':'quire', 'property':'number'}, },
                {text: 'Column count', value: '6', attrs: {'object':'column', 'property':'count'}, },
                {text: 'Column size', value: '6', attrs: {'object':'column', 'property':'size'}, },
                
                {text: 'Parchment color', value: '10', attrs: {'object':'parchment', 'property':'color'}, },
                {text: 'Parchment side', value: '11', attrs: {'object':'parchment', 'property':'side'}, },
                {text: 'Parchment size', value: '12', attrs: {'object':'parchment', 'property':'size'}, }
                ];
    
    function addButton(aitems, button_key, button_label, filters) {
    
        editor.addButton(button_key, function() {
        
            var items = [];
            for (var i in aitems) {
                var aitem = aitems[i];
                if (filters.indexOf(aitem.attrs.object) > -1) {
                    items.push(aitem);
                }
            }
        
            return {
                type: 'listbox',
                text: button_label,
                values: items,
                fixedWidth: true,
                onclick: function(e) {
                    if (e.target.tagName !== 'BUTTON' && $(e.target).parent()[0].tagName != 'BUTTON') {
                        var settings = e.control.settings;
                        addSpan({'tag': 'codesc', 'attributes': settings.attrs});
                        editor.focus();
                    }
                }
            };
        });
        
    }
    
    addButton(cods, 'pscodperf', 'Perforation', ['perforation']);
    addButton(cods, 'pscodruling', 'Ruling', ['ruling']);
    addButton(cods, 'pscodsign', 'Signature', ['signature']);
    addButton(cods, 'pscodfol', 'Foliation', ['foliation']);
    addButton(cods, 'pscodparch', 'Parchment', ['parchment']);
    addButton(cods, 'pscodothers', 'Codicology (other)', ['quire', 'bifolium', 'column']);

    // -------------------------------------------------------------------

    // Hand
    // http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-del.html
    editor.addButton('psgraph', {
        text: 'Annotation',
        tooltip: 'The ID of an annotation to include in the description. e.g. #101 to include Annotation 101.',
        onclick: function() {
            addSpan({'tag': 'record', 'attributes': {'model': 'graph'}});
        }
    });

    // Stints
    editor.addButton('psstint', {
        text: 'Stint',
        tooltip: 'Folio range(s) for one or more stints by this hand only. e.g. 350v20-1r13',
        onclick: function() {
            if (!editor.selection.isCollapsed()) {
                var sel_cont = editor.selection.getContent();
                sel_cont = sel_cont.replace(/(OF\s*)?\b(\d{1,4}(r|v))[^\s;,\]<]*/g,
                            function($0, $1){
                                return $1 ? $0+$1 : '<span data-dpt="stint" data-dpt-cat="chars">'+$0+'</span>';
                            }
                        );
                setContent(sel_cont);
            }
        }
    });
    
    editor.addButton('pscharacter', {
        text: 'Character',
        tooltip: 'A character. e.g. b',
        onclick: function() {
            if (!editor.selection.isCollapsed()) {
                var sel_cont = editor.selection.getContent();
                if (sel_cont.indexOf('</p>') > -1) {
                    var l = 0;
                    while (true) {
                        l = sel_cont.length;
                        sel_cont = sel_cont.replace(/(>[^<]*\s|>)([bcdefghjklmnopqrstuvwxyz]|Gallow'?s mark|et nota|e cauda)\b(?!<\/span)/gi, '$1<span data-dpt="record" data-dpt-model="character">$2</span>');
                        if (l == sel_cont.length) break;
                    }
                    
                    setContent(sel_cont);
                } else {
                    addSpan({'tag': 'record', 'attributes': {'model': 'character'}});
                }
            }
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

            //console.log((parents[0] === parents[1]) ? 'Same parent' : 'Different parents');
            //console.log(parents);

            // check that the selection doesn't contain fragmentary elements.
            // e.g. '1</span>2' or '1<span>2'
            var yo = 0;
            
            //editor.insertContent('<br/>');
        }
    });
    
};

window.tinymce.PluginManager.add('panelset', PanelSetPlugIn);
