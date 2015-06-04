import logging

from django.db import models
import arrow
from taggit.managers import TaggableManager

from cobalt.act import Act

DEFAULT_LANGUAGE = 'eng'
DEFAULT_COUNTRY = 'za'

log = logging.getLogger(__name__)


class Document(models.Model):
    db_table = 'documents'

    frbr_uri = models.CharField(max_length=512, null=False, blank=False, default='/', help_text="Used globally to identify this work")
    """ The FRBR Work URI of this document that uniquely identifies it globally """

    title = models.CharField(max_length=1024, null=True, default='(untitled)')
    country = models.CharField(max_length=2, default=DEFAULT_COUNTRY)

    """ The 3-letter ISO-639-2 language code of this document """
    language = models.CharField(max_length=3, default=DEFAULT_LANGUAGE)
    draft = models.BooleanField(default=True, help_text="Drafts aren't available through the public API")
    """ Is this a draft? """

    document_xml = models.TextField(null=True, blank=True)
    """ Raw XML content of the entire document """

    # Date from the FRBRExpression element. This is either the publication date or the date of the last
    # amendment. This is used to identify this particular version of this work, so is stored in the DB.
    # It can be null only so that users aren't forced to add a value.
    expression_date = models.DateField(null=True, blank=True, help_text="Date of publication or latest amendment")

    # Date of commencement. AKN doesn't have a good spot for this, so it only goes in the DB.
    commencement_date = models.DateField(null=True, blank=True, help_text="Date of commencement unless otherwise specified")
    # Date of assent. AKN doesn't have a good spot for this, so it only goes in the DB.
    assent_date = models.DateField(null=True, blank=True, help_text="Date signed by the president")

    stub = models.BooleanField(default=False, help_text="This is a placeholder document without full content")
    """ Is this a stub without full content? """

    deleted = models.BooleanField(default=False, help_text="Has this document been deleted?")

    # freeform tags via django-taggit
    tags = TaggableManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def doc(self):
        """ The wrapped `an.act.Act` that this document works with. """
        if not getattr(self, '_doc', None):
            self._doc = Act(self.document_xml)
        return self._doc

    @property
    def content(self):
        """ Alias for `document_xml` """
        return self.document_xml

    @content.setter
    def content(self, value):
        """ The correct way to update the raw XML of the document. This will re-parse the XML
        and other attributes -- such as the document title and FRBR URI based on the XML. """
        self.reset_xml(value)

    @property
    def year(self):
        return self.doc.year

    @property
    def number(self):
        return self.doc.number

    @property
    def nature(self):
        return self.doc.nature

    @property
    def subtype(self):
        return self.doc.frbr_uri.subtype

    @property
    def locality(self):
        return self.doc.frbr_uri.locality

    @property
    def publication_name(self):
        return self.doc.publication_name

    @publication_name.setter
    def publication_name(self, value):
        self.doc.publication_name = value

    @property
    def publication_number(self):
        return self.doc.publication_number

    @publication_number.setter
    def publication_number(self, value):
        self.doc.publication_number = value

    @property
    def publication_date(self):
        return self.doc.publication_date

    @publication_date.setter
    def publication_date(self, value):
        self.doc.publication_date = value

    @property
    def amendments(self):
        return self.doc.amendments

    @amendments.setter
    def amendments(self, value):
        self.doc.amendments = value

    def save(self, *args, **kwargs):
        self.copy_attributes()
        return super(Document, self).save(*args, **kwargs)

    def copy_attributes(self, from_model=True):
        """ Copy attributes from the model into the document, or reverse
        if `from_model` is False. """

        if from_model:
            self.doc.title = self.title
            self.doc.frbr_uri = self.frbr_uri
            self.doc.language = self.language

            self.doc.work_date = self.doc.publication_date
            self.doc.expression_date = self.expression_date or self.doc.publication_date or arrow.now()
            self.doc.manifestation_date = self.updated_at or arrow.now()

        else:
            self.title = self.doc.title
            self.language = self.doc.language
            self.frbr_uri = self.doc.frbr_uri.work_uri()
            self.expression_date = self.doc.expression_date

        # update the model's XML from the Act XML
        self.refresh_xml()

    def refresh_xml(self):
        log.debug("Refreshing document xml for %s" % self)
        self.document_xml = self.doc.to_xml()

    def reset_xml(self, xml):
        """ Completely reset the document XML to a new value, and refresh database attributes
        from the new XML document. """
        log.debug("Setting for %s xml to: %s" % (self, xml))

        # this validates it
        doc = Act(xml)

        # now update ourselves
        self._doc = doc
        self.copy_attributes(from_model=False)

    def table_of_contents(self):
        return [t.as_dict() for t in self.doc.table_of_contents()]

    def amended_versions(self):
        """ Return a list of all the amended versions of this work.
        This is all documents that share the same URI but have different
        expression dates.
        """
        return Document.objects\
                .filter(deleted__exact=False)\
                .filter(frbr_uri=self.frbr_uri)\
                .order_by('expression_date').all()

    def __unicode__(self):
        return 'Document<%s, %s>' % (self.id, (self.title or '(Untitled)')[0:50])


class Subtype(models.Model):
    name = models.CharField(max_length=1024, help_text="Name of the document subtype")
    abbreviation = models.CharField(max_length=20, help_text="Short abbreviation to use in FRBR URI. No punctuation.", unique=True)

    class Meta:
        verbose_name = 'Document subtype'

    def clean(self):
        if self.abbreviation:
            self.abbreviation = self.abbreviation.lower()

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.abbreviation)
