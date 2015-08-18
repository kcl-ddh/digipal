# Content Permission in DigiPal

User access to the content is determined by the following factors:

1. is the user logged in as staff?
2. is the type of the content public or private?
3. the permission on the repository or the image record

## 1. Public user and staff

We distinguish between public users and users logged in as staff (i.e. database editors). Staff have access to the Django backend interface and the database tables and records. They also have less restrictions on the content displayed on the front-end.

The Django super users can use the django permission system to grant write and read access to the users on any table.

## 2. Content type visibility

Two setting variables in your local_settings.py file control the visibility of some content types on the front-end:

```
MODELS_PUBLIC = ['itempart', 'image', 'graph', 'hand', 'scribe', 'textcontentxml']
MODELS_PRIVATE = ['itempart', 'image', 'graph', 'hand', 'scribe', 'textcontentxml']
```

MODELS_PUBLIC is for public users, MODELS_PRIVATE is for staff. Inclusion within the list means that the content type is visible. If a content type is invisible, its existence is completely hidden on the site from the users. This affects the advanced and faceted search, the record views, the text editor and the annotator.
itempart is more or less like a manuscript (or an object with man-made letterforms or decorations), image = an image of a manuscript, textcontentxml = the textual content of an itempart

## 3. Image permissions

You can create your own image permissions and permission messages in the database and apply them to a whole repository or to individual images. A media permission contains a custom message (e.g. "The quality of this image is too low. It is only available as a thumbnail.") and a level permission. The permision level is either: public, thumbnail only or public. This will affect the visibility of the image in the search results and the various image viewer.

