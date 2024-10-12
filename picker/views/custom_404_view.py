# picker/views/custom_404_view.py

from django.utils.decorators import classonlymethod
from django.views.generic import TemplateView


class Custom404View(TemplateView):
    template_name = "error.html"
    status_code = 404

    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        view.raise_exception = True
        return view

    def render_to_response(self, context, **response_kwargs):
        response_kwargs["status"] = self.status_code
        return super().render_to_response(context, **response_kwargs)
