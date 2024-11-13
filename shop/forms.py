import json
from django import forms
from .models import Category, Product
from django.utils.safestring import mark_safe


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


class UploadProductsForm(forms.Form):
    file = forms.FileField(label="Виберіть файл Excel")


class ProductAdminForm(forms.ModelForm):
    attributes_table = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        attributes = self.get_attributes_as_dict(self.instance.additional_attributes)
        table_html = self.generate_table_html(attributes)
        self.fields["attributes_table"].widget = forms.Textarea(
            attrs={"readonly": "readonly"}
        )
        self.fields["attributes_table"].initial = table_html

    def get_attributes_as_dict(self, json_data):
        try:
            return json.loads(json_data) if json_data else {}
        except json.JSONDecodeError:
            return {}

    def generate_table_html(self, attributes):
        rows = "".join(
            f'<tr><td>{key}</td><td><input type="text" name="attr_{key}" value="{value}" /></td></tr>'
            for key, value in attributes.items()
        )
        return mark_safe(f"<table>{rows}</table>")

    def clean(self):
        cleaned_data = super().clean()
        attributes = {}
        for key, value in self.data.items():
            if key.startswith("attr_"):
                attr_key = key.replace("attr_", "")
                attributes[attr_key] = value
        cleaned_data["additional_attributes"] = json.dumps(attributes)
        return cleaned_data

