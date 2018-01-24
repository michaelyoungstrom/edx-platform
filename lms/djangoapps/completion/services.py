"""
Runtime service for communicating completion information to the xblock system.
"""

from .models import BlockCompletion
from . import waffle


class CompletionService(object):
    """
    Service for handling completions for a user within a course.

    Exposes

    * self.completion_tracking_enabled() -> bool
    * self.get_completions(candidates)

    Constructor takes a user object and course_key as arguments.
    """
    def __init__(self, user, course_key):
        self._user = user
        self._course_key = course_key

    def completion_tracking_enabled(self):
        """
        Exposes ENABLE_COMPLETION_TRACKING waffle switch to XModule runtime

        Return value:

            bool -> True if completion tracking is enabled.
        """
        return waffle.waffle().is_enabled(waffle.ENABLE_COMPLETION_TRACKING)

    def get_completions(self, candidates):
        """
        Given an iterable collection of block_keys in the course, returns a
        mapping of the block_keys to the present completion values of their
        associated blocks.

        If a completion is not found for a given block in the current course,
        0.0 is returned.  The service does not attempt to verify that the block
        exists within the course.

        Parameters:

            candidates: collection of BlockKeys within the current course.

        Return value:

            dict[BlockKey] -> float: Mapping blocks to their completion value.
        """
        completion_queryset = BlockCompletion.objects.filter(
            user=self._user,
            course_key=self._course_key,
            block_key__in=candidates,
        )
        completions = {block.block_key: block.completion for block in completion_queryset}
        for candidate in candidates:
            if candidate not in completions:
                completions[candidate] = 0.0
        return completions

    def get_course_completions(self):
        """
        query all completions for a course/user pair

        Return value: dict[BlockKey] = float
        """
        course_block_query = BlockCompletion.objects.filter(
            user=self._user,
            course_key=self._course_key,
        )
        completions = {block.block_key: block.completion for block in course_block_query}
        return completions

    def get_latest_block_completed(self):
        latest_completed_block_query = BlockCompletion.objects.filter(
            user=self._user,
            course_key=self._course_key,
        ).latest()
        completions = {latest_completed_block_query.block_key: latest_completed_block_query.completion} # for block in latest_completed_block_query}
        return completions
