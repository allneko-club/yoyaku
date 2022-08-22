from django import forms

from yoyaku.mail.models import MailAddress, SystemMail


class AddressCreateUpdateForm(forms.ModelForm):
    class Meta:
        model = MailAddress
        fields = ('email', 'memo')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'memo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_email(self):
        d = self.cleaned_data['email']
        return d.lower()


class SystemMailUpdateForm(forms.ModelForm):
    class Meta:
        model = SystemMail
        fields = ('sender', 'subject', 'content')
        widgets = {
            'sender': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sender'].empty_label = ''


class SendMailForm(SystemMailUpdateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sender'].required = True
