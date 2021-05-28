class ExecError(Exception):
    def __init__(self, exit_code):
        self.exit_code = exit_code
        msg = f"Error while executing shell command. Exit code: {self.exit_code}"
        super().__init__(msg)

class ErrorStatus(Exception):
    def __init__(self, status, description):
        self.status = status
        self.description = description
        super().__init__(f"Status code: {status}; Description: {description}")
    def get_status(self):
        return self.status

class InternalError(ErrorStatus):
    def __init__(self):
        super().__init__(-1, "Internal error")    

class GenerationError(ErrorStatus):
    def __init__(self):
        super().__init__(-2, "Generation error")

class CompilationError(ErrorStatus):
    def __init__(self):
        super().__init__(-3, "Compilation error")
    
class ParserError(ErrorStatus):
    def __init__(self):
        super().__init__(-4, "Parser error")
    