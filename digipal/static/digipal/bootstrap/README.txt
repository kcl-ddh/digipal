Bootstrap source code for compiling the stylesheets.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! ONLY dpbootstrap.less CAN BE EDITED. !
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

The styles are converted dynamically to CSS by django compressor.

To customise the styles for all DigiPal instances, edit less/dpbootstrap.less

To customise the styles for a specific DigiPal instance, override dpbootstrap.less
by copying it into your project static folder (with the same relative path).
 
To upgrade Bootstrap, download the source code, and copy the less folder over
the existing one here. Edit dpbootstrap.less by pasting variables.less
followed by pasting bootstrap.less (without @import "variables.less"). Then
edit the values of the variables to customise the appearance of the site.

See http://getbootstrap.com/customize/ for explanations about the variables.

