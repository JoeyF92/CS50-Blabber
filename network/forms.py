from django.forms import ModelForm, TextInput
from network.models import Post


class NewPostForm(ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        exclude = ['user', 'likes', 'timestamp']
        widgets = {            
            'post': TextInput(attrs={
                'class': "form-control",
                'style': 'width: 100%',
            })
        }
