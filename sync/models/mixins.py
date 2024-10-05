# sync/models/mixins.py


class FormattedDurationMixin:
    def formatted_duration(self):
        if self.duration is None:
            return "N/A"
        total_minutes = self.duration // (1000 * 60)  # Convert milliseconds to minutes
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


class FormattedActorsMixin:
    def formatted_actors(self, limit=None):
        actor_roles = (
            self.roles.filter(role_type="ACTOR")
            .select_related("person")
            .order_by("person__last_name", "person__first_name")
        )
        if limit:
            actor_roles = actor_roles[:limit]
        if not actor_roles:
            return "No cast information available"

        def format_actor_name(role):
            person = role.person
            name = f"{person.first_name} {person.last_name}".strip() or "Unknown Actor"
            if role.character_name:
                return f"{name} as {role.character_name}"
            return name

        return ", ".join(format_actor_name(role) for role in actor_roles)


class FormattedGenresMixin:
    def formatted_genres(self):
        return ", ".join(genre.name for genre in self.genres.all())
