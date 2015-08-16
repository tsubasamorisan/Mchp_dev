from django import forms
from django.forms import ModelForm, TextInput, ChoiceField, Select, IntegerField
from calendar_mchp.models import CalendarEvent

from documents.models import Document


class DocumentUploadForm(ModelForm):

    PRICE_WIDGET = TextInput(attrs=dict({
        'placeholder':'type a price in points, ex: 400 would be $4.00',
        'data-toggle':'tooltip',
        'data-placement':'right',
        'data-original-title':'The average document sells for 400 points. Type a number!',
        'container_id': 'document_price',
        'class': 'form-control input-lg',
    }))

    # Price is not required in case Document is Syllabus
    # In which case automatically settings price to 0
    price = IntegerField(required=False, min_value=0, widget=PRICE_WIDGET)



    EVENT_WIDGET = TextInput(attrs=dict({
        'placeholder': 'type a event name (Exam 1)',
        'autocomplete': 'off',
        'data-toggle': 'dropdown',
        'class': 'form-control input-lg dropdown-toggle',
        'id': 'id_event'
    }))
    event_id = IntegerField(required=True, min_value=0, widget=EVENT_WIDGET)


    # {{ form.as_style }} with use this in templates
    def as_style(self):
        return self._html_output(
            normal_row = '\
            <div class="form-group">\
            <div class="input-group">\
            <span class="input-group-addon">%(label)s</span>\
            %(field)s\
            %(help_text)s</div></div>',
            error_row = '%s',
            row_ender = '',
            help_text_html = '%s',
            errors_on_separate_row = True)

    def clean(self):
        cleaned_data = super(DocumentUploadForm, self).clean()

        # Syllabus is always free
        if cleaned_data['type'] == Document.SYLLABUS:
            cleaned_data['price'] = 0
        elif 'price' not in cleaned_data:
            self.add_error('price', 'This field is required')

        event_id = cleaned_data.get('event_id', None)
        if event_id:
            event = CalendarEvent.objects.filter(id=event_id)
            if event.exists():
                cleaned_data['event'] = event[0]
            else:
                self.add_error('event_id', 'Event does not exist')


        return cleaned_data

    class Meta:
        model = Document
        fields = ['title', 'description', 'type', 'course', 'event_id', 'price', 'document']

        input_attr = {
            'class': 'form-control input-lg',
        }
        widgets = {
            # dict(x.items() | y.items()) combines the _base attrs with 
            # any class specific attrs, like the placeholder
            'title': TextInput(attrs=dict({
                'placeholder': 'ex: Exam 1 Study Guide',
                'data-toggle':'tooltip',
                'data-placement':'right',
                'data-original-title':'Document title only. Please don\'t include the name of the class'
            }.items() | input_attr.items())),

            'description': TextInput(attrs=dict({
                'placeholder':'Short description of this file',
                'data-toggle':'tooltip',
                'data-placement':'right',
                'data-original-title':'What you say here will help convince your classmates to buy this'
            }.items() | input_attr.items())),

            'course': TextInput(attrs=dict({
                'placeholder':'type a course code and number: CSC 245',
                'autocomplete': 'off',
                'data-toggle': 'dropdown',
                'class': 'form-control input-lg dropdown-toggle'
            }.items())),

            'type': Select(attrs=dict({
                'choices': Document.DOCUMENT_TYPE_CHOICES,
                'class': 'form-control input-lg dropdown-toggle',
                'id': 'document_type',
          }.items() | input_attr.items())),
        }

        labels = {
            'title': 'Title',
            'description': 'Description',
            'price': 'Sell for',
            'document': 'File',
            'event_id': 'Event',
        }
        error_messages = {
            'title': {
                'max_length': 'That title is unreasonably long.',
                'required': 'That title is unreasonably short',
            },
            'price': {
                'invalid': 'That is not a price.',
            },
            'description': {
                'max_length': 'Tone it down there, Tolstoy.'
            },
            'document': {
                'required': 'Please select a file.',
            },
        }
