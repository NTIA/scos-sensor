class Action(object):
    def __call__(self, schedule_entry_id, task_id):
        raise NotImplementedError("Implement action logic.")
