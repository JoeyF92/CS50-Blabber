from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Post(models.Model):
    post = models.CharField(max_length=300)
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="users_post")
    timestamp = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField("User", blank=True, related_name="liked")
    
    def serialize(self):
        return {
            "id": self.id,
            "post": self.post,
            "timestamp": self.timestamp.strftime("%b %d %Y, %I:%M %p"),
        }
       
    
    def __str__(self):
        return f"Post: {self.id}"

class Follow(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="followed_by")
    user_to_follow = models.ForeignKey("User", on_delete=models.CASCADE, related_name="following")
    
    class Meta:
        unique_together = ['user_to_follow', 'user']
        
    def __str__(self):
        return f" {self.user} follows {self.user_to_follow}"