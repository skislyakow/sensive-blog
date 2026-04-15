from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count, OuterRef, Subquery


class PostQuerySet(models.QuerySet):
    def year(self, year):
        posts_at_year = self.filter(
            published_at__year=year
        ).order_by('published_at')

        return posts_at_year

    def popular(self):
        return self.annotate(
            likes_count=Count('likes')
        ).order_by('-likes_count')

    def fetch_with_comments_count(self):
        """
        Добавляет к каждому посту количество комментариев через Subquery.

        Разберём по частям:

        1. OuterRef('id') - ссылка на поле 'id' из ВНЕШНЕГО (outer) запроса.
           Без OuterRef Django не знал бы, к какой именно записи обращаться.

        2. Comment.objects.filter(post_id=OuterRef('id')) - для каждого поста
           находим все комментарии, где post_id равен id этого поста.

        3. .annotate(count=Count('*')) - считаем количество таких комментариев.
           Count('*') = посчитать все записи (можно просто Count('id'))

        4. .values('count') - берём только поле count (агрегат)

        5. Subquery(...) - оборачиваем это в подзапрос, чтобы использовать
           как поле основного запроса

        Плюс этого подхода перед annotate(Count('comments')):
        - Работает даже когда простой Count не справляется (например, со
          сложными условиями фильтрации)
        - Можно переиспользовать в других QuerySet

        Нужны популярные с комментариями-
        Post.objects.popular().fetch_with_comments_count()

        Нужны свежие с комментариями-
        Post.objects.order_by('-published_at').fetch_with_comments_count()

        Нужен один метод-
        some_queryset.fetch_with_comments_count()

        - Даёт точный контроль над подзапросом
        """
        return self.annotate(
            comments_count=Subquery(
                Comment.objects.filter(post_id=OuterRef('id'))
                .annotate(count=Count('id'))
                .values('count')
            )
        )


class TagQuerySet(models.QuerySet):
    def popular(self):
        popular_tags = self.annotate(
            tags_count=Count('posts')
        ).order_by('-tags_count')
        return popular_tags

    def with_posts_count(self):
        return self.annotate(
            tags_count=Count('posts')
        ).order_by()


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    objects = PostQuerySet.as_manager()


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'

    objects = TagQuerySet.as_manager()


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        verbose_name='Пост, к которому написан',
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
