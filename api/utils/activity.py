from api.models import Activity


def log_activity(
    *,
    group=None,
    actor,
    action: str,
    expense=None,
    settlement=None,
    metadata: dict | None = None,
):
    Activity.objects.create(
        group=group,
        actor=actor,
        action=action,
        expense=expense,
        settlement=settlement,
        metadata=metadata or {},
    )
