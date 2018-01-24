"""
Common utilities for the course experience, including course outline.
"""
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import BlockUsageLocator

from lms.djangoapps.course_api.blocks.api import get_blocks
from lms.djangoapps.course_blocks.utils import get_student_module_as_dict
from request_cache.middleware import request_cached
from xmodule.modulestore.django import modulestore

from lms.djangoapps.completion.services import CompletionService
from lms.djangoapps.completion.models import BlockCompletion

@request_cached
def get_course_outline_block_tree(request, course_id):
    """
    Returns the root block of the course outline, with children as blocks.
    """

    def populate_children(block, all_blocks):
        """
        Replace each child id with the full block for the child.

        Given a block, replaces each id in its children array with the full
        representation of that child, which will be looked up by id in the
        passed all_blocks dict. Recursively do the same replacement for children
        of those children.
        """
        children = block.get('children', [])

        for i in range(len(children)):
            child_id = block['children'][i]
            child_detail = populate_children(all_blocks[child_id], all_blocks)
            block['children'][i] = child_detail

        return block

    def set_last_accessed_default(block):
        """
        Set default of False for last_accessed on all blocks.
        """
        block['last_accessed'] = False
        block['complete'] = False
        for child in block.get('children', []):
            set_last_accessed_default(child)

    def mark_blocks_completed(user, course_key, block):
        """

        """
        # RESUME_BLOCKS_WHITELIST = [
        #     'sequential', 'vertical', 'html', 'problem', 'video'
        # ]

        def recurse_mark_complete(completion_query, last_complete, block):
            locatable_block_string = BlockUsageLocator.from_string(block['id'])

            if BlockUsageLocator.from_string(block['id']) in completion_query.keys():
                block['complete'] = True
                if locatable_block_string == last_complete.keys()[0]:
                    block['last_accessed'] = True

            if block.get('children'):
                for child in block['children']:
                    block['children'][block['children'].index(child)] = recurse_mark_complete(completion_query, last_complete, block=child)
                    if block['children'][block['children'].index(child)]['last_accessed'] is True: #  and block['type'] in RESUME_BLOCKS_WHITELIST:
                        block['last_accessed'] = True
            return block

        completion_service_instance = CompletionService(
            user=user,
            course_key=course_key
        )
        last_completed_child_position = completion_service_instance.get_latest_block_completed()
        course_block_query = completion_service_instance.get_course_completions()
        block = recurse_mark_complete(completion_query=course_block_query, last_complete=last_completed_child_position, block=block)

    def mark_last_accessed(user, course_key, block):
        """
        Recursively marks the branch to the last accessed block.
        """
        block_key = block.serializer.instance
        student_module_dict = get_student_module_as_dict(user, course_key, block_key)

        last_accessed_child_position = student_module_dict.get('position')
        if last_accessed_child_position and block.get('children'):
            block['last_accessed'] = True
            if last_accessed_child_position <= len(block['children']):
                last_accessed_child_block = block['children'][last_accessed_child_position - 1]
                last_accessed_child_block['last_accessed'] = True
                mark_last_accessed(user, course_key, last_accessed_child_block)
            else:
                # We should be using an id in place of position for last accessed. However, while using position, if
                # the child block is no longer accessible we'll use the last child.
                block['children'][-1]['last_accessed'] = True

    course_key = CourseKey.from_string(course_id)
    course_usage_key = modulestore().make_course_usage_key(course_key)

    all_blocks = get_blocks(
        request,
        course_usage_key,
        user=request.user,
        nav_depth=3,
        requested_fields=['children', 'display_name', 'type', 'due', 'graded', 'special_exam_info', 'show_gated_sections', 'format'],
        block_types_filter=['course', 'chapter', 'sequential', 'vertical', 'html', 'problem', 'video']
    )

    course_outline_root_block = all_blocks['blocks'].get(all_blocks['root'], None)
    if course_outline_root_block:
        populate_children(course_outline_root_block, all_blocks['blocks'])
        set_last_accessed_default(course_outline_root_block)
        completion_service_instance = CompletionService(
            user=request.user,
            course_key=course_key
        )
        if completion_service_instance.completion_tracking_enabled():
            mark_blocks_completed(request.user, course_key, course_outline_root_block)
        else:
            mark_last_accessed(request.user, course_key, course_outline_root_block)
    return course_outline_root_block
