'''
    Patches for other apps or libraries.
    Patches should always be avoided if possible because they are likely to break when the
    patched app gets upgraded. However we don't have direct control over them and it's
    sometimes the most efficient way to quickly include missing features.
    
    Patches are applied at the end of model.py (b/c/ this module is always loaded)
'''

import re

from digipal.compressor_filters import compressor_patch


def mezzanine_patches():
    # Patch 4:
    # Fix Mezzanine case-insensitive keyword issue
    # See https://github.com/stephenmcd/mezzanine/issues/647

    from mezzanine.conf import settings
    if 'mezzanine.blog' in settings.INSTALLED_APPS:

        keyword_exists = True
        try:
            from mezzanine.generic.models import Keyword
        except Exception, e:
            keyword_exists = False
            if getattr(settings, 'DEV_SERVER', False):
                print 'WARNING: import failed (%s) and Mezzanine Blog case-sensitive keywords patch cannot be applied.' % e

        if keyword_exists:
            # patch integrated into the latest mezzanine version

            #             from django.contrib.admin.views.decorators import staff_member_required
            #             @staff_member_required
            #             def admin_keywords_submit(request):
            #                 """
            #                 Adds any new given keywords from the custom keywords field in the
            #                 admin, and returns their IDs for use when saving a model with a
            #                 keywords field.
            #                 """
            #                 ids, titles = [], []
            #                 for title in request.POST.get("text_keywords", "").split(","):
            #                     title = "".join([c for c in title if c.isalnum() or c in "- "])
            #                     title = title.strip()
            #                     if title:
            #                         keywords = Keyword.objects.filter(title__iexact=title)
            #
            #                         # pick a case-sensitive match if it exists.
            #                         # otherwise pick any other match.
            #                         for keyword in keywords:
            #                             if keyword.title == title:
            #                                 break
            #
            #                         # no match at all, create a new keyword.
            #                         if not keywords.count():
            #                             keyword = Keyword(title=title)
            #                             keyword.save()
            #
            #                         id = str(keyword.id)
            #                         if id not in ids:
            #                             ids.append(id)
            #                             titles.append(title)
            #                 from django.http import HttpResponse
            #                 return HttpResponse("%s|%s" % (",".join(ids), ", ".join(titles)))
            #
            #             import mezzanine.generic.views
            #             mezzanine.generic.views.admin_keywords_submit = admin_keywords_submit

            # TODO: move this code to a new view that extends Mezzanine blog_post_detail.
            # Not documented way of doing it so we stick with this temporary
            # solution for the moment.

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

            from mezzanine.blog.models import BlogPost
            BlogPost.get_related_posts_by_tag = blogPost_get_related_posts_by_tag

    # see https://github.com/stephenmcd/mezzanine/issues/1060
    patch_thumbnail = True
    if patch_thumbnail:
        from mezzanine.core.templatetags import mezzanine_tags

        thumbnail = mezzanine_tags.thumbnail

        def thumbnail_2(*args, **kwargs):
            ret = ''
            try:
                ret = thumbnail(*args, **kwargs)
            except:
                pass
            return ret
        mezzanine_tags.thumbnail = thumbnail_2


def admin_patches():
    # Patch 5: bar permissions to some application models in the admin
    # Why not doing it with django permissions and groups?
    # Because we want to keep the data migration scripts simple and
    # therefore we copy all the django records from  STG to the other
    # servers. This means that we can't have different permissions and
    # user groups across our servers.
    #
    # setings.HIDDEN_ADMIN_APPS = ('APP_LABEL_1', )
    #

    from mezzanine.conf import settings
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

# Whoosh 2.6 patch for the race condition during clearing of the cache
# See JIRA DIGIPAL-480


def whoosh_patches():

    import functools
    from heapq import nsmallest
    from whoosh.compat import iteritems, xrange
    from operator import itemgetter
    from time import time
    from threading import Lock

    def lru_cache(maxsize=100):
        """A simple cache that, when the cache is full, deletes the least recently
        used 10% of the cached values.

        This function duplicates (more-or-less) the protocol of the
        ``functools.lru_cache`` decorator in the Python 3.2 standard library.

        Arguments to the cached function must be hashable.

        View the cache statistics tuple ``(hits, misses, maxsize, currsize)``
        with f.cache_info().  Clear the cache and statistics with f.cache_clear().
        Access the underlying function with f.__wrapped__.
        """

        def decorating_function(user_function):
            stats = [0, 0]  # Hits, misses
            data = {}
            lastused = {}
            lock = Lock()

            @functools.wraps(user_function)
            def wrapper(*args):
                with lock:
                    try:
                        result = data[args]
                        stats[0] += 1  # Hit
                    except KeyError:
                        stats[1] += 1  # Miss
                        if len(data) == maxsize:
                            for k, _ in nsmallest(maxsize // 10 or 1,
                                                  iteritems(lastused),
                                                  key=itemgetter(1)):
                                del data[k]
                                del lastused[k]
                        data[args] = user_function(*args)
                        result = data[args]
                    finally:
                        lastused[args] = time()
                    return result

            def cache_info():
                with lock:
                    return stats[0], stats[1], maxsize, len(data)

            def cache_clear():
                with lock:
                    data.clear()
                    lastused.clear()
                    stats[0] = stats[1] = 0

            wrapper.cache_info = cache_info
            wrapper.cache_clear = cache_clear
            return wrapper
        return decorating_function

    from whoosh.util import cache
    cache.lru_cache = lru_cache
