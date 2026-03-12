from odoo import models, fields, api

class TaskTeamMemberWizard(models.TransientModel):
    _name = "task.team.member.wizard"
    _description = "Add / Remove Team Member Wizard"

    user_ids = fields.Many2many('res.users', string="Select Users")
    task_id = fields.Many2one('project.task', string="Task")

    def add_selected_users(self):
        """Replace task team members and sync Assignees (user_ids) intelligently"""
        if not self.task_id:
            return {'type': 'ir.actions.act_window_close'}

        task = self.task_id
        selected_users = self.user_ids or self.env['res.users']

        # Replace team members
        task.team_member_ids = [(6, 0, selected_users.ids)]

        # Update Assignees:
        # 1. Add all selected users
        for u in selected_users:
            if u not in task.user_ids:
                task.user_ids = [(4, u.id)]

        # 2. Remove any previous team members who are no longer selected
        for u in task.user_ids:
            if u not in selected_users and u != task.recruitment_manager_id:
                task.user_ids = [(3, u.id)]  # remove from Many2many

        # Close wizard
        return {'type': 'ir.actions.act_window_close'}

class TaskManagerWizard(models.TransientModel):
    _name = "task.manager.wizard"
    _description = "Assign Manager to Task"

    task_id = fields.Many2one('project.task', string="Task", required=True)
    manager_id = fields.Many2one('res.users', string="Manager", required=True)

    def assign_manager(self):
        """Assign a new manager and update user_ids smartly"""
        for wizard in self:
            task = wizard.task_id
            new_manager = wizard.manager_id

            if not task or not new_manager:
                continue

            old_manager = task.recruitment_manager_id

            # Update manager field
            task.recruitment_manager_id = new_manager

            # Remove old manager from Assignees if not in team members
            if old_manager and old_manager not in task.team_member_ids and old_manager in task.user_ids:
                task.user_ids = [(3, old_manager.id)]  # (3, id) removes from Many2many

            # Add new manager to Assignees if not already present
            if new_manager not in task.user_ids:
                task.user_ids = [(4, new_manager.id)]  # (4, id) adds to Many2many

        # Close wizard
        return {'type': 'ir.actions.act_window_close'}