class DerivedStringGenerator:
    def __init__(self, depends_on: str, template: str):
        self.depends_on = depends_on
        self.template = template

    def generate(self, row: dict):
        value = row[self.depends_on]
        return self.template.format(value=value)