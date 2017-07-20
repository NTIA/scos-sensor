class Action(object):
    def __init__(self, schema):
        self.schema = schema

        err = "action expects schema to be initialized with strict=True"
        assert schema.strict, err

    def __call__(self, scheduler_entry_id, task_id):
        raise NotImplementedError("Implement action logic.")

    def set_properties(self, kwargs):
        if not self.schema:
            raise RuntimeError("no schema set")

        loaded_kwargs = self.schema.load(kwargs).data
        kwargs_with_defaults = self.schema.dump(loaded_kwargs).data
        for k, v in kwargs_with_defaults.items():
            assert k != "schema", "schema is a reserved Action property"
            setattr(self, k, v)
