import re
import uuid

from django import forms
from django.contrib.auth.forms import UserCreationForm

from yoyaku.accounts.models import User
from yoyaku.core.exceptions.field_validatiors import validate_username
from yoyaku.accounts.widgets_factory import text_input_factory, textarea_factory


class StaffForm(UserCreationForm):
    password1 = forms.CharField(
        label='パスワード*',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        max_length=User.PASSWORD_MAX_LENGTH,
        help_text=f'（半角の英字・数字両方を用いて下さい。8~{User.PASSWORD_MAX_LENGTH}文字）'
    )
    password2 = forms.CharField(
        label='パスワード（確認）*',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ('user_id', 'username')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'user_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if commit:
            user.save()
        return user


class CustomerSearchForm(forms.Form):
    """顧客検索フォーム"""
    username = forms.CharField(
        label='名前',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    furigana = forms.CharField(
        label='フリガナ',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    email = forms.CharField(
        label='メール',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    phone_number = forms.CharField(
        label='電話番号',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )


class CustomerForm(forms.ModelForm):
    """顧客を作成/更新するためのフォーム"""

    side_business_experience = forms.ChoiceField(
        required=False,
        choices=(('', ''), ('はい', 'はい'), ('いいえ', 'いいえ')),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ('username', 'furigana', 'email', 'phone_number', 'linename', 'age', 'ages', 'job',
                  'zip_code', 'zip', 'side_business_experience', 'workable_time', 'contact', 'memo1', 'memo2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'furigana': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'type': 'email', 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'linename': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'ages': forms.Select(attrs={'class': 'form-control'}),
            'job': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'zip': forms.TextInput(attrs={'class': 'form-control'}),
            'workable_time': textarea_factory(3),
            'contact': textarea_factory(3),
            'memo1': textarea_factory(3),
            'memo2': textarea_factory(4),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].validators.append(validate_username)
        self.fields['ages'].empty_label = ''

    def clean_username(self):
        """空白を全て削除"""
        username = self.cleaned_data['username']
        return re.sub(r'\s+', '', username)

    def clean_email(self):
        d = self.cleaned_data['email']
        return d.lower()

    def save(self, commit=True):
        # customerはuser_idを使わないが、ユニーク制限があるため自動生成する
        obj = super().save(commit=False)
        obj.user_id = uuid.uuid4()
        if commit:
            obj.save()
        return obj


class RegisterCustomerForm(forms.ModelForm):
    """予約ページの顧客情報用フォーム"""

    # 18歳~85歳 までとする
    age = forms.TypedChoiceField(
        choices=[('', '')] + [(i, i) for i in range(18, 86)],
        coerce=int,
        widget=forms.Select(attrs={'id': 'booking_age', 'class': 'form-select'}),
        error_messages={
            'required': '年齢は必須です。',
            'invalid_choice': '年齢は選択肢から選択してください。',
        },
    )

    class Meta:
        model = User
        fields = ('username', 'furigana', 'email', 'phone_number', 'linename', 'age', 'job')
        widgets = {
            'username': text_input_factory('booking_username', '（例）山田太朗'),
            'furigana': text_input_factory('booking_furigana', '（例）ヤマダタロウ'),
            'email': text_input_factory('booking_email', '（例）yamadataro@yahoo.co.jp', input_type='email'),
            'phone_number': text_input_factory('booking_phone_number', '（例）09012345678'),
            'linename': text_input_factory('booking_line_name', '（例）山田太朗'),
            'job': text_input_factory('booking_job', '（例）会社員'),
        }
        error_messages = {
            'username': {
                'required': 'お名前は必須です。',
                'max_length': 'お名前は%(limit_value)d文字以内で入力してください。',
            },
            'furigana': {
                'required': 'フリガナは必須です。',
                'max_length': 'フリガナは%(limit_value)d文字以内で入力してください。',
            },
            'email': {
                'required': 'メールアドレスは必須です。',
                'max_length': 'メールアドレスは%(limit_value)d文字以内で入力してください。',
            },
            'phone_number': {
                'required': '電話番号は必須です。',
                'max_length': '電話番号は半角数字でハイフンなしで入力してください。',
            },
            'linename': {
                'max_length': 'ライン名は%(limit_value)d文字以内で入力してください。',
            },
            'job': {
                'required': '職業は必須です。',
                'max_length': '職業は%(limit_value)d文字以内で入力してください。',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['furigana'].required = True
        self.fields['username'].validators.append(validate_username)
        self.fields['job'].required = True

    def clean_username(self):
        """苗字と名前の間の空白を削除"""
        d = self.cleaned_data['username']
        return re.sub(r'\s+', '', d)

    def clean_furigana(self):
        """苗字と名前の間の空白を削除"""
        d = self.cleaned_data['furigana']
        return re.sub(r'\s+', '', d)

    def clean_email(self):
        d = self.cleaned_data['email']
        return d.lower()

    def save(self, commit=True):
        # customerはuser_idを使わないが、ユニーク制限があるため自動生成する
        obj = super().save(commit=False)
        obj.user_id = uuid.uuid4()
        if commit:
            obj.save()
        return obj
