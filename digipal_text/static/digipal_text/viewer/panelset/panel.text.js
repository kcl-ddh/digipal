//////////////////////////////////////////////////////////////////////
//
// PanelText: read-only text/XML/HTML panel
//
// PanelTextWrite: editable text/XML/HTML panel
//
//////////////////////////////////////////////////////////////////////
(function(TextViewer, $, undefined) {

    //////////////////////////////////////////////////////////////////////
    //
    // PanelText
    //
    // A read-only Text Viewer panel. The content is simply displayed as HTML.
    //
    //////////////////////////////////////////////////////////////////////
    var PanelText = TextViewer.PanelText = function($root, contentType, options) {
        TextViewer.Panel.call(this, $root, contentType, 'Text', options);
        var me = this;

        this.editingMode = false;
        
        this.loadContentCustom = function(loadLocations, address, subLocation) {
            // load the content with the API
            var me = this;
            this.callApi(
                'loading content',
                address,
                function(data) {
                    if (data.content !== undefined) {
                        me.onContentLoaded(data);
                    } else {
                        //me.setMessage('ERROR: no content received from server.');
                    }
                },
                {
                    'load_locations': loadLocations ? 1 : 0,
                }
            );
        };

        this.$content.on('mouseup', function(e) {
            if (!me.getEditingMode()) {
                // find the dpt element we've just clicked on
                var subLocation = TextViewer.get_sublocation_from_element(e.target);

                if (subLocation.length) {
                    me.setSubLocation(subLocation);
                    // dispatch the element we are on
                    //me.panelSet.syncWithPanel(me);
                }
            }
        });

    };

    PanelText.prototype = Object.create(TextViewer.Panel.prototype);

    PanelText.prototype.onContentLoaded = function(data) {
        this.$content.addClass('mce-content-body').addClass('preview ct-'+this.getContentType());
        this.$content.html(data.content);
        TextViewer.Panel.prototype.onContentLoaded.call(this, data);
    };

    PanelText.prototype.isDownloadable = function() {
        return true;
    };


    //////////////////////////////////////////////////////////////////////
    //
    // PanelTextWrite
    //
    // A Text Editor panel. The content is managed with TinyMCE.
    // Can save modified content back to server.
    //
    //////////////////////////////////////////////////////////////////////
    TextViewer.textAreaNumber = 0;

    var PanelTextWrite = TextViewer.PanelTextWrite = function($root, contentType, options) {
        TextViewer.PanelText.call(this, $root, contentType, options);

        this.unreadyComponents.push('tinymce');

        this.editingMode = true;

        // TODO: fix with 'proper' prototype inheritance
        this.baseOnResize = this.onResize;
        this.onResize = function () {
            this.baseOnResize();
            if (this.tinymce) {
                // resize tinmyce to take the remaining height in the panel
                var $el = this.$root.find('iframe');
                var height = this.$content.innerHeight() - ($el.offset().top - this.$content.offset().top);
                $el.height(height+'px');
            }
        };

        this.getContentHash = function() {
            var ret = this.tinymce.getContent();
            return ret;
            //return ret.length + ret;
        };

        this.saveContentCustom = function(options) {
            // options:
            // synced, autoMarkup, saveCopy
            var me = this;
            this.callApi(
                'saving content',
                this.loadedAddress,
                function(data) {
                    //me.tinymce.setContent(data.content);
                    me.onContentSaved(data);
                    if (options.autoMarkup) {
                        me.tinymce.setContent(data.content);
                        me.setNotDirty();
                    }
                },
                {
                    'content': me.tinymce.getContent(),
                    'convert': options.autoMarkup ? 1 : 0,
                    'save_copy': options.saveCopy ? 1 : 0,
                    'method': 'POST',
                },
                options.synced
            );
        };

        this.initTinyMCE = function() {
            TextViewer.textAreaNumber += 1;
            var divid = 'text-area-' + TextViewer.textAreaNumber;
            this.$content.append('<div id="'+ divid + '"></div>');
            var me = this;
            
            var text_editor_options = window.text_editor_options;

            var v = Math.floor(Date.now() / 1000);
            var static_path = '/static/digipal_text/viewer/';

            var options = {
                skin : 'digipal',
                selector: '#' + divid,
                init_instance_callback: function() {
                    me.tinymce = window.tinyMCE.get(divid);
                    me.componentIsReady('tinymce');
                },
                plugins: ['paste', 'code', 'panelset'],
                toolbar: text_editor_options.toolbars[me.contentType] || text_editor_options.toolbars.default,
                paste_word_valid_elements: 'i,em,p,span',
                paste_postprocess: function(plugin, args) {
                    //args.node is a temporary div surrounding the content that will be inserted
                    //console.log($(args.node).html());
                    //$(args.node).html($(args.node).html().replace(/<(\/?)p/g, '<$1div'));
                    //console.log($(args.node).html());
                },
                menubar : false,
                statusbar: false,
                height: '15em',
                content_css : static_path + 'tinymce.css?v='+v+
                    ','+static_path+'tinymce_custom.css?v='+v+
                    ',/digipal/manuscripts/1/texts/view/tinymce_generated.css?v='+v
            };

            if (this.contentType == 'codicology') {
                // move thst to Exon project
                options.toolbar = 'psclear undo redo pssave | psh1 psh2 | italic | pshand | pscodparch pscodfol pscodsign pscodperf pscodruling pscodothers | code';
                options.paste_as_text = true;
                options.paste_postprocess = function(plugin, args) {
                    //args.node is a temporary div surrounding the content that will be inserted
                    //console.log($(args.node).html());
                    //$(args.node).html($(args.node).html().replace(/<(\/?)p/g, '<$1div'));
                    //console.log($(args.node).html());
                    //console.log(args.node);

                    // remove all tags except <p>s
                    var content = $(args.node).html();
                    content = content.replace(/<(?!\/?p(?=>|\s.*>))\/?.*?>/gi, '');
                    // remove attributes from all the elements
                    content = content.replace(/<(\/?)([a-z]+)\b[^>]*>/gi, '<$1$2>');
                    // remove &nbsp;
                    content = content.replace(/&nbsp;/gi, '');
                    // remove empty elements
                    content = content.replace(/<[^>]*>\s*<\/[^>]*>/gi, '');
                    $(args.node).html(content);
                };
            }

            window.tinyMCE.init(options);

        };

        this.initTinyMCE();
    };

    PanelTextWrite.prototype = Object.create(PanelText.prototype);

    PanelTextWrite.prototype._ready = function() {
        var ret = PanelText.prototype._ready.call(this);
        
        var me = this;

        $(this.tinymce.editorContainer).on('psconvert', function() {
            // mark up the content
            // TODO: make sure the editor is read-only until we come back
            me.saveContent({forceSave: true, autoMarkup: true});
        });

        $(this.tinymce.editorContainer).on('pssave', function() {
            // mark up the content
            // TODO: make sure the editor is read-only until we come back
            me.saveContent({forceSave: true, saveCopy: true});
        });

        // make sure we save the content if tinymce looses focus or we close the tab/window
        this.tinymce.on('blur', function() {
            me.saveContent();
        });

        $(window).bind('beforeunload', function() {
            me.saveContent({synced: true});
        });

        return ret;
    };

    PanelTextWrite.prototype.onContentLoaded = function(data) {
        this.tinymce.setContent(data.content);

        this.tinymce.focus();
        this.tinymce.undoManager.clear();
        this.tinymce.undoManager.add();
        // We skip PanelText
        TextViewer.Panel.prototype.onContentLoaded.call(this, data);
    };

    PanelTextWrite.prototype.scrollToTopOfContent = function(data) {
        if (this.tinymce) this.tinymce.getBody().firstChild.scrollIntoView();
    };

}( window.TextViewer = window.TextViewer || {}, jQuery ));
