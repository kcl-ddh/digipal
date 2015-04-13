jQuery(document).ready(function($) {

    var panelset = new PanelSet();
    panelset.setLayout($('#text-viewer .panels'));
    panelset.setMessageBox($('#text-viewer .message-box'));
    panelset.setExpandButton($('#text-viewer .message-box a'));
    panelset.registerPanel(new PanelTextWrite($('.ui-layout-center')));
    panelset.ready();
    
});
