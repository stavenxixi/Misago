from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from misago.acl import cachebuster
from misago.admin.views import generic
from misago.forums.models import Forum
from misago.forums.forms import ForumFormFactory


class ForumAdmin(generic.AdminBaseMixin):
    root_link = 'misago:admin:forums:nodes:index'
    Model = Forum
    templates_dir = 'misago/admin/forums'
    message_404 = _("Requested forum does not exist.")

    def get_target(self, kwargs):
        target = super(ForumAdmin, self).get_target(kwargs)
        if target.pk and target.tree_id != 1:
            raise Forum.DoesNotExist()
        else:
            return target


class ForumsList(ForumAdmin, generic.ListView):
    ordering = (('lft', None),)

    def get_queryset(self):
        return Forum.objects.all_forums()

    def process_context(self, request, context):
        context['items'] = [f for f in context['items']]

        levels_lists = {}

        for i, item in enumerate(context['items']):
            item.level_range = range(item.level - 1)
            item.first = False
            item.last = False
            levels_lists.setdefault(item.level, []).append(item)

        for level_items in levels_lists.values():
            level_items[0].first = True
            level_items[-1].last = True

        return context


class ForumFormMixin(object):
    def create_form_type(self, request, target):
        return ForumFormFactory(target)

    def handle_form(self, form, request, target):
        if form.instance.pk:
            if form.instance.parent_id != form.cleaned_data['new_parent'].pk:
                form.instance.move_to(form.cleaned_data['new_parent'],
                                      position='last-child')
            form.instance.save()
        else:
            form.instance.insert_at(form.cleaned_data['new_parent'],
                                    position='last-child',
                                    save=True)

        cachebuster.invalidate()
        messages.success(request, self.message_submit % target.name)


class NewForum(ForumFormMixin, ForumAdmin, generic.ModelFormView):
    message_submit = _('New forum "%s" has been saved.')


class EditForum(ForumFormMixin, ForumAdmin, generic.ModelFormView):
    message_submit = _('Forum "%s" has been edited.')


class EditForum(ForumFormMixin, ForumAdmin, generic.ModelFormView):
    message_submit = _('Forum "%s" has been deleted.')


class MoveUpForum(ForumAdmin, generic.ButtonView):
    def button_action(self, request, target):
        try:
            other_target = target.get_previous_sibling()
        except Forum.DoesNotExist:
            other_target = None

        if other_target:
            Forum.objects.move_node(target, other_target, 'left')
            message = _('Forum "%s" has been moved up.') % target.name
            messages.success(request, message)


class MoveDownForum(ForumAdmin, generic.ButtonView):
    def button_action(self, request, target):
        try:
            other_target = target.get_next_sibling()
        except Forum.DoesNotExist:
            other_target = None

        if other_target:
            Forum.objects.move_node(target, other_target, 'right')
            message = _('Forum "%s" has been moved down.') % target.name
            messages.success(request, message)