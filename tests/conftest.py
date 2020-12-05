import os

from hypothesis import settings

settings.register_profile("dev", deadline=None, max_examples=10)
settings.register_profile("ci", max_examples=1000)
settings.load_profile(
    os.getenv("HYPOTHESIS_PROFILE", "ci" if os.getenv("CI") else "default")
)
