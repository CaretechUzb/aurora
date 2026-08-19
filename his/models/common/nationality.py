from odoo import fields, models, api
from ...utils.cyrillic_latin_translator import to_latin, to_cyrillic


class Nationality(models.Model):
    _name = "his.nationality"
    _description = "Nationality Records"
    _rec_name = "name"

    name = fields.Char(string="Nationality", required=True, translate=True)

    # @api.model
    # def _name_search(self, name="", args=None, operator="ilike", limit=1000):
    #     if not args:
    #         args = []
    #
    #     if name:
    #         name_latin = to_latin(name)
    #         name_cyrillic = to_cyrillic(name)
    #         lang = self.env.context.get('lang', 'en_US')  # Get current language
    #
    #         # Perform raw SQL search on the JSONB field
    #         query = """
    #             SELECT id FROM his_nationality
    #             WHERE (name->>%s) ILIKE %s OR (name->>%s) ILIKE %s
    #             LIMIT %s
    #         """
    #         params = [lang, f"%{name_latin}%", lang, f"%{name_cyrillic}%", limit]
    #         self.env.cr.execute(query, params)
    #         ids = [row[0] for row in self.env.cr.fetchall()]
    #
    #         if not ids:
    #             return []
    #
    #         # Apply additional filters if any
    #         if args:
    #             args.append(('id', 'in', ids))
    #             return self._search(args, limit=limit)
    #
    #         return self.browse(ids).name_get()
    #     else:
    #         return super(Nationality, self)._name_search(name, args, operator, limit)
