from odoo import models, fields, api


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    @api.model
    def hide_menu_for_group(self):
        excluded_menus = self.env["his.menu.group.exclusion"].sudo().search([])

        for excluded_menu in excluded_menus:
            module = excluded_menu.menu_xml_id.split(".")[0]
            menu_id = excluded_menu.menu_xml_id.split(".")[1]

            menu_data = self.env["ir.model.data"].search(
                [("module", "=", module), ("name", "=", menu_id)], limit=1
            )

            if menu_data:
                menu = self.browse(menu_data.res_id)

                if menu:
                    if excluded_menu.group_id.id not in menu.excluded_group_ids.ids:
                        menu.write(
                            {"excluded_group_ids": [(4, excluded_menu.group_id.id)]}
                        )
        return True

        # group_xml_id = 'lis_external.group_lisex_examiner'
        #
        # menu_xml_ids = [
        #     'base.menu_management',
        #     'contacts.menu_contacts',
        #     'hr.menu_hr_root',
        #     'utm.menu_link_tracker_root',
        #     'maintenance.menu_maintenance_title',
        #     'website.menu_website_configuration',
        #     'spreadsheet_dashboard.spreadsheet_dashboard_menu_root',
        #     'ks_dashboard_ninja.board_menu_root',
        #     'calendar.mail_menu_calendar',
        #     'mail.menu_root_discuss',
        #     'odoo_reportbro.menu_report_report',
        #     'todo_list.todo_list_menu',
        #     'lis.menu_lis_order',
        #     'his.menu_his_general_medical'
        # ]
        #
        # group_id = self.env.ref(group_xml_id)
        #
        # for menu_xml_id in menu_xml_ids:
        #
        #     module = menu_xml_id.split('.')[0]
        #     menu_id = menu_xml_id.split('.')[1]
        #
        #     menu_data = self.env['ir.model.data'].search([
        #         ('module', '=', module),
        #         ('name', '=', menu_id)
        #     ], limit=1)
        #
        #     if menu_data:
        #         menu = self.env['ir.ui.menu'].browse(menu_data.res_id)
        #         if menu:
        #             if group_id.id not in menu.excluded_group_ids.ids:
        #                 menu.write({
        #                     'excluded_group_ids': [(4, group_id.id)]
        #                 })
        # return True
