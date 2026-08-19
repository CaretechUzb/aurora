from odoo import _, models, fields, api
from ...utils.cyrillic_latin_translator import to_latin, to_cyrillic


class State(models.Model):
    _inherit = "res.country.state"

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=1000):
        if not args:
            args = []

        if name:
            name_latin = to_latin(name)
            name_cyrillic = to_cyrillic(name)
            args += [
                "|",
                ["name", "ilike", name_latin],
                ["name", "ilike", name_cyrillic],
            ]
        return self._search(args, limit=limit)


class District(models.Model):
    _inherit = "res.state.district"

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=1000):
        if not args:
            args = []

        if name:
            name_latin = to_latin(name)
            name_cyrillic = to_cyrillic(name)
            args += [
                "|",
                ["name", "ilike", name_latin],
                ["name", "ilike", name_cyrillic],
            ]
        self.env.cr.execute("SELECT set_limit(0.1);")
        return self._search(args, limit=limit)


class Neighborhood(models.Model):
    _inherit = "res.district.neighborhood"

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=1000):
        if not args:
            args = []

        if name:
            name_latin = to_latin(name)
            name_cyrillic = to_cyrillic(name)
            args += [
                "|",
                ["name", "ilike", name_latin],
                ["name", "ilike", name_cyrillic],
            ]
        self.env.cr.execute("SELECT set_limit(0.1);")
        return self._search(args, limit=limit)
