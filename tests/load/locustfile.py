"""Locust scenarios for exercising workflow start and approval paths."""

from locust import HttpUser, task


class SnacktopusUser(HttpUser):
    """Placeholder user that will call into the agent shell once it exists."""

    @task
    def ask_for_snack(self) -> None:
        self.environment.runner.greenlet.spawn_later(0, self._not_implemented)

    def _not_implemented(self) -> None:
        raise NotImplementedError("Load testing will be implemented once the API is ready.")
