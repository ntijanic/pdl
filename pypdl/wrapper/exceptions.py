class JobError(Exception):
    def __json__(self):
        return {'$$type': 'error', 'message': self.message or str(self)}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get('message', 'Job error'))


class ProtocolError(JobError):
    pass


class NoWrapperIdError(ProtocolError):
    pass


class NoResourcesError(ProtocolError):
    pass


class NoSuchMethodError(ProtocolError):
    pass


class NotAJobError(ProtocolError):
    pass


class ValidationError(JobError):
    pass


class InputsValidationError(ValidationError):
    pass


class ParamsValidationError(ValidationError):
    pass


__exit_codes = {
    NotAJobError: 33,
    JobError: 34,
    NoWrapperIdError: 36,
    InputsValidationError: 37,
    ParamsValidationError: 38,
    NoSuchMethodError: 40,
    NoResourcesError: 41
}


def exit_code_for_exception(exception):
    return __exit_codes.get(exception.__class__, 39)
