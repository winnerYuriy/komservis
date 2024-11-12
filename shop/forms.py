from django import forms
from .models import Category

class ExcelUploadForm(forms.Form):
    file = forms.FileField(
        label='Виберіть Excel-файл',
        help_text='Підтримувані формати: .xlsx, .xls',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    

class ChangeCategoryForm(forms.Form):
    new_category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label="Виберіть нову категорію",
        required=True
    )
