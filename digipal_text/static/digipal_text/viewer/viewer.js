jQuery(document).ready(function($) {

    var panelset = new PanelSet();
    panelset.setLayout($('#text-viewer .panels'));
    panelset.setMessageBox($('#text-viewer .message-box'));
    panelset.setExpandButton($('#text-viewer .message-box a'));
    panelset.registerPanel(new PanelTextWrite($('.ui-layout-center')));
    panelset.ready();
    
    /*
    function tinymce_ready(ted) {
        //var ted = tinymce.get('text-area');
        
        $('select[name=content_type]').on('change', function() {
            window.location = window.location + $(this).val();
            return false;
        });
       
        // load the text
        function load_text() {
            submit_request('?action=load_text', function(data) {
                ted.setContent(data['text'] || '');
                ted.isNotDirty = true;
            });
        }
        
        function save_text() {
            if (ted.isDirty()) {
                submit_request('?action=save_text', function(data) {
                    ted.isNotDirty = true;
                }, {'text': ted.getContent()});
            }
        }

        function set_message(message, status) {
            $message = $('div.message');
            var date = new Date();
            $message.html(message + '<span class="message-time">(' + date.getHours() + ':'  + date.getMinutes() + ':'  + date.getSeconds() + ')</span>');
            status = 'empty';
            if (message) {
                $message.addClass('message-'+status);
            }
        }

        function submit_request(url, on_success, request_data) {
            // See http://stackoverflow.com/questions/9956255.
            // This tricks prevents caching of the fragment by the browser.
            // Without this if you move away from the page and then click back
            // it will show only the last Ajax response instead of the full HTML page.
            url = url ? url : '';
            var url_ajax = url + ((url.indexOf('?') === -1) ? '?' : '&') + 'jx=1';
            
            
            
            $.get(url_ajax, request_data)
                .success(function(data) {
                    if (on_success) {
                        on_success(data);
                        set_message(data.message, data.status);
                    }
                })
                .fail(function(data) {
                });
        }
        
        load_text();
        
        ted.focus();
        
        setInterval(function() {
            save_text();
        }, 1000);
        
        $('select[name=image_selector]').on('click change', function() {
            var url = $(this).val();
            $('#image-viewer').html('<img src="' + url + '" />');
        });
        
    }    
    
    tinyMCE.init({
        selector: "#text-area",
        init_instance_callback: tinymce_ready,
        plugins: ["paste"],
        toolbar: "undo redo", 
        menubar : false,
        statusbar: false,
        height: '15em',
    });
    */
    
});
