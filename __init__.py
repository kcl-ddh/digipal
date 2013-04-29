# Tell South about the iipimage field
# See http://south.readthedocs.org/en/latest/tutorial/part4.html#simple-inheritance
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^iipimage\.fields\.ImageField"])

# patch the iipimage to correct a bug (.image was hardcoded)
from iipimage import storage
from iipimage.storage import generate_new_image_path
from django.conf import settings

import logging
dplog = logging.getLogger( 'digipal_debugger')

# PATCH 1:
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

    from django.contrib.admin.views.decorators import staff_member_required
    from django.http import HttpResponse, HttpResponseRedirect
    from mezzanine.generic.models import Keyword, Rating
    
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
