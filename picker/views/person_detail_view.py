# picker/views/person_detail_view.py

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import DetailView

from picker.forms.person_detail_sort_form import PersonDetailSortForm
from sync.models import Person, Role
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class PersonDetailView(DetailView):
    model = Person
    template_name = "person_detail.html"
    context_object_name = "person"
    pk_url_kwarg = "person_id"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            html = render_to_string("person_detail_content.html", context, request)
            return HttpResponse(html)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = self.object

        form = PersonDetailSortForm(self.request.GET or None)
        context["form"] = form

        roles = Role.objects.filter(person=person).select_related("movie", "show")

        movies = list(set([role.movie for role in roles if role.movie]))
        shows = list(set([role.show for role in roles if role.show]))

        # Set safe_poster_url for each movie
        for movie in movies:
            movie.safe_poster_url = self.get_safe_poster_url(movie)

        sort_by = form.cleaned_data.get("sort_by") if form.is_valid() else "name_asc"
        context["movies"] = self.apply_sorting(movies, sort_by)
        context["shows"] = self.apply_sorting(shows, sort_by)

        return context

    def apply_sorting(self, items, sort_by):
        if sort_by == "year_asc":
            return sorted(items, key=lambda x: x.year or 0)
        elif sort_by == "year_desc":
            return sorted(items, key=lambda x: x.year or 0, reverse=True)
        elif sort_by == "name_desc":
            return sorted(items, key=lambda x: x.title.lower(), reverse=True)
        else:
            return sorted(items, key=lambda x: x.title.lower())

    def get_safe_poster_url(self, movie):
        if movie.optimized_poster:
            try:
                return movie.optimized_poster.url
            except Exception as e:
                logger.warning(
                    f"Error accessing optimized poster for movie {movie.id}: {str(e)}"
                )
        return movie.poster_url
