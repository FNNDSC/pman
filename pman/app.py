
import os

from flask import Flask
from flask_restful import Api

from .config import DevConfig, ProdConfig
from pman.resources import JobList, Job


def create_app(config_dict=None):
    app_mode = os.environ.get("APPLICATION_MODE", default="development")
    if app_mode == 'development':
        config_obj = DevConfig()
    else:
        config_obj = ProdConfig()

    app = Flask(__name__)
    app.config.from_object(config_obj)
    app.config.update(config_dict or {})

    api = Api(app, prefix='/api/v1/')

    # url mappings
    api.add_resource(JobList, '/', endpoint='api.joblist')
    api.add_resource(Job, '/<string:job_id>/', endpoint='api.job')

    return app
