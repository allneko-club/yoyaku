from django import forms


def text_input_factory(_id, placeholder, clas='form-control', input_type='text'):
    result = forms.TextInput(
        attrs={
            'class': clas,
            'id': _id,
            'placeholder': placeholder,
            'type': input_type,
        }
    )
    return result


def textarea_factory(row, clas='form-control'):
    result = forms.Textarea(
        attrs={
            "class": clas,
            'rows': row,
        }
    )
    return result
