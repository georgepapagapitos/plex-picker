# picker/views/movie_cast_view.py

from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from sync.models.movie import Movie


class MovieCastView(DetailView):
    model = Movie
    template_name = "movie_cast.html"
    context_object_name = "movie"
    pk_url_kwarg = "movie_id"

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        return get_object_or_404(
            queryset.prefetch_related("roles__person"),
            pk=self.kwargs.get(self.pk_url_kwarg),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_roles"] = self.object.roles.select_related("person").order_by(
            "order"
        )
        return context
