# picker/forms/person_detail_sort_form.py

from django import forms


class PersonDetailSortForm(forms.Form):
    SORT_CHOICES = [
        ("year_asc", "Year (Oldest First)"),
        ("year_desc", "Year (Newest First)"),
        ("name_asc", "Name (A-Z)"),
        ("name_desc", "Name (Z-A)"),
    ]
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        label="Sort by",
        initial="name_asc",
    )
