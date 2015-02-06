tinymce.PluginManager.add('panelset', function(editor, url) {
    
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
    
    // Expansion
    // http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-expan.html
    editor.addButton('psexpansion', {
        text: '()',
        tooltip: 'Expansion of abbreviation',
        icon: false,
        onclick: function() {
            if (editor.selection.isCollapsed()) return;
            var parents = getSelectionParents();
            if (parents[0] !== parents[1]) return;
            var sel_cont = editor.selection.getContent();
            if (sel_cont.match(/^\s*$/g)) return;
            if (sel_cont.match(/</g)) return;
            
            // TODO: keep spaces outside the newly created span
            editor.selection.setContent('<span data-dpt="expan">' + sel_cont + '</span>');
        }
    });

    // Expansion
    // http://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-expan.html
    editor.addButton('psclear', {
        text: '\u274C',
        tooltip: 'Clear Markup',
        icon: false,
        onclick: function() {
            // remove parent tags
            // TODO: don't remove non data-dpt?
            var parents = getSelectionParents();
            $(parents).each(function (index, parent) {
                // don't remove second parent if same as first
                if ((index == 0) || (parents[0] !== parents[1])) {
                    console.log('remove');
                    console.log(parent);
                    // make sure we remove only data-dpt parents and not any parent element
                    var $panelset_parent = $(parent).closest('[data-dpt]');
                    $panelset_parent.replaceWith($panelset_parent.html());
                }
            });
            
            if (!editor.selection.isCollapsed()) {
                // TODO: remove all the data-dpt elements inside the selection
                var sel_cont = editor.selection.getContent();
                sel_cont = sel_cont.replace(/<[^>]*>/g, '');
                editor.selection.setContent(sel_cont);
                //ed.selection.moveToBookmark(bm);
            }
        }
    });

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
    
});