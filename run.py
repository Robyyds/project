from app import create_app, db
from app.models import User, Project, DynamicColumn, ProjectNote, ProjectFile, ProjectDynamicValue
app = create_app()
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Project': Project,
        'DynamicColumn': DynamicColumn,
        'ProjectNote': ProjectNote,
        'ProjectFile': ProjectFile,
        'ProjectDynamicValue': ProjectDynamicValue
    }
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)


