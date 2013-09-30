# Tell South about the iipimage field
# See http://south.readthedocs.org/en/latest/tutorial/part4.html#simple-inheritance
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^iipimage\.fields\.ImageField"])

# patch the iipimage to correct a bug (.image was hardcoded)
from iipimage import storage
from django.conf import settings

import logging
import re
dplog = logging.getLogger( 'digipal_debugger')

# PATCH 1:

# prefix the upload dir with IMAGE_SERVER_ADMIN_UPLOAD_DIR
def generate_new_image_path():
    ret = storage.generate_new_image_path()
    # GN: prefix the path with settings.IMAGE_SERVER_ADMIN_UPLOAD_DIR
    try:
        import os
        ret = os.path.join(settings.IMAGE_SERVER_ADMIN_UPLOAD_DIR, ret)
    except Exception:
        pass
    return ret

# The name of the iipimage field was hardcoded.
# Changed to iipimage to match Page model.
def get_image_path (instance, filename):
    """Returns the upload path for a page image.

    The path returned is a Unix-style path with forward slashes.

    This filename is entirely independent of the supplied `name`. It
    includes a directory prefix of the first character of the UUID and
    a fixed 'jp2' extension.

    Note that the image that `name` is of is most likely not a JPEG
    2000 image. However, even though we're using a UUID, it's worth
    not futzing about with the possibility of collisions with the
    eventual filename. Also, it's more convenient to always be passing
    around the real filename.

    :param instance: the instance of the model where the ImageField is
      defined
    :type instance: `models.Model`
    :param filename: the filename that was originally given to the file
    :type filename: `str`
    :rtype: `str`

    """
    
    if instance.id:
        # Reuse the existing filename. Unfortunately,
        # instance.image.name gives the filename of the image being
        # uploaded, so load the original record.
        original = instance._default_manager.get(pk=instance.id)
        image_path = original.iipimage.name
        if not image_path:
            # While the model instance exists, it previously had no
            # image, so generate a new image path.
            image_path = generate_new_image_path()
        else:
            # The original image file must be deleted or else the save
            # will add a suffix to `image_path`.
            # GN: iipimage
            original.iipimage.delete(save=False)
    else:
        image_path = generate_new_image_path()
    
    return image_path

storage.get_image_path = get_image_path

# PATCH 2:
# subprocess.check_call(shlex.split(command.encode('ascii')))
# Didn't work on Windows. Changed to a cross-platform implementation.

import os

def _call_image_conversion (command, input_path):
    """Run the supplied image conversion `command`.

    Tidy up by removing the original image at `input_path`.

    """
    try:
        #subprocess.check_call(shlex.split(command.encode('ascii')))
        os.system(command.encode('ascii'))
    except subprocess.CalledProcessError, e:
        os.remove(input_path)
        raise IOError('Failed to convert the page image to .jp2: %s' % e)
    finally:
        # Tidy up by deleting the original image, regardless of
        # whether the conversion is successful or not.
        os.remove(input_path)

storage.image_storage._call_image_conversion = _call_image_conversion

from iipimage import fields

# Patch 3:
# The order of the query string arguments do matter, 
# if CVT appears before HEI, the resizing will fail on some iip image server implementations 

def thumbnail_url (self, height=None, width=None):
    try:
        height = '&HEI=%s' % str(int(height))
    except (TypeError, ValueError):
        height = ''
    try:
        width = '&WID=%s' % str(int(width))
    except (TypeError, ValueError):
        width = ''
    return '%s%s%s&CVT=JPEG' % (self.full_base_url, height, width)

fields.ImageFieldFile.thumbnail_url = thumbnail_url


# Patch 4:
# Fix Mezzanine case-insensitive keyword issue
# See https://github.com/stephenmcd/mezzanine/issues/647

if 'mezzanine.blog' in settings.INSTALLED_APPS:
    
    keyword_exists = True
    from django.contrib.admin.views.decorators import staff_member_required
    from django.http import HttpResponse, HttpResponseRedirect
    try:
        from mezzanine.generic.models import Keyword
    except Exception, e:
        keyword_exists = False 

    if keyword_exists:
        
        @staff_member_required
        def admin_keywords_submit(request):
            """
            Adds any new given keywords from the custom keywords field in the
            admin, and returns their IDs for use when saving a model with a
            keywords field.
            """
            ids, titles = [], []
            for title in request.POST.get("text_keywords", "").split(","):
                title = "".join([c for c in title if c.isalnum() or c in "- "])
                title = title.strip()
                if title:
                    keywords = Keyword.objects.filter(title__iexact=title)
                    
                    # pick a case-sensitive match if it exists.
                    # otherwise pick any other match.
                    for keyword in keywords:
                        if keyword.title == title:
                            break
                    
                    # no match at all, create a new keyword.
                    if not keywords.count():
                        keyword = Keyword(title=title)
                        keyword.save()                
                    
                    id = str(keyword.id)
                    if id not in ids:
                        ids.append(id)
                        titles.append(title)
            return HttpResponse("%s|%s" % (",".join(ids), ", ".join(titles)))
        
        import mezzanine.generic.views
        mezzanine.generic.views.admin_keywords_submit = admin_keywords_submit
        
        # TODO: move this code to a new view that extends Mezzanine blog_post_detail.
        # Not documented way of doing it so we stick with this temporary solution for the moment.
        from mezzanine.blog.models import BlogPost
        
        def blogPost_get_related_posts_by_tag(self):
            # returns a list of BlogPosts with common tags to the current post
            # the list is reverse chronological order
            ret = []
            
            from django.contrib.contenttypes.models import ContentType
            content_type_id = ContentType.objects.get_for_model(self).id
            select = r'''
                select p.* 
                from blog_blogpost p
                join generic_assignedkeyword ak on (p.id = ak.object_pk)
                where 
                    ak.content_type_id = %s
                AND 
                    ak.keyword_id in (select distinct ak2.keyword_id from generic_assignedkeyword ak2 where ak2.object_pk = %s and ak.content_type_id = %s)
                AND 
                    p.id <> %s
                order by p.publish_date;
            '''
            params = [content_type_id, self.id, content_type_id, self.id]
            
            # run the query and remove duplicates
            posts = {}
            for post in BlogPost.objects.raw(select, params):
                posts[post.publish_date] = post
            keys = posts.keys()
            keys.sort()
            for key in keys[::-1]:
                ret.append(posts[key])
                    
            return ret
        
        BlogPost.get_related_posts_by_tag = blogPost_get_related_posts_by_tag

# Patch 5: bar permissions to some application models in the admin
# Why not doing it with django permissions and groups?
# Because we want to keep the data migration scripts simple and
# therefore we copy all the django records from  STG to the other 
# servers. This means that we can't have different permissions and
# user groups across our servers.
# 
# setings.HIDDEN_ADMIN_APPS = ('APP_LABEL_1', )
#

import django.contrib.auth.models 

_user_has_module_perms_old = django.contrib.auth.models._user_has_module_perms

def _user_has_module_perms(user, app_label):
    if user and not user.is_superuser and user.is_active and \
        app_label in getattr(settings, 'HIDDEN_ADMIN_APPS', ()):
        return False
    return _user_has_module_perms_old(user, app_label)

django.contrib.auth.models._user_has_module_perms = _user_has_module_perms

_user_has_perm_old = django.contrib.auth.models._user_has_perm
def _user_has_perm(user, perm, obj):
    # perm =  'digipal.add_allograph'
    if user and not user.is_superuser and user.is_active and perm and \
        re.sub(ur'\..*$', '', '%s' % perm) in getattr(settings, 'HIDDEN_ADMIN_APPS', ()):
        return False
    return _user_has_perm_old(user, perm, obj)

django.contrib.auth.models._user_has_perm = _user_has_perm

# Patch 6: Whoosh ReadTooFar bug.
# See Jira 115: ReadToFar Error on the search page 
# See Whoosh Issue Tracker: 331
#  https://bitbucket.org/mchaput/whoosh/issue/331/readtoofar-exception
from whoosh.matching.combo import ArrayUnionMatcher
    
def array_union_matcher_skip_to(self, docnum):
    if docnum < self._offset:
        # We've already passed it
        return
    elif docnum < self._limit:
        # It's in the current part
        self._docnum = docnum
        self._find_next()
        return

    # Advance all submatchers
    submatchers = self._submatchers
    active = False
    for subm in submatchers:
        # GN: patch for the ReadTooFar error.
        if subm.is_active():
            subm.skip_to(docnum)
        active = active or subm.is_active()

    if active:
        # Rebuffer
        self._docnum = self._min_id()
        self._read_part()
    else:
        self._docnum = self._doccount
    
# Commnented out as the code seem the have been fixed in new version of Whoosh
##ArrayUnionMatcher.skip_to = array_union_matcher_skip_to
