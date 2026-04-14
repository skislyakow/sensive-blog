from django.contrib import admin
from blog.models import Post, Tag, Comment


class PostAdmin(admin.ModelAdmin):
    raw_id_fields = ('author',)
    autocomplete_fields = ('tags',)
    exclude = ('likes',)


admin.site.register(Post, PostAdmin)


class CommentAdmin(admin.ModelAdmin):
    raw_id_fields = ('post', 'author')
    list_display = ('author', 'post', 'text', 'published_at')
    list_select_related = ('post', 'author')


admin.site.register(Comment, CommentAdmin)


class TagAdmin(admin.ModelAdmin):
    search_fields = ('title',)


admin.site.register(Tag, TagAdmin)
